from langchain.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)

from langchain_core.runnables import RunnablePassthrough

from llm_mapping.target_model import OUTPUT_PARSER


SYSTEM_PROMPT = """
You are a data transformation assistant that processes raw telemetry data collected daily from industrial production machines. 
Your job is to convert each raw input JSON into a structured, standardized JSON object with the following goals:

- Extract and rename fields according to the target format.
- Ensure units are correct and standardized (e.g., converting g to kg when necessary).
- Ensure the data types are correct (e.g., converting strings to numbers).
- Return only valid JSON — no extra commentary.

{format_instructions}
"""

HUMAN_PROMPT = "{input_json}"

prompt_template = ChatPromptTemplate.from_messages(
    [
        SystemMessagePromptTemplate.from_template(SYSTEM_PROMPT),
        HumanMessagePromptTemplate.from_template(HUMAN_PROMPT),
    ]
)


PROMPT = {"input_json": RunnablePassthrough()} | prompt_template.partial(
    format_instructions=OUTPUT_PARSER.get_format_instructions()
)
