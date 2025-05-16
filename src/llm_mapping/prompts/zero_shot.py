from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate
from langchain.output_parsers import PydanticOutputParser

from src.llm_mapping.prompts.base_prompt import SYSTEM_PROMPT, HUMAN_PROMPT


def get_zero_shot_prompt(parser: PydanticOutputParser, include_schema: bool):
    """Generates a zero-shot prompt template with/without target schema.

    Args:
        parser (PydanticOutputParser): The output parser to use.
        include_schema (bool): Whether to include the schema in the prompt.

    Returns:
        ChatPromptTemplate: The prompt template.
    """
    system_prompt = SYSTEM_PROMPT

    if include_schema:
        system_prompt += "\n\n{format_instructions}"

    prompt_template = ChatPromptTemplate.from_messages(
        [
            SystemMessagePromptTemplate.from_template(system_prompt),
            HUMAN_PROMPT,
        ]
    )

    format_instructions = parser.get_format_instructions()
    return prompt_template.partial(format_instructions=format_instructions)
