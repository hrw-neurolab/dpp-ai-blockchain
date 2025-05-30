import argparse
import sys

from dotenv import load_dotenv
from loguru import logger

from src.run_pipeline import RunPipeline


def main(args):
    if args.resume is not None:
        pipeline = RunPipeline.from_run_dir(args.resume)
    else:
        pipeline = RunPipeline(args)

    pipeline.run()
    pipeline.evaluate()


def init_loguru():
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
        level="INFO",
        colorize=True,
    )


if __name__ == "__main__":
    load_dotenv()
    init_loguru()

    parser = argparse.ArgumentParser(
        description="This script performs an evaluation of LLM JSON mapping capabilities."
    )
    parser.add_argument(
        "--resume",
        type=str,
        help="The path to a previous run's output directory to resume from.",
    )

    if "--resume" in sys.argv:
        args = parser.parse_args()
        main(args)
        sys.exit(0)

    parser.add_argument(
        "--model-provider",
        type=str,
        required=True,
        choices=["openai", "ollama"],
        help="The provider of the LLM model to use for evaluation.",
    )
    parser.add_argument(
        "--model-name",
        type=str,
        required=True,
        help="The name of the LLM model to use for evaluation.",
    )
    parser.add_argument(
        "--prompt",
        type=str,
        required=True,
        choices=["zero-shot", "few-shot", "mapping-function"],
        help="The prompt type to use for evaluation.",
    )
    parser.add_argument(
        "--include-schema",
        action="store_true",
        help="Flag to indicate whether to include the schema in the prompt.",
    )
    parser.add_argument(
        "--difficulty",
        type=str,
        required=True,
        choices=["simple", "moderate", "complex"],
        help="The difficulty level of the dataset to use for evaluation.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./output",
        help="Directory to save the processed output files.",
    )
    parser.add_argument(
        "--cache-dir",
        type=str,
        default="./data",
        help="Directory to cache the datasets and few-shot prompts.",
    )
    parser.add_argument(
        "--num-samples",
        type=int,
        default=None,
        help="Number of samples to use for evaluation. If None, all samples will be used.",
    )
    parser.add_argument(
        "--blockchain",
        action="store_true",
        help="Flag to indicate whether to push the parsed data to the blockchain.",
    )
    parser.add_argument(
        "--ollama-host",
        type=str,
        default="127.0.0.1:11434",
        help="Host address for the Ollama model server.",
    )
    parser.add_argument(
        "--max-refinement-attempts",
        type=int,
        default=0,
        help="Maximum number of refinement attempts for the model.",
    )
    parser.add_argument(
        "--structured-output",
        type=str,
        choices=["function_calling", "json_mode", "json_schema"],
        help="Structured output mode for the model. Not applicable to `mapping-function` prompt.",
    )
    parser.add_argument(
        "--wrap-thinking",
        action="store_true",
        help="Whether to wrap the thinnking content in a seperate field in the output. (Only for structured output modes)",
    )

    args = parser.parse_args()
    main(args)
