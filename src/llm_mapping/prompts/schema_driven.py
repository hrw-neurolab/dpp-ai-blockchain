from typing import Literal

from langchain.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.output_parsers import PydanticOutputParser


SYSTEM_PROMPT_SIMPLE = """
You are a data transformation assistant that processes raw telemetry data collected daily from industrial production machines. 
Your job is to convert each raw input JSON into a structured, standardized JSON object with the following goals:

- Extract and rename fields according to the target format.
- Ensure units are correct and standardized (e.g., converting g to kg when necessary).
- Ensure the data types are correct (e.g., converting strings to numbers).
- Return only valid JSON — no extra commentary.

{format_instructions}
"""


SYSTEM_PROMPTS = {
    "simple": SYSTEM_PROMPT_SIMPLE,
    "moderate": SYSTEM_PROMPT_SIMPLE,
    "complex": SYSTEM_PROMPT_SIMPLE,
}

HUMAN_PROMPT = "{input_json}"


def get_schema_driven_prompt(
    difficulty: Literal["simple", "moderate", "complex"], parser: PydanticOutputParser
):
    """Loads or generates a schema-driven prompt for the specified difficulty level.

    Args:
        difficulty (Literal["simple", "moderate", "complex"]): The difficulty level of the prompt.
        parser (PydanticOutputParser): The output parser to use.

    Returns:
        ChatPromptTemplate: The prompt template.
    """
    system_prompt = SYSTEM_PROMPTS[difficulty]

    prompt_template = ChatPromptTemplate.from_messages(
        [
            SystemMessagePromptTemplate.from_template(system_prompt),
            HumanMessagePromptTemplate.from_template(HUMAN_PROMPT),
        ]
    )

    return prompt_template.partial(format_instructions=parser.get_format_instructions())
