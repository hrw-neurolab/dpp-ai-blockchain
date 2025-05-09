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
    "moderate": SYSTEM_PROMPT_SIMPLE,
    "complex": SYSTEM_PROMPT_SIMPLE,
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
