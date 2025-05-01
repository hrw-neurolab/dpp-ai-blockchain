from dataclasses import dataclass, field

import matplotlib.pyplot as plt


def _zero_div(a: float, b: float) -> float:
    return a / b if b > 0 else 0.0


def _generate_plot(labels, values, title):
    fig, ax = plt.subplots(figsize=(8, 6))
    total = sum(values)
    pcts = [_zero_div(v, total) * 100 for v in values]

    bars = ax.bar(labels, values)

    # Annotate each bar with value and percentage
    for bar, value, pct in zip(bars, values, pcts):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            f"{value}\n{pct:.1f}%",
            ha="center",
            va="bottom",
            fontsize=10,
        )

    max_height = max(values)
    ax.set_ylim(0, max_height * 1.15)

    ax.set_title(title)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    return fig


@dataclass
class Stats:
    total: int = 0
    pct: dict = None
    avg: dict = None

    @property
    def absolute(self):
        return [
            (f, getattr(self, f))
            for f in self.__dataclass_fields__
            if f != "pct" and f != "avg"
        ]

    @property
    def plot_items(self):
        labels = []
        values = []

        for field, value in self.absolute:
            if field == "total":
                continue
            labels.append(field)
            values.append(value)

        return labels, values

    def plot(self, title: str = None):
        if title is None:
            title = self.__class__.__name__

        labels, values = self.plot_items
        return _generate_plot(labels, values, title)

    def __iadd__(self, other):
        if not isinstance(other, Stats):
            return NotImplemented

        for field, value in self.absolute:
            setattr(self, field, value + getattr(other, field))

        return self


@dataclass
class SampleStats(Stats):
    llm_call_exception: int = 0
    invalid_json: int = 0
    pydantic_exception: int = 0
    false_positive: int = 0
    correct: int = 0

    def calculate_pct(self):
        self.pct = {
            "llm_call_exception": _zero_div(self.llm_call_exception, self.total),
            "invalid_json": _zero_div(self.invalid_json, self.total),
            "pydantic_exception": _zero_div(self.pydantic_exception, self.total),
            "false_positive": _zero_div(self.false_positive, self.total),
            "correct": _zero_div(self.correct, self.total),
        }


@dataclass
class TimeStats(Stats):
    llm: float = 0.0
    blockchain: float = 0.0
    correct: float = 0.0

    def calculate_pct(self):
        self.pct = {
            "llm": _zero_div(self.llm, self.total),
            "blockchain_time": _zero_div(self.blockchain, self.total),
            "correct": _zero_div(self.correct, self.total),
        }

    def calculate_avg(self, num_samples: int):
        self.avg = {
            "total": _zero_div(self.total, num_samples),
            # TODO: Should we divide by num_samples - llm_call_exceptions ?
            "llm": _zero_div(self.llm, num_samples),
            # TODO: Should we divide by num_samples - llm_call_exceptions - invalid_jsons ?
            "blockchain": _zero_div(self.blockchain, num_samples),
            # TODO: Should we divide by num_samples - llm_call_exceptions - invalid_jsons - pydantic_exceptions ?
            "correct": _zero_div(self.correct, num_samples),
        }


@dataclass
class TokenStats(Stats):
    input: int = 0
    output: int = 0

    def calculate_pct(self):
        self.pct = {
            "input": _zero_div(self.input, self.total),
            "output": _zero_div(self.output, self.total),
        }

    def calculate_avg(self, num_samples: int):
        # TODO: Should we divide by num_samples - llm_call_exceptions ?
        self.avg = {
            "total": _zero_div(self.total, num_samples),
            "input": _zero_div(self.input, num_samples),
            "output": _zero_div(self.output, num_samples),
        }


@dataclass
class ParsedFieldStats(Stats):
    correct: int = 0
    missing_key: int = 0
    type_mismatch: int = 0
    value_mismatch: int = 0
    pydantic_error: int = 0

    def calculate_pct(self):
        self.pct = {
            "correct": _zero_div(self.correct, self.total),
            "missing_key": _zero_div(self.missing_key, self.total),
            "type_mismatch": _zero_div(self.type_mismatch, self.total),
            "value_mismatch": _zero_div(self.value_mismatch, self.total),
            "pydantic_error": _zero_div(self.pydantic_error, self.total),
        }

    def calculate_avg(self, num_samples: int):
        self.avg = {
            "total": _zero_div(self.total, num_samples),
            "correct": _zero_div(self.correct, num_samples),
            "missing_key": _zero_div(self.missing_key, num_samples),
            "type_mismatch": _zero_div(self.type_mismatch, num_samples),
            "value_mismatch": _zero_div(self.value_mismatch, num_samples),
            "pydantic_error": _zero_div(self.pydantic_error, num_samples),
        }


@dataclass
class DirectMappingStats:
    samples: SampleStats = field(default_factory=SampleStats)
    time: TimeStats = field(default_factory=TimeStats)
    tokens: TokenStats = field(default_factory=TokenStats)
    parsed_fields: ParsedFieldStats = field(default_factory=ParsedFieldStats)

    def calculate_pct(self):
        self.samples.calculate_pct()
        self.time.calculate_pct()
        self.tokens.calculate_pct()
        self.parsed_fields.calculate_pct()

    def calculate_avg(self):
        self.time.calculate_avg(self.samples.total)
        self.tokens.calculate_avg(self.samples.total)
        self.parsed_fields.calculate_avg(self.samples.total)

    def plots(self):
        titles = [
            "Sample Statistics",
            "Time Statistics",
            "Token Statistics",
            "Parsed Field Statistics",
        ]
        file_names = ["sample_stats", "time_stats", "token_stats", "parsed_field_stats"]
        stats: list[Stats] = [
            self.samples,
            self.time,
            self.tokens,
            self.parsed_fields,
        ]

        for file_name, title, stat in zip(file_names, titles, stats):
            fig = stat.plot(title)
            yield file_name, fig
            plt.close(fig)

    def __iadd__(self, other):
        if not isinstance(other, DirectMappingStats):
            return NotImplemented

        self.samples += other.samples
        self.time += other.time
        self.tokens += other.tokens
        self.parsed_fields += other.parsed_fields

        return self


@dataclass
class SampleStatsMF(Stats):
    llm_call_exception: int = 0
    no_code_block: int = 0
    function_syntax_error: int = 0
    function_not_found: int = 0
    function_not_callable: int = 0
    function_execution_exception: int = 0
    function_return_type: int = 0
    pydantic_exception: int = 0
    false_positive: int = 0
    correct: int = 0

    def calculate_pct(self):
        self.pct = {
            "llm_call_exception": _zero_div(self.llm_call_exception, self.total),
            "no_code_block": _zero_div(self.no_code_block, self.total),
            "function_syntax_error": _zero_div(self.function_syntax_error, self.total),
            "function_not_found": _zero_div(self.function_not_found, self.total),
            "function_not_callable": _zero_div(self.function_not_callable, self.total),
            "function_execution_exception": _zero_div(
                self.function_execution_exception, self.total
            ),
            "function_return_type": _zero_div(self.function_return_type, self.total),
            "pydantic_exception": _zero_div(self.pydantic_exception, self.total),
            "false_positive": _zero_div(self.false_positive, self.total),
            "correct": _zero_div(self.correct, self.total),
        }


@dataclass
class MappingFunctionStats(DirectMappingStats):
    samples: SampleStatsMF = field(default_factory=SampleStatsMF)
