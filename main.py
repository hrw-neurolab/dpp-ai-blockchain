import argparse
import sys

from dotenv import load_dotenv
from loguru import logger

from study.run_pipeline import RunPipeline


def main(args):
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
        "--output-dir",
        type=str,
        default="./output",
        help="Directory to save the processed output files.",
    )
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
        choices=["few_shot", "schema_driven", "mapping_function"],
        help="The prompt type to use for evaluation.",
    )
    parser.add_argument(
        "--single-sample",
        action="store_true",
        help="Run the evaluation on a single sample instead of the entire dataset.",
    )

    args = parser.parse_args()
    main(args)
