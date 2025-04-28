import json
import argparse
import os
import shutil
import sys
from typing import Literal

from loguru import logger

from src.evaluation.evaluation import evaluate_direct_mapping, evaluate_mapping_function


def init_loguru(run_dir: str):
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
        level="INFO",
        colorize=True,
    )
    logger.add(
        os.path.join(run_dir, "rerun_evaluation.log"),
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> "
        "| <level>{level: <8}</level> "
        "| <cyan>{file: <15}</cyan>:<cyan>{line: <3}</cyan> "
        "-> <level>{message}</level>",
    )


def reset_run_dir(run_dir: str):
    # delete the plots directory
    plots_dir = os.path.join(run_dir, "plots")
    if os.path.exists(plots_dir):
        shutil.rmtree(plots_dir)

    # delete the metrics.json file
    metrics_file = os.path.join(run_dir, "metrics.json")
    if os.path.exists(metrics_file):
        os.remove(metrics_file)

    # delete the wrong_samples.json file
    metrics_file = os.path.join(run_dir, "wrong_samples.json")
    if os.path.exists(metrics_file):
        os.remove(metrics_file)

    # convert every .json in raw_results back to .jsonl
    raw_results_dir = os.path.join(run_dir, "raw_results")
    for filename in os.listdir(raw_results_dir):
        if not filename.endswith(".json"):
            continue

        json_file_path = os.path.join(raw_results_dir, filename)
        with open(json_file_path, "r") as f:
            data = json.load(f)

        jsonl_file_path = os.path.join(
            raw_results_dir, filename.replace(".json", ".jsonl")
        )
        with open(jsonl_file_path, "w") as f:
            for item in data:
                f.write(json.dumps(item) + "\n")

        os.remove(json_file_path)


def run_evaluation(run_dir: str):
    # Load the configuration file
    config_file = os.path.join(run_dir, "config.json")
    with open(config_file, "r") as f:
        config = json.load(f)

    prompt: Literal["schema_driven", "few_shot", "mapping_function"] = config["prompt"]

    # Run the evaluation based on the prompt type
    if prompt in ["schema_driven", "few_shot"]:
        evaluate_direct_mapping(run_dir)
        return

    evaluate_mapping_function(run_dir)


def main(run_dir: str):
    if not os.path.exists(run_dir):
        print(f"Run directory {run_dir} does not exist.")
        return

    # Initialize logging
    init_loguru(run_dir)
    logger.warning(f"Restarting the evaluation process for {run_dir}")

    # Reset the output directory
    logger.info("Resetting the run directory...")
    reset_run_dir(run_dir)

    # Run the evaluation
    logger.info("Running the evaluation...")
    run_evaluation(run_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="This script re-runs the evaluation for a given output folder."
    )
    parser.add_argument(
        "--run-dir",
        type=str,
        required=True,
        help="Path to the output folder containing the evaluation results.",
    )

    args = parser.parse_args()
    main(args.run_dir)
