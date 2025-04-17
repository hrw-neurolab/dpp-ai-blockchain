from langchain.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain_core.runnables import RunnablePassthrough

from llm_mapping.target_model import OUTPUT_PARSER


SYSTEM_PROMPT = """
You are a data transformation assistant that processes raw telemetry data collected daily from industrial production machines. 
Your job is to generate a python function that maps a raw input JSON into a structured, standardized JSON object.

The function should:
- be named `map_raw_to_standard`.
- take a single argument, `input_json`, which is a dictionary.
- return a dictionary that represents the transformed data.
- extract and rename fields according to the target format.
- ensure units are correct and standardized (e.g., converting g to kg when necessary).
- ensure the data types are correct (e.g., converting strings to numbers).

{format_instructions}

Provide only the function definition inside a markdown python code block and without any additional comments or explanations.
"""

HUMAN_PROMPT = "{input_json}"

prompt_template = ChatPromptTemplate.from_messages(
    [
        SystemMessagePromptTemplate.from_template(SYSTEM_PROMPT),
        HumanMessagePromptTemplate.from_template(HUMAN_PROMPT),
    ]
)

format_instructions = OUTPUT_PARSER.get_format_instructions()
format_instructions = format_instructions.replace(
    "The output should be formatted as a JSON instance that conforms to the JSON schema below.",
    "",
).strip()


PROMPT = {"input_json": RunnablePassthrough()} | prompt_template.partial(
    format_instructions=format_instructions
)
