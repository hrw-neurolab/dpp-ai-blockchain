from __future__ import annotations

import copy
import json
import time
from typing import Any, Dict, List
import re

from langchain_core.utils.json import parse_json_markdown
from loguru import logger
from pydantic import ValidationError

from src.llm_mapping.llm_mapping import LlmMapping


class IterativeRefiner:
    """Wrapper that adds a correction loop and history tracking (Ollama only)."""

    def __init__(self, base_mapper: "LlmMapping", max_attempts: int = 3):
        from langchain_ollama import ChatOllama

        if not isinstance(base_mapper.llm, ChatOllama):
            raise ValueError("IterativeRefiner is intended for Ollama-based models only.")
        if base_mapper.prompt_type == "mapping_function":
            raise ValueError("A refinement loop is not required for 'mapping_function' prompts.")

        self.base_mapper = base_mapper
        self.max_attempts = max(1, max_attempts)

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
            
            if (not single["error"]) or attempts >= self.max_attempts:
                final_result = copy.deepcopy(single)
                final_result["refinement_attempts"] = attempts
                final_result["attempt_history"] = history
                return final_result

         
            attempts += 1
            correction_msg = (
                 "The previous output was **invalid**.\n\n"
                 "This is exactly what you returned:\n"
                 "```json\n"
                 + str(single.get("response_raw", "")) 
                 + "\n```\n"
                 "Fix **ALL** issues and return **ONLY** one valid JSON object \n\n "
                 "Error list:\n"
                 + json.dumps(single["error_msg"], ensure_ascii=False)
                 )
    
    def strip_thinking_tags(self, response_raw: str) -> str:
   
        return re.sub(r"<think>.*?</think>\s*", "", response_raw, flags=re.DOTALL).strip()         
        
    def _single_run(self, payload: Dict[str, Any], attempt_no: int):
        bm = self.base_mapper
        result = {
            "attempt": attempt_no,
            "payload": payload,
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

        start = time.time()
        try:
            resp = bm.chain.invoke(payload)
            usage = resp.usage_metadata or {}
            result.update({
                "input_tokens": usage.get("input_tokens"),
                "output_tokens": usage.get("output_tokens"),
                "total_tokens": usage.get("total_tokens"),
            })
        except Exception as e:
            result.update({
                "error": True,
                "error_msg": str(e),
                "error_type": "LLM_CALL_EXCEPTION",
            })
            return result

        result["llm_time"] = time.time() - start
        raw = resp.text()
        raw = self.strip_thinking_tags(raw)
        result["response_raw"] = raw

        try:
            parsed = parse_json_markdown(raw)
            parsed = bm.parser.pydantic_object.model_validate(parsed)
            result["response_parsed"] = parsed.model_dump()
        except ValidationError as e:
            result.update({
                "error": True,
                "error_msg": e.errors(include_url=False, include_context=False),
                "error_type": "PYDANTIC_VALIDATION_ERROR",
            })
        except Exception as e:
            result.update({
                "error": True,
                "error_msg": str(e),
                "error_type": "PARSING_EXCEPTION",
            })
        return result
