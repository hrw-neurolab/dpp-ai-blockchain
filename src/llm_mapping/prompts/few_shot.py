import json
import os

from langchain.prompts import (
    ChatPromptTemplate,
    FewShotChatMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel

from src.dataset.preparation import generate_few_shot_examples
from src.llm_mapping.prompts.base_prompt import SYSTEM_PROMPT, HUMAN_PROMPT
from src.types import Difficulty


EXAMPLE_PROMPT = ChatPromptTemplate.from_messages(
    [("human", "{input}"), ("ai", "{output}")]
)


def get_few_shot_examples(difficulty: Difficulty, cache_dir: str):
    """Generates or loads few-shot examples for the specified difficulty level.

    Args:
        difficulty (Difficulty): The difficulty level of the examples.
        cache_dir (str): The directory where the few-shot examples are stored.

    Returns:
        list[dict]: A list of few-shot examples.
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

    return examples


def get_enum_fields_prompt(target_model: BaseModel):
    """
    Generate a prompt for the enum fields in the target model.

    Args:
        target_model (BaseModel): The target model class.

    Returns:
        str: The generated prompt.
    """
    prompt = "Valid options for the enum fields in the target model:"
    schema = target_model.model_json_schema()

    enum_defs = {}
    for def_name, def_info in schema["$defs"].items():
        if "enum" not in def_info:
            continue

        enum_defs[def_name] = def_info["enum"]

    for field_name, field_info in schema["properties"].items():
        if "$ref" not in field_info:
            continue

        enum_name = field_info["$ref"].split("/")[-1]
        enum_values = enum_defs[enum_name]

        prompt += f"\n- {field_name}: {json.dumps(enum_values)}"

    return prompt


def get_few_shot_prompt(
    difficulty: Difficulty,
    cache_dir: str,
    parser: PydanticOutputParser,
    include_enums: bool,
):
    """Loads or generates a few-shot prompt template for the specified difficulty level.

    Args:
        difficulty (Difficulty): The difficulty level of the prompt.
        cache_dir (str): The directory where the few-shot examples are stored.
        parser (PydanticOutputParser): The output parser to use.
        include_enums (bool): Whether to include the enum options in the prompt.

    Returns:
        ChatPromptTemplate: The few-shot prompt template.
    """
    examples = get_few_shot_examples(difficulty, cache_dir)
    few_shot_prompt = FewShotChatMessagePromptTemplate(
        examples=examples,
        example_prompt=EXAMPLE_PROMPT,
    )

    system_prompt = SYSTEM_PROMPT

    if difficulty != "simple" and include_enums:
        enum_fields_prompt = get_enum_fields_prompt(parser.pydantic_object)
        system_prompt += f"\n\n{enum_fields_prompt}"

    system_prompt += "\n\nHere are some examples:\n"

    prompt_template = ChatPromptTemplate.from_messages(
        [
            SystemMessagePromptTemplate.from_template(system_prompt),
            few_shot_prompt,
            HUMAN_PROMPT,
        ]
    )

    return prompt_template
