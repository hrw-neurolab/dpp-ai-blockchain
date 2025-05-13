import json
import textwrap

from langchain_ollama import ChatOllama
from langchain.prompts import HumanMessagePromptTemplate
from loguru import logger

from src.llm_mapping.llm_mapping import LlmMapping


class IterativeRefiner:
    """
    Wrapper that runs the LLM Mapping repeatedly until no errors are found
    or the maximum number of attempts is reached.

    * Only Ollama models are supported.
    * Adds `refinement_attempts` and `attempt_history` keys.
    """

    def __init__(self, llm_mapping: LlmMapping, max_attempts: int):
        self.llm_mapping = llm_mapping

        if not isinstance(self.llm_mapping.llm, ChatOllama):
            raise ValueError("Iterative refinement is intended for Ollama models only.")

        self.max_attempts = max(1, max_attempts)
        self.__init_correction_msg()

    @property
    def prompt(self):
        """Get the prompt of the LLM mapping."""
        return self.llm_mapping.prompt

    def __init_correction_msg(self):
        """Initialize the correction message template based on the prompt type."""
        if self.llm_mapping.prompt_type == "mapping_function":
            msg = """\
            The previous code was **invalid**.

            This is exactly what you returned:
            {prev_output}

            Please fix *ALL* problems and return **ONLY ONE** Python code block
            that defines a *callable* function **map_raw_to_standard(raw: dict) -> dict**
            and nothing else – no markdown, no comments, no explanation.

            Errors you must correct:
            {error}
            """
        else:
            msg = """\
            The previous output was **invalid**.

            This is exactly what you returned:
            {prev_output}

            Fix **ALL** issues and return **ONLY** the valid JSON object.

            Errors you must correct:
            {error}
            """

        self.correction_msg = textwrap.dedent(msg).strip()

    def __build_correction_msg(self, failed_result: dict) -> str:
        """Build a correction instruction that contains

        * the invalid output from the previous attempt, and
        * the thrown error list / message.

        Args:
            failed_result (dict): The result of the previous attempt.

        Returns:
            str: The correction message.
        """
        prev_output = failed_result.get("response_raw", "")
        error = failed_result.get("error_msg", "")

        # Pydantic validation errors
        if not isinstance(error, str):
            error = json.dumps(error, ensure_ascii=False)

        return self.correction_msg.format(prev_output=prev_output, error=error)

    def __call__(self, template_vars: dict, source: dict):
        attempts = 0
        correction_msg = ""
        history: list[dict] = []

        while True:
            logger.info(f"      >> Attempt {attempts}")

            template_vars["correction_msg"] = correction_msg
            result = self.llm_mapping(template_vars, source)

            result["attempt_no"] = attempts
            result["correction_msg"] = correction_msg

            success = not result["error"]
            llm_call_exception = result["error_type"] == "LLM_CALL_EXCEPTION"
            max_attempts_reached = attempts >= self.max_attempts

            if success or llm_call_exception or max_attempts_reached:
                result["refinement_attempts"] = attempts
                result["attempt_history"] = history
                return result

            if attempts == 0:
                self.llm_mapping.prompt.append(
                    HumanMessagePromptTemplate.from_template("{correction_msg}")
                )

            attempts += 1
            history.append(result)
            correction_msg = self.__build_correction_msg(result)
