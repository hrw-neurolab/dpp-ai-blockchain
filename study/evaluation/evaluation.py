import os
import json
from dataclasses import asdict

from langchain_core.utils.json import parse_json_markdown
from loguru import logger

from study.evaluation.stats import DirectMappingStats, MappingFunctionStats


def _evaluate_parsing_exception(result: dict, stats: DirectMappingStats):
    """Evaluate the parsing exception and update the stats accordingly.

    Args:
        result (dict): The result dictionary containing the parsing exception.
        stats (DirectMappingStats): The stats object to update.
    """
    try:
        output = parse_json_markdown(result["raw_response"])
        for key, value in result["target"].items():
            if key not in output:
                stats.num_missing_keys += 1
                break

            if type(output[key]) != type(value):
                stats.num_type_mismatches += 1
                break

            if output[key] != value:
                stats.num_value_mismatches += 1
                break

    except Exception as e:
        stats.num_invalid_json += 1


def evaluate_direct_mapping(run_dir: str):
    """Evaluate the mapping results for the prompting techniques: few_shot, schema_driven.

    Args:
        run_dir (str): The directory containing the run results.
    """
    os.makedirs(os.path.join(run_dir, "raw_results"), exist_ok=True)

    metrics = {}

    # Loop through the jsonl files
    for file_name in os.listdir(run_dir):
        if not file_name.endswith("_result.jsonl"):
            continue

        machine_id = file_name.split("_")[0]

        # Read the jsonl file and convert it to json
        input_file_path = os.path.join(run_dir, file_name)
        output_file_path = os.path.join(run_dir, "raw_results", f"{machine_id}.json")

        with open(input_file_path, "r") as f:
            lines = f.readlines()

        machine_results = [json.loads(line) for line in lines]
        del lines
        with open(output_file_path, "w") as f:
            json.dump(machine_results, f, indent=4)

        os.remove(input_file_path)

        # Accumulate the machine stats
        stats = DirectMappingStats()
        stats.num_samples = len(machine_results)

        for index, result in enumerate(machine_results):
            logger.info(
                f"[{machine_id}: {index + 1:03}/{stats.num_samples}] Evaluating..."
            )

            stats.total_runtime += result["total_time"]

            mapping_result = result["llm_mapping"]
            if mapping_result["error_type"] == "LLM_CALL_EXCEPTION":
                stats.num_llm_call_exceptions += 1
                continue

            if mapping_result["error_type"] == "PARSING_EXCEPTION":
                # Try to find the reason for the parsing exception
                _evaluate_parsing_exception(result, stats)
                continue

            stats.num_samples_correct += 1
            stats.total_tokens += mapping_result["total_tokens"]
            stats.total_input_tokens += mapping_result["input_tokens"]
            stats.total_output_tokens += mapping_result["output_tokens"]
            stats.total_llm_time_correct += mapping_result["llm_time"]
            stats.total_time_correct += result["total_time"]
            stats.total_blockchain_time += result["blockchain_time"]

        # Calculate the machine metrics
        stats.calculate_pct()
        stats.calculate_avg()

        metrics[machine_id] = stats

    # Accumulate the overall stats
    logger.info(f"Calculating overall metrics")
    overall_stats = DirectMappingStats()

    for machine_stat in metrics.values():
        overall_stats.total_runtime += machine_stat.total_runtime
        overall_stats.num_samples += machine_stat.num_samples
        overall_stats.num_samples_correct += machine_stat.num_samples_correct
        overall_stats.num_llm_call_exceptions += machine_stat.num_llm_call_exceptions
        overall_stats.num_invalid_json += machine_stat.num_invalid_json
        overall_stats.num_missing_keys += machine_stat.num_missing_keys
        overall_stats.num_type_mismatches += machine_stat.num_type_mismatches
        overall_stats.num_value_mismatches += machine_stat.num_value_mismatches
        overall_stats.total_tokens += machine_stat.total_tokens
        overall_stats.total_input_tokens += machine_stat.total_input_tokens
        overall_stats.total_output_tokens += machine_stat.total_output_tokens
        overall_stats.total_time_correct += machine_stat.total_time_correct
        overall_stats.total_llm_time_correct += machine_stat.total_llm_time_correct
        overall_stats.total_blockchain_time += machine_stat.total_blockchain_time

    # Calculate the overall metrics
    overall_stats.calculate_pct()
    overall_stats.calculate_avg()
    metrics["overall"] = overall_stats

    # Convert the metrics to a dictionary
    for machine_id, machine_stat in metrics.items():
        metrics[machine_id] = asdict(machine_stat)

    output_file_path = os.path.join(run_dir, f"metrics.json")
    with open(output_file_path, "w") as f:
        json.dump(metrics, f, indent=4)

    logger.info(f"Metrics saved to: {output_file_path}")


def evaluate_mapping_function(run_dir: str):
    """Evaluate the mapping results for the mapping function technique.

    Args:
        run_dir (str): The directory containing the run results.
    """
    os.makedirs(os.path.join(run_dir, "raw_results"), exist_ok=True)

    stats = MappingFunctionStats()

    # Loop through the json files
    for file_name in os.listdir(run_dir):
        if not file_name.endswith("_result.json"):
            continue

        machine_id = file_name.split("_")[0]
        stats.num_samples += 1
        logger.info(f"[{machine_id}] {stats.num_samples:03}/{stats.num_samples}")

        # Read the json file
        input_file_path = os.path.join(run_dir, file_name)

        with open(input_file_path, "r") as f:
            machine_results = json.load(f)

        # Move the raw results
        output_file_path = os.path.join(run_dir, "raw_results", f"{machine_id}.json")
        with open(output_file_path, "w") as f:
            json.dump(machine_results, f, indent=4)

        os.remove(input_file_path)

        # Accumulate the results
        stats.total_runtime += machine_results["total_time"]

        mapping_result = machine_results["llm_mapping"]
        if mapping_result["error_type"] == "LLM_CALL_EXCEPTION":
            stats.num_llm_call_exceptions += 1
            continue

        if mapping_result["error_type"] == "NO_CODE_BLOCK":
            stats.num_no_code_block += 1
            continue

        if mapping_result["error_type"] == "FUNCTION_NOT_FOUND":
            stats.num_function_not_found += 1
            continue

        if mapping_result["error_type"] == "FUNCTION_NOT_CALLABLE":
            stats.num_function_not_callable += 1
            continue

        if mapping_result["error_type"] == "FUNCTION_EXECUTION_EXCEPTION":
            stats.num_function_execution_exception += 1
            continue

        if mapping_result["error_type"] == "FUNCTION_RETURN_TYPE":
            stats.num_function_return_type += 1
            continue

        # If we reach here, the mapping was successful
        stats.num_samples_correct += 1
        stats.total_tokens += mapping_result["total_tokens"]
        stats.total_input_tokens += mapping_result["input_tokens"]
        stats.total_output_tokens += mapping_result["output_tokens"]

    # Calculate the metrics
    logger.info(f"Calculating metrics")
    stats.calculate_pct()
    stats.calculate_avg()

    stats = asdict(stats)

    output_file_path = os.path.join(run_dir, f"metrics.json")
    with open(output_file_path, "w") as f:
        json.dump(stats, f, indent=4)

    logger.info(f"Metrics saved to: {output_file_path}")
