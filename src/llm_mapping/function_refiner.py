# src/llm_mapping/function_refiner.py
from __future__ import annotations

import copy
import json
import textwrap
import time
import re
from types import FunctionType
from typing import Any, Dict, List

from langchain_core.utils.json import parse_json_markdown
from loguru import logger
from pydantic import ValidationError

from src.llm_mapping.llm_mapping import LlmMapping


class FunctionRefiner:
    """
    Wrapper that runs a mapping‑function prompt repeatedly until it
    produces runnable code **and** the result passes the target‑schema
    validation.

    * Ollama‑only, just like `IterativeRefiner`.
    * Adds `refinement_attempts` and `attempt_history` keys.
    """

    def __init__(self, base_mapper: "LlmMapping", max_attempts: int = 3):
        from langchain_ollama import ChatOllama
        import langchain
        langchain.debug = True


        if base_mapper.prompt_type != "mapping_function":
            raise ValueError(
                "FunctionRefiner only makes sense for prompt_type='mapping_function'"
            )
        if not isinstance(base_mapper.llm, ChatOllama):
            raise ValueError("FunctionRefiner is intended for Ollama models only.")

        self.base_mapper = base_mapper
        self.max_attempts = max(1, max_attempts)

        # expose same attributes as the wrapped mapper
        self.prompt = base_mapper.prompt
        self.parser = base_mapper.parser
    
    def __call__(self, source: Dict[str, Any]):
        attempts = 0
        correction_msg = ""
        src_copy = copy.deepcopy(source)
        history: List[Dict[str, Any]] = []

        while True:
            payload = {
                "input_json": src_copy,
                "correction_msg": correction_msg,
            }
            single = self._single_run(payload, attempts)
            history.append(copy.deepcopy(single))

            # success ───────────────────────────────────────────────────
            if not single["error"]:
                single["refinement_attempts"] = attempts
                single["attempt_history"] = history
                return single

            fatal = single["error_type"] not in {
                "FUNCTION_SYNTAX_ERROR",
                "FUNCTION_NOT_FOUND",
                "FUNCTION_NOT_CALLABLE",
                "FUNCTION_EXECUTION_EXCEPTION",
                "PYDANTIC_VALIDATION_ERROR",
                "NO_CODE_BLOCK",
                "PARSING_EXCEPTION",
            }
            if fatal or attempts >= self.max_attempts:
                single["refinement_attempts"] = attempts
                single["attempt_history"] = history
                return single

            attempts += 1
            correction_msg = self._build_correction_msg(single)
    def strip_thinking_tags(self, response_raw: str) -> str:
   
        return re.sub(r"<think>.*?</think>\s*", "", response_raw, flags=re.DOTALL).strip()   
    
    def _single_run(self, payload: Dict[str, Any], attempt_no: int):
        bm = self.base_mapper
        res: Dict[str, Any] = {
            "attempt": attempt_no,
            "payload": payload,
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

        t0 = time.time()
        try:
            response = bm.chain.invoke(payload)

            token_usage = response.usage_metadata
            res["input_tokens"] = token_usage["input_tokens"]
            res["output_tokens"] = token_usage["output_tokens"]
            res["total_tokens"] = token_usage["total_tokens"]
            print(response)
        except Exception as e:  
            res.update(error=True, error_msg=str(e), error_type="LLM_CALL_EXCEPTION")
            return res

        res["llm_time"] = time.time() - t0
        res["response_raw"] = response.text().strip()
        raw = self.strip_thinking_tags(raw)

        if "```python" not in res["response_raw"] or "```" not in res["response_raw"]:
            res.update(
                error=True,
                error_msg="No Python code block found.",
                error_type="NO_CODE_BLOCK",
            )
            return res

        code = res["response_raw"].split("```python")[1].split("```")[0].strip()
        res["response_parsed"] = code
        local: Dict[str, Any] = {}
        try:
            exec(code, {}, local)
        except SyntaxError as syn:
            res.update(
                error=True, error_msg=str(syn), error_type="FUNCTION_SYNTAX_ERROR"
            )
            return res

        fn: FunctionType | None = local.get("map_raw_to_standard")
        if fn is None or not callable(fn):
            res.update(
                error=True,
                error_msg="map_raw_to_standard() not found or not callable.",
                error_type="FUNCTION_NOT_FOUND",
            )
            return res

        try:
            output = fn(payload["input_json"])
            res["function_result"] = output
        except Exception as ex:
            res.update(
                error=True, error_msg=str(ex), error_type="FUNCTION_EXECUTION_EXCEPTION"
            )
            return res

        if not isinstance(output, dict):
            res.update(
                error=True,
                error_msg="Function must return a dict.",
                error_type="FUNCTION_RETURN_TYPE",
            )
            return res

        try:
            self.parser.pydantic_object.model_validate(output)
            return res
        except ValidationError as ve:
            res.update(
                error=True,
                error_msg=ve.errors(include_url=False, include_context=False),
                error_type="PYDANTIC_VALIDATION_ERROR",
            )
            return res

    def _build_correction_msg(self, failed_run: Dict[str, Any]) -> str:
        """
        Build a correction instruction that contains

        * the invalid code (truncated),
        * the thrown error list / message.
        """

        code = str(failed_run.get("response_parsed", ""))

        err = failed_run.get("error_msg", "")
        if not isinstance(err, str):
            err = json.dumps(err, ensure_ascii=False)

        return textwrap.dedent(
            f"""
            The previous code was **invalid**.

            ```python
            {code}
            ```

            Please fix *all* problems and return **only one** Python code block
            that defines a *callable* function **map_raw_to_standard(raw: dict) -> dict**
            and nothing else – no markdown, no comments, no explanation.

            Errors you must correct:
            {err}
            """
        )
