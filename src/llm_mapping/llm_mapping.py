import time
from typing import Literal

from langchain.output_parsers import PydanticOutputParser
from langchain_core.utils.json import parse_json_markdown
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from loguru import logger
from pydantic import ValidationError

from src.llm_mapping.target_model import OUTPUT_PARSERS
from src.llm_mapping.prompts import (
    get_few_shot_prompt,
    get_schema_driven_prompt,
    get_mapping_function_prompt,
)


class LlmMapping:
    def __init__(
        self,
        provider: Literal["openai", "ollama"],
        model_name: str,
        prompt_type: Literal["few_shot", "schema_driven", "mapping_function"],
        difficulty: Literal["simple", "moderate", "complex"],
        cache_dir: str,
    ):
        """Initialize the LLM mapping class.

        Args:
            provider ("openai" | "ollama"): The provider for the language model.
            model_name (str): The model to use for evaluation.
            prompt_type ("few_shot" | "schema_driven" | "mapping_function"): The type of prompt to use.
            difficulty ("simple" | "moderate" | "complex"): The difficulty level of the dataset.
            cache_dir (str): The cache directory for storing the few-shot examples.
        """
        logger.info(f"Initializing LLM: {provider} - {model_name}")
        self.__init_llm(provider, model_name)

        self.prompt_type = prompt_type
        self.difficulty = difficulty
        self.cache_dir = cache_dir

        self.parser: PydanticOutputParser = OUTPUT_PARSERS[difficulty]

        logger.info(f"Initializing prompt template: {prompt_type}")
        self.__init_prompt()

        self.chain = self.prompt | self.llm

    def __init_llm(self, provider: str, model_name: str):
        """Initialize the LLM based on the provider and model name.

        Args:
            provider (str): The provider for the language model.
            model_name (str): The model to use for evaluation.
        """
        if provider == "openai":
            self.llm = ChatOpenAI(
                model=model_name,
                temperature=0,
                timeout=None,
                max_retries=2,
            )
        elif provider == "ollama":
            self.llm = ChatOllama(
                model=model_name,
                temperature=0,
            )
        else:
            raise ValueError(
                f"Invalid model type: {model_name}. Supported models are 'gpt' and 'ollama'."
            )

    def __init_prompt(self):
        """Initialize the prompt based on the provided type."""
        if self.prompt_type == "few_shot":
            self.prompt = get_few_shot_prompt(self.difficulty, self.cache_dir)

        elif self.prompt_type == "schema_driven":
            self.prompt = get_schema_driven_prompt(self.difficulty, self.parser)

        elif self.prompt_type == "mapping_function":
            self.prompt = get_mapping_function_prompt(self.difficulty, self.parser)

        else:
            raise ValueError(
                f"Invalid prompt type: {self.prompt_type}. "
                "Supported types are 'few_shot', 'schema_driven', and 'mapping_function'."
            )

    def __process_direct_mapping(self, source: dict):
        """Map a sample directly using the LLM and the provided prompt.

        Args:
            source (dict): The source data to evaluate.

        Returns:
            A dictionary containing the evaluation results.
        """
        result = {
            "llm_time": None,
            "response_raw": None,
            "response_parsed": None,
            "error": False,
            "error_msg": None,
            "error_type": None,
            "input_tokens": None,
            "output_tokens": None,
            "total_tokens": None,
        }

        start_time = time.time()

        try:
            response = self.chain.invoke(source)

            token_usage = response.usage_metadata
            result["input_tokens"] = token_usage["input_tokens"]
            result["output_tokens"] = token_usage["output_tokens"]
            result["total_tokens"] = token_usage["total_tokens"]

        except Exception as e:
            result["error"] = True
            result["error_msg"] = str(e)
            result["error_type"] = "LLM_CALL_EXCEPTION"
            return result

        result["llm_time"] = time.time() - start_time
        response_raw = response.text()
        result["response_raw"] = response_raw

        try:
            parsed = parse_json_markdown(response_raw)
            parsed = self.parser.pydantic_object.model_validate(parsed, strict=True)
            result["response_parsed"] = parsed.model_dump()

        except ValidationError as e:
            result["error"] = True
            result["error_msg"] = e.errors(include_url=False, include_context=False)
            result["error_type"] = "PYDANTIC_VALIDATION_ERROR"

        except Exception as e:
            result["error"] = True
            result["error_msg"] = str(e)
            result["error_type"] = "PARSING_EXCEPTION"

        return result

    def __process_mapping_function(self, source: dict):
        """Generate and execute a mapping function to transform the source data into the target format.

        Args:
            source (dict): The source data to evaluate.

        Returns:
            A dictionary containing the results.
        """
        result = {
            "llm_time": None,
            "response_raw": None,
            "response_parsed": None,
            "function_result": None,
            "error": False,
            "error_msg": None,
            "error_type": None,
            "input_tokens": None,
            "output_tokens": None,
            "total_tokens": None,
        }

        start_time = time.time()

        try:
            response = self.chain.invoke(source)

            token_usage = response.usage_metadata
            result["input_tokens"] = token_usage["input_tokens"]
            result["output_tokens"] = token_usage["output_tokens"]
            result["total_tokens"] = token_usage["total_tokens"]

        except Exception as e:
            result["error"] = True
            result["error_msg"] = str(e)
            result["error_type"] = "LLM_CALL_EXCEPTION"
            return result

        result["llm_time"] = time.time() - start_time

        response_raw = response.text().strip()
        result["response_raw"] = response_raw

        # Extract the code string from the response
        if "```python" not in response_raw or not response_raw.endswith("```"):
            result["error"] = True
            result["error_msg"] = "No code block found in the response."
            result["error_type"] = "NO_CODE_BLOCK"
            return result

        code_str = response_raw.split("```python")[1].split("```")[0].strip()

        # Execute the code string to get the transform function
        local_vars = {}
        try:
            exec(code_str, {}, local_vars)
        except SyntaxError as e:
            result["error"] = True
            result["error_msg"] = str(e)
            result["error_type"] = "FUNCTION_SYNTAX_ERROR"
            return result

        map_raw_to_standard = local_vars.get("map_raw_to_standard", None)

        if map_raw_to_standard is None:
            result["error"] = True
            result["error_msg"] = (
                "map_raw_to_standard function not found in the response."
            )
            result["error_type"] = "FUNCTION_NOT_FOUND"
            return result

        if not callable(map_raw_to_standard):
            result["error"] = True
            result["error_msg"] = (
                "map_raw_to_standard function not found in the response."
            )
            result["error_type"] = "FUNCTION_NOT_CALLABLE"
            return result

        result["response_parsed"] = code_str

        # Call the function with the source data
        try:
            output = map_raw_to_standard(source)
        except Exception as e:
            result["error"] = True
            result["error_msg"] = str(e)
            result["error_type"] = "FUNCTION_EXECUTION_EXCEPTION"
            return result

        result["function_result"] = output

        if not type(output) == dict:
            result["error"] = True
            result["error_msg"] = "Function did not return a dictionary."
            result["error_type"] = "FUNCTION_RETURN_TYPE"
            return result

        # Validate the output using the Pydantic parser
        try:
            self.parser.pydantic_object.model_validate(output, strict=True)
        except ValidationError as e:
            result["error"] = True
            result["error_msg"] = e.errors(include_url=False, include_context=False)
            result["error_type"] = "PYDANTIC_VALIDATION_ERROR"

        return result

    def __call__(self, source: dict):
        """Process a sample using the selected prompt type.

        Args:
            source (dict): The source data to process.

        Returns:
            A dictionary containing the results.
        """
        if self.prompt_type == "mapping_function":
            return self.__process_mapping_function(source)

        return self.__process_direct_mapping(source)
