from typing import Literal


ModelProvider = Literal["openai", "ollama"]
"""Options for the Model provider."""

PromptType = Literal["zero-shot", "few-shot", "mapping-function"]
"""Options for the type of prompt used."""

Difficulty = Literal["simple", "moderate", "complex"]
"""Options for the difficulty level of the dataset."""

StructuredOutput = Literal["function_calling", "json_mode", "json_schema"]
"""Options for the structured output method used by the LLM provider."""
