import json
from langchain.prompts import (
    ChatPromptTemplate,
    FewShotChatMessagePromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain_core.runnables import RunnablePassthrough


EXAMPLES = [
    {
        "input": json.dumps(
            {
                "Date": "20/01/01",
                "OperationalHours": 8,
                "EnergyConsumedKWh": 300,
                "MaterialUsedKg": 481,
                "MaterialWasteKg": 47,
                "CO2EmissionsKg": 193,
                "WaterConsumedLiters": 961,
                "WaterRecoveredLiters": 183,
                "OutputUnits": 430,
            }
        ),
        "output": json.dumps(
            {
                "date": "2020-01-01",
                "operation_hours": 8,
                "energy_consumption_kWh": 300,
                "material_used_kg": 481,
                "material_waste_kg": 47,
                "CO2_emissions_kg": 193,
                "water_consumption_liters": 961,
                "water_recycled_liters": 183,
                "product_output_units": 430,
            }
        ),
    },
    {
        "input": json.dumps(
            {
                "date_iso": "2020-11-14T00:00:00",
                "operation_seconds": 25200,
                "energy_consumption_Wh": 294000,
                "material_used_g": 467000,
                "material_waste_g": 43000,
                "CO2_emissions_t": 0.188,
                "water_consumption_ml": 942000,
                "water_recycled_ml": 173000,
                "product_output_units_thousands": 0.42,
            }
        ),
        "output": json.dumps(
            {
                "date": "2020-11-14",
                "operation_hours": 7,
                "energy_consumption_kWh": 294,
                "material_used_kg": 467,
                "material_waste_kg": 43,
                "CO2_emissions_kg": 188,
                "water_consumption_liters": 942,
                "water_recycled_liters": 173,
                "product_output_units": 420,
            }
        ),
    },
    {
        "input": json.dumps(
            {
                "date": "2020-03-14",
                "operation": "8 h",
                "energy_consumption": "327 kWh",
                "material_used": "512 kg",
                "material_waste": "56 kg",
                "CO2_emissions": "207 kg",
                "water_consumption": "1046 l",
                "water_recycled": "213 l",
                "product_output": "460 units",
            }
        ),
        "output": json.dumps(
            {
                "date": "2020-03-14",
                "operation_hours": 8,
                "energy_consumption_kWh": 327,
                "material_used_kg": 512,
                "material_waste_kg": 56,
                "CO2_emissions_kg": 207,
                "water_consumption_liters": 1046,
                "water_recycled_liters": 213,
                "product_output_units": 460,
            }
        ),
    },
    {
        "input": json.dumps(
            {
                "date": {"value": "2020-04-07", "unit": "ISO"},
                "operation": {"value": 25200, "unit": "s"},
                "energy_consumption": {"value": 273000, "unit": "Wh"},
                "material_used": {"value": 447000, "unit": "g"},
                "material_waste": {"value": 39000, "unit": "g"},
                "CO2_emissions": {"value": 0.177, "unit": "t"},
                "water_consumption": {"value": 879000, "unit": "ml"},
                "water_recycled": {"value": 150000, "unit": "ml"},
                "product_output": {"value": 0.4, "unit": "thousand units"},
            }
        ),
        "output": json.dumps(
            {
                "date": "2020-04-07",
                "operation_hours": 7,
                "energy_consumption_kWh": 273,
                "material_used_kg": 447,
                "material_waste_kg": 39,
                "CO2_emissions_kg": 177,
                "water_consumption_liters": 879,
                "water_recycled_liters": 150,
                "product_output_units": 400,
            }
        ),
    },
]

EXAMPLE_PROMPT = ChatPromptTemplate.from_messages(
    [("human", "{input}"), ("ai", "{output}")]
)

few_shot_prompt = FewShotChatMessagePromptTemplate(
    examples=EXAMPLES,
    example_prompt=EXAMPLE_PROMPT,
)

SYSTEM_PROMPT = """
You are a data transformation assistant that processes raw telemetry data collected daily from industrial production machines. 
Your job is to convert each raw input JSON into a structured, standardized JSON object with the following goals:

- Extract and rename fields according to the target format.
- Ensure units are correct and standardized (e.g., converting g to kg when necessary).
- Ensure the data types are correct (e.g., converting strings to numbers).
- Return only valid JSON — no extra commentary.

Here are some examples:
"""

HUMAN_PROMPT = "{input_json}"

prompt_template = ChatPromptTemplate.from_messages(
    [
        SystemMessagePromptTemplate.from_template(SYSTEM_PROMPT),
        few_shot_prompt,
        HumanMessagePromptTemplate.from_template(HUMAN_PROMPT),
    ]
)

PROMPT = {"input_json": RunnablePassthrough()} | prompt_template
