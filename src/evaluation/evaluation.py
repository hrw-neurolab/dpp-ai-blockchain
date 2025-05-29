import os
import json
from dataclasses import asdict
import re

from langchain_core.utils.json import parse_json_markdown
from loguru import logger

from src.evaluation.stats import DirectMappingStats, MappingFunctionStats


def _evaluate_validation_error(
    output: dict, target: dict, stats: DirectMappingStats | MappingFunctionStats
):
    """Evaluate the validation error and update the stats accordingly.

    Args:
        output (dict): The output dictionary containing the generated content.
        target (dict): The target dictionary to compare against.
        stats (DirectMappingStats | MappingFunctionStats): The stats object to update.
    """
    for key, value in target.items():
        if key not in output:
            stats.parsed_fields.missing_key += 1
            continue

        if type(output[key]) != type(value):
            stats.parsed_fields.type_mismatch += 1
            continue

        if output[key] != value:
            stats.parsed_fields.value_mismatch += 1
            continue

        stats.parsed_fields.correct += 1


def _strip_thinking_tags(response_raw: str) -> str:
    return re.sub(
        r"<think>.*?</think>\s*",
        "",
        response_raw,
        flags=re.DOTALL,
    ).strip()


def evaluate_direct_mapping(run_dir: str):
    """Evaluate the mapping results for the prompting techniques: few_shot, schema_driven.

    Args:
        run_dir (str): The directory containing the run results.
    """
    raw_results_dir = os.path.join(run_dir, "raw_results")
    plots_dir = os.path.join(run_dir, "plots")
    os.makedirs(plots_dir, exist_ok=True)

    metrics = {}
    wrong_samples = {}

    # Loop through the jsonl files
    for file_name in os.listdir(raw_results_dir):
        machine_id = file_name.split(".")[0]

        wrong_samples[machine_id] = {
            "llm_call_exception": [],
            "invalid_json": [],
            "pydantic_exception": [],
            "false_positive": [],
        }

        # Read the jsonl file and convert it to json
        input_file_path = os.path.join(raw_results_dir, file_name)
        with open(input_file_path, "r") as f:
            lines = f.readlines()

        results = [json.loads(line) for line in lines]
        del lines

        output_file_path = os.path.join(raw_results_dir, f"{machine_id}.json")
        with open(output_file_path, "w") as f:
            json.dump(results, f, indent=4)

        os.remove(input_file_path)

        # Accumulate the machine stats
        stats = DirectMappingStats()
        stats.samples.total = len(results)

        for index, result in enumerate(results):
            logger.info(
                f"[{machine_id}: {index + 1:03}/{stats.samples.total:03}] Evaluating..."
            )

            stats.time.total += result["total_time"]

            mapping_result = result["llm_mapping"]
            if mapping_result["error_type"] == "LLM_CALL_EXCEPTION":
                stats.samples.llm_call_exception += 1
                wrong_samples[machine_id]["llm_call_exception"].append(
                    {
                        "index": index,
                        "error_msg": mapping_result["error_msg"],
                    }
                )
                continue

            stats.time.llm += mapping_result["llm_time"]
            stats.tokens.total += mapping_result["total_tokens"]
            stats.tokens.input += mapping_result["input_tokens"]
            stats.tokens.output += mapping_result["output_tokens"]

            if mapping_result["error_type"] == "PARSING_EXCEPTION":
                stats.samples.invalid_json += 1
                wrong_samples[machine_id]["invalid_json"].append(
                    {
                        "index": index,
                        "response_raw": mapping_result["response_raw"],
                        "error_msg": mapping_result["error_msg"],
                    }
                )
                continue

            output = _strip_thinking_tags(mapping_result["response_raw"])
            output = parse_json_markdown(output)
            stats.parsed_fields.total += len(output)

            if mapping_result["error_type"] == "PYDANTIC_VALIDATION_ERROR":
                _evaluate_validation_error(output, result["target"], stats)
                stats.parsed_fields.pydantic_error += len(mapping_result["error_msg"])
                stats.samples.pydantic_exception += 1
                wrong_samples[machine_id]["pydantic_exception"].append(
                    {
                        "index": index,
                        "response_parsed": output,
                        "error_msg": mapping_result["error_msg"],
                    }
                )
                continue

            stats.time.blockchain += result.get("blockchain_time", 0)

            # Check if there are wrong values since pydantic only checks types
            value_mismatches = [
                key for key, value in result["target"].items() if output[key] != value
            ]
            num_value_mismatches = len(value_mismatches)

            num_correct = len(output) - num_value_mismatches
            stats.parsed_fields.correct += num_correct

            if num_value_mismatches > 0:
                stats.samples.false_positive += 1
                stats.parsed_fields.value_mismatch += num_value_mismatches
                wrong_samples[machine_id]["false_positive"].append(
                    {
                        "index": index,
                        "response_parsed": {k: output[k] for k in value_mismatches},
                        "target": {k: result["target"][k] for k in value_mismatches},
                    }
                )
                continue

            # If we reach here, the mapping was 100% successful
            stats.samples.correct += 1
            stats.time.correct += result["total_time"]

        # Calculate the machine metrics
        stats.calculate_pct()
        stats.calculate_avg()

        metrics[machine_id] = stats

    # Accumulate the overall stats
    logger.info(f"Calculating overall metrics")
    overall_stats = DirectMappingStats()

    for machine_stat in metrics.values():
        overall_stats += machine_stat

    # Calculate the overall metrics
    overall_stats.calculate_pct()
    overall_stats.calculate_avg()
    metrics["overall"] = overall_stats

    # Convert the metrics to a dictionary
    metrics_dict = dict()
    for machine_id, machine_stat in metrics.items():
        metrics_dict[machine_id] = asdict(machine_stat)

    output_file_path = os.path.join(run_dir, f"metrics.json")
    with open(output_file_path, "w") as f:
        json.dump(metrics_dict, f, indent=4)

    logger.info(f"Metrics saved to: {output_file_path}")

    # Save the wrong samples to a json file
    wrong_samples_file_path = os.path.join(run_dir, f"wrong_samples.json")
    with open(wrong_samples_file_path, "w") as f:
        json.dump(wrong_samples, f, indent=4)

    logger.info(f"Wrong samples saved to: {wrong_samples_file_path}")

    # Save the plot figures
    for machine_id, machine_stat in metrics.items():
        machine_plots_dir = os.path.join(plots_dir, machine_id)
        os.makedirs(machine_plots_dir, exist_ok=True)

        for file_name, plot in machine_stat.plots():
            file_path = os.path.join(machine_plots_dir, file_name + ".pdf")
            plot.savefig(file_path, format="pdf")

    logger.info(f"Plots saved to: {plots_dir}")


def evaluate_mapping_function(run_dir: str):
    """Evaluate the mapping results for the mapping function technique.

    Args:
        run_dir (str): The directory containing the run results.
    """
    raw_results_dir = os.path.join(run_dir, "raw_results")
    plots_dir = os.path.join(run_dir, "plots")
    os.makedirs(plots_dir, exist_ok=True)

    parsed_fns_dir = os.path.join(run_dir, "parsed_functions")
    os.makedirs(parsed_fns_dir, exist_ok=True)

    stats = MappingFunctionStats()

    # Loop through the json files
    for file_name in os.listdir(raw_results_dir):
        machine_id = file_name.split(".")[0]
        logger.info(f"[{machine_id}] Evaluating...")

        # Read the json file
        file_path = os.path.join(raw_results_dir, file_name)
        with open(file_path, "r") as f:
            result = json.load(f)

        # Accumulate the results
        stats.samples.total += 1
        stats.time.total += result["total_time"]

        mapping_result = result["llm_mapping"]
        if mapping_result["error_type"] == "LLM_CALL_EXCEPTION":
            stats.samples.llm_call_exception += 1
            continue

        stats.time.llm += mapping_result["llm_time"]
        stats.tokens.total += mapping_result["total_tokens"]
        stats.tokens.input += mapping_result["input_tokens"]
        stats.tokens.output += mapping_result["output_tokens"]

        if mapping_result["error_type"] == "NO_CODE_BLOCK":
            stats.samples.no_code_block += 1
            continue

        if mapping_result["error_type"] == "FUNCTION_SYNTAX_ERROR":
            stats.samples.function_syntax_error += 1
            continue

        if mapping_result["error_type"] == "FUNCTION_NOT_FOUND":
            stats.samples.function_not_found += 1
            continue

        if mapping_result["error_type"] == "FUNCTION_NOT_CALLABLE":
            stats.samples.function_not_callable += 1
            continue

        # Save the parsed function
        parsed_fn_file_path = os.path.join(parsed_fns_dir, f"{machine_id}.py")
        with open(parsed_fn_file_path, "w") as f:
            f.write(mapping_result["response_parsed"])

        if mapping_result["error_type"] == "FUNCTION_EXECUTION_EXCEPTION":
            stats.samples.function_execution_exception += 1
            continue

        if mapping_result["error_type"] == "FUNCTION_RETURN_TYPE":
            stats.samples.function_return_type += 1
            continue

        output = mapping_result["function_result"]
        stats.parsed_fields.total += len(output)

        if mapping_result["error_type"] == "PYDANTIC_VALIDATION_ERROR":
            # Try to find the reason for the validation error
            _evaluate_validation_error(output, result["target"], stats)
            stats.parsed_fields.pydantic_error += len(mapping_result["error_msg"])
            stats.samples.pydantic_exception += 1
            continue

        # Check if there are wrong values since pydantic only checks types
        num_value_mismatches = sum(
            [1 for key, value in result["target"].items() if output[key] != value]
        )
        num_correct = len(output) - num_value_mismatches
        stats.parsed_fields.correct += num_correct

        if num_value_mismatches > 0:
            stats.samples.false_positive += 1
            stats.parsed_fields.value_mismatch += num_value_mismatches
            continue

        # If we reach here, the mapping was 100% successful
        stats.samples.correct += 1
        stats.time.correct += result["total_time"]

    # Calculate the metrics
    logger.info(f"Calculating metrics")
    stats.calculate_pct()
    stats.calculate_avg()

    stats_dict = asdict(stats)

    output_file_path = os.path.join(run_dir, f"metrics.json")
    with open(output_file_path, "w") as f:
        json.dump(stats_dict, f, indent=4)

    logger.info(f"Metrics saved to: {output_file_path}")

    # Save the plot figures
    for file_name, plot in stats.plots():
        file_path = os.path.join(plots_dir, file_name + ".pdf")
        plot.savefig(file_path, format="pdf")

    logger.info(f"Plots saved to: {plots_dir}")
