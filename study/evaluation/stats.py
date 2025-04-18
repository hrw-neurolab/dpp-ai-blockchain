from dataclasses import dataclass


def _zero_div(a: float, b: float) -> float:
    if b == 0:
        return 0.0
    else:
        return a / b


@dataclass
class DirectMappingStats:
    total_runtime: float = 0.0
    num_samples: int = 0
    num_samples_correct: int = 0
    num_llm_call_exceptions: int = 0
    num_invalid_json: int = 0
    num_missing_keys: int = 0
    num_type_mismatches: int = 0
    num_value_mismatches: int = 0
    total_time_correct: float = 0.0
    total_llm_time_correct: float = 0.0
    total_blockchain_time: float = 0.0
    total_tokens: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    pct: dict = None
    avg: dict = None

    def __pct_samples(self, key: str):
        return _zero_div(getattr(self, key), self.num_samples)

    def __pct_tokens(self, key: str):
        return _zero_div(getattr(self, key), self.total_tokens)

    def __avg_samples_correct(self, key: str):
        return _zero_div(getattr(self, key), self.num_samples_correct)

    def calculate_pct(self):
        self.pct = {
            "samples_correct": self.__pct_samples("num_samples_correct"),
            "llm_call_exceptions": self.__pct_samples("num_llm_call_exceptions"),
            "parsing_exceptions": self.__pct_samples("num_invalid_json"),
            "missing_keys": self.__pct_samples("num_missing_keys"),
            "type_mismatches": self.__pct_samples("num_type_mismatches"),
            "value_mismatches": self.__pct_samples("num_value_mismatches"),
            "input_tokens": self.__pct_tokens("total_input_tokens"),
            "output_tokens": self.__pct_tokens("total_output_tokens"),
        }

    def calculate_avg(self):
        self.avg = {
            "time_correct": self.__avg_samples_correct("total_time_correct"),
            "llm_time_correct": self.__avg_samples_correct("total_llm_time_correct"),
            "blockchain_time": self.__avg_samples_correct("total_blockchain_time"),
            "tokens": self.__avg_samples_correct("total_tokens"),
            "input_tokens": self.__avg_samples_correct("total_input_tokens"),
            "output_tokens": self.__avg_samples_correct("total_output_tokens"),
        }


@dataclass
class MappingFunctionStats:
    total_runtime: float = 0.0
    total_tokens: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    num_samples: int = 0
    num_samples_correct: int = 0
    num_llm_call_exceptions: int = 0
    num_no_code_block: int = 0
    num_function_not_found: int = 0
    num_function_not_callable: int = 0
    num_function_execution_exception: int = 0
    num_function_return_type: int = 0
    pct: dict = None
    avg: dict = None

    def __pct_samples(self, key: str):
        return _zero_div(getattr(self, key), self.num_samples)

    def __pct_tokens(self, key: str):
        return _zero_div(getattr(self, key), self.total_tokens)

    def __avg_samples_correct(self, key: str):
        return _zero_div(getattr(self, key), self.num_samples_correct)

    def calculate_pct(self):
        self.pct = {
            "samples_correct": self.__pct_samples("num_samples_correct"),
            "llm_call_exceptions": self.__pct_samples("num_llm_call_exceptions"),
            "no_code_block": self.__pct_samples("num_no_code_block"),
            "function_not_found": self.__pct_samples("num_function_not_found"),
            "function_not_callable": self.__pct_samples("num_function_not_callable"),
            "function_execution_exception": self.__pct_samples(
                "num_function_execution_exception"
            ),
            "function_return_type": self.__pct_samples("num_function_return_type"),
            "input_tokens": self.__pct_tokens("total_input_tokens"),
            "output_tokens": self.__pct_tokens("total_output_tokens"),
        }

    def calculate_avg(self):
        self.avg = {
            "time_correct": self.__avg_samples_correct("total_runtime"),
            "tokens": self.__avg_samples_correct("total_tokens"),
            "input_tokens": self.__avg_samples_correct("total_input_tokens"),
            "output_tokens": self.__avg_samples_correct("total_output_tokens"),
        }
