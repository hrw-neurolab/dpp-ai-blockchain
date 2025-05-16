from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate
from langchain.output_parsers import PydanticOutputParser

from src.llm_mapping.prompts.base_prompt import HUMAN_PROMPT


SYSTEM_PROMPT = """\
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

Provide only the function definition inside a markdown python code block and without any additional comments or explanations.\
"""


def get_mapping_function_prompt(parser: PydanticOutputParser):
    """Loads or generates a mapping function prompt for the specified difficulty level.

    Args:
        parser (PydanticOutputParser): The output parser to use.

    Returns:
        ChatPromptTemplate: The prompt template.
    """
    prompt_template = ChatPromptTemplate.from_messages(
        [
            SystemMessagePromptTemplate.from_template(SYSTEM_PROMPT),
            HUMAN_PROMPT,
        ]
    )

    format_instructions = parser.get_format_instructions()
    format_instructions = format_instructions.replace(
        "The output should be formatted as a JSON instance that conforms to the JSON schema below.",
        "The function output dict should conform to the JSON schema below.",
    ).strip()

    return prompt_template.partial(format_instructions=format_instructions)
