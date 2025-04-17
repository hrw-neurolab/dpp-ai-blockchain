import argparse
from dotenv import load_dotenv

from study.run_pipeline import RunPipeline


def main(args):
    load_dotenv()
    pipeline = RunPipeline(args)
    pipeline.run()
    pipeline.evaluate()


if __name__ == "__main__":
    load_dotenv()

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
        choices=["gpt", "ollama"],
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
