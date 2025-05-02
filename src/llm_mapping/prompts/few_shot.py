import json
import os
from typing import Literal

from langchain.prompts import (
    ChatPromptTemplate,
    FewShotChatMessagePromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain_core.runnables import RunnablePassthrough

from src.dataset.preparation import generate_few_shot_examples


EXAMPLE_PROMPT = ChatPromptTemplate.from_messages(
    [("human", "{input}"), ("ai", "{output}")]
)

SYSTEM_PROMPT_SIMPLE = """
You are a data transformation assistant that processes raw telemetry data collected daily from industrial production machines. 
Your job is to convert each raw input JSON into a structured, standardized JSON object with the following goals:

- Extract and rename fields according to the target format.
- Ensure units are correct and standardized (e.g., converting g to kg when necessary).
- Ensure the data types are correct (e.g., converting strings to numbers).
- Return only valid JSON — no extra commentary.

### STRICT OUTPUT FORMAT
Return **ONLY** a single JSON object – NO markdown, NO code fences,
NO comments. Use double quotes for every key and string. Keys must 
match the target schema exactly. Any deviation will be rejected.

Here are some examples:
"""

SYSTEM_PROMPT_FLEX = """
You are an **industrial-telemetry data transformer**.  
Your ONLY allowed reply is a single JSON object that matches the schema below.

<schema>
{{
  "date": "YYYY-MM-DD"
  "operation_hours": "float"             
  "energy_consumption_kWh": "float"       
  "material_used_kg": "float"           
  "material_waste_kg": "float"           
  "CO2_emissions_kg": "float"             
  "water_consumption_liters": "float"    
  "water_recycled_liters": "float"        
  "product_output_units": "int"          
  "operating_temperature_C": "float"     
  "ambient_humidity_percent": "float"     
  "vibration_level_mmps": "float"        
  "renewable_energy_percent": "float"     
  "downtime_minutes": "int"              
  "noise_level_dB": "int",
  "worker_count": "int",
  "lubrication_level": "low | medium | high",
  "cooling_system_status": "operational | faulty | off",
  "maintenance_required": "boolean"
  "fuel_type": "electric | fossil_fuel | renewable_fuel | hybrid"
}}
</schema>

Transformation rules
--------------------
1. Detect units dynamically
   • Examine field names (suffixes like `_g`, `_kg`, `_mg`, `_t`), inline units (`"350 K"`, `"0.42 MWh"`), or surrounding text.  
   • Convert every numeric value so it matches the target unit in the schema (e.g. g -> kg, mg -> kg, t -> kg, Wh -> kWh, K -> °C, mm/min -> mm/s, s -> minutes, fraction -> percent).  
   • If the unit is ambiguous or missing, make a best guess based on context; otherwise emit `null`.  

2. Rename & normalise keys  
   Output keys **must exactly equal** those in the schema – no extras, no casing changes.

3. Categorical mapping  
   Map synonyms to the allowed values, e.g.  
   • normal -> medium; increased / high -> high; low / decreased -> low  
   • problem / faulty / broken -> faulty  
   • battery_based -> electric; petroleum_based / fossil -> fossil_fuel

4. Type-coercion  
   Convert numeric strings to numbers; booleans must be lowercase JSON literals `true` or `false` (never `True` / `False`)!!

5. Missing data  
   If a required field cannot be derived, output `null`.

Output protocol
---------------
- Extract and rename fields according to the target format.  
- Ensure units are correct and standardised (e.g., converting g to kg when necessary).  
- Ensure the data types are correct (e.g., converting strings to numbers).  
- Return **only** valid JSON — no extra commentary.

Examples
--------
The following in-context pairs show how wildly different raw inputs are converted into the unified JSON.  
Replicate their structure exactly.

"""

SYSTEM_PROMPT = """
You are a data transformation assistant that processes raw telemetry data collected daily from industrial production machines. 
Your job is to convert each raw input JSON into a structured, standardized JSON object with the following goals:

- Extract and rename fields according to the target format.
- Ensure units are correct and standardized (e.g., converting g to kg when necessary).
- Ensure the data types are correct (e.g., converting strings to numbers).
- Return only valid JSON — no extra commentary.

Valid values for the categorical fields are:
- lubrication_level: "low", "medium", "high"
- cooling_system_status: "operational", "faulty", "off"
- fuel_type: "electric", "fossil_fuel", "renewable_fuel", "hybrid"

### STRICT OUTPUT FORMAT
Return **ONLY** a single JSON object – NO markdown, NO code fences,
NO comments. Use double quotes for every key and string. Keys must 
match the target schema exactly. Any deviation will be rejected.

Here are some examples:
"""

SYSTEM_PROMPTS = {
    "simple": SYSTEM_PROMPT_SIMPLE,
    "moderate": SYSTEM_PROMPT_FLEX,
    "complex": SYSTEM_PROMPT_FLEX,
}

HUMAN_PROMPT = "{input_json}\n\n{correction_msg}" 


def get_few_shot_prompt(
    difficulty: Literal["simple", "moderate", "complex"], cache_dir: str
):
    """Loads or generates a few-shot prompt for the specified difficulty level.

    Args:
        difficulty (str): The difficulty level of the prompt. Can be "simple", "moderate" or "complex".
        cache_dir (str): The directory where the few-shot examples are stored.

    Returns:
        ChatPromptTemplate: The few-shot prompt template.
    """
    file_path = os.path.join(cache_dir, difficulty, f"few_shot_examples.json")

    if not os.path.exists(file_path):
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        examples = generate_few_shot_examples(difficulty)
        with open(file_path, "w") as f:
            json.dump(examples, f, indent=4)

    else:
        with open(file_path, "r") as f:
            examples = json.load(f)

    examples = [
        {
            "input": json.dumps(example["input"]),
            "output": json.dumps(example["output"]),
        }
        for example in examples
    ]

    few_shot_prompt = FewShotChatMessagePromptTemplate(
        examples=examples,
        example_prompt=EXAMPLE_PROMPT,
    )

    prompt_template = ChatPromptTemplate.from_messages(
        [
            SystemMessagePromptTemplate.from_template(SYSTEM_PROMPTS[difficulty]),
            few_shot_prompt,
            HumanMessagePromptTemplate.from_template(HUMAN_PROMPT),
        ]
    )

    prompt = {"input_json": RunnablePassthrough(), "correction_msg": RunnablePassthrough(),} | prompt_template

    return prompt
