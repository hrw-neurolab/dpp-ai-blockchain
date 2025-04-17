import os
import json

from langchain_core.utils.json import parse_json_markdown


def evaluate_direct_mapping(run_dir: str):
    # Create the directory if it doesn't exist
    os.makedirs(os.path.join(run_dir, "raw_results"), exist_ok=True)

    metrics = {}
    total_runtime = 0.0

    # loop through the jsonl files
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

        # Evaluate the results
        stats = {
            "num_samples": len(machine_results),
            "num_samples_correct": 0,
            "num_llm_call_exceptions": 0,
            "num_parsing_exceptions": 0,
            "num_missing_keys": 0,
            "num_type_mismatches": 0,
            "num_value_mismatches": 0,
            "total_time_correct": 0.0,
            "total_llm_time_correct": 0.0,
            "total_blockchain_time": 0.0,
        }

        for result in machine_results:
            total_runtime += result["total_time"]

            mapping_result = result["llm_mapping"]
            if mapping_result["error_type"] == "LLM_CALL_EXCEPTION":
                stats["num_llm_call_exceptions"] += 1
                continue

            if mapping_result["error_type"] == "PARSING_EXCEPTION":
                # Try to find the reason for the parsing exception
                try:
                    output = parse_json_markdown(result["raw_response"])
                    for key, value in result["target"].items():
                        if key not in output:
                            stats["num_missing_keys"] += 1
                            break

                        if type(output[key]) != type(value):
                            stats["num_type_mismatches"] += 1
                            break

                        if output[key] != value:
                            stats["num_value_mismatches"] += 1
                            break

                except Exception as e:
                    stats["num_parsing_exceptions"] += 1

                continue

            stats["num_samples_correct"] += 1
            stats["total_llm_time_correct"] += mapping_result["llm_time"]
            stats["total_time_correct"] += result["total_time"]
            stats["total_blockchain_time"] += result["blockchain_time"]

        # Calculate the machine metrics
        stats["pct_samples_correct"] = (
            stats["num_samples_correct"] / stats["num_samples"]
        )
        stats["pct_llm_call_exceptions"] = (
            stats["num_llm_call_exceptions"] / stats["num_samples"]
        )
        stats["pct_parsing_exceptions"] = (
            stats["num_parsing_exceptions"] / stats["num_samples"]
        )
        stats["pct_missing_keys"] = stats["num_missing_keys"] / stats["num_samples"]
        stats["pct_type_mismatches"] = (
            stats["num_type_mismatches"] / stats["num_samples"]
        )
        stats["pct_value_mismatches"] = (
            stats["num_value_mismatches"] / stats["num_samples"]
        )

        if stats["num_samples_correct"] > 0:
            stats["avg_time_correct"] = (
                stats["total_time_correct"] / stats["num_samples_correct"]
            )
            stats["avg_llm_time_correct"] = (
                stats["total_llm_time_correct"] / stats["num_samples_correct"]
            )
            stats["avg_blockchain_time"] = (
                stats["total_blockchain_time"] / stats["num_samples_correct"]
            )
        else:
            stats["avg_time_correct"] = 0.0
            stats["avg_llm_time_correct"] = 0.0
            stats["avg_blockchain_time"] = 0.0

        metrics[machine_id] = stats

    # Calculate the overall metrics
    total_samples = sum([m["num_samples"] for m in metrics.values()])
    total_samples_correct = sum([m["num_samples_correct"] for m in metrics.values()])
    total_llm_call_exceptions = sum(
        [m["num_llm_call_exceptions"] for m in metrics.values()]
    )
    total_parsing_exceptions = sum(
        [m["num_parsing_exceptions"] for m in metrics.values()]
    )
    total_missing_keys = sum([m["num_missing_keys"] for m in metrics.values()])
    total_type_mismatches = sum([m["num_type_mismatches"] for m in metrics.values()])
    total_value_mismatches = sum([m["num_value_mismatches"] for m in metrics.values()])
    total_time_correct = sum([m["total_time_correct"] for m in metrics.values()])
    total_llm_time_correct = sum(
        [m["total_llm_time_correct"] for m in metrics.values()]
    )
    total_blockchain_time = sum([m["total_blockchain_time"] for m in metrics.values()])

    pct_samples_correct = total_samples_correct / total_samples
    pct_llm_call_exceptions = total_llm_call_exceptions / total_samples
    pct_parsing_exceptions = total_parsing_exceptions / total_samples
    pct_missing_keys = total_missing_keys / total_samples
    pct_type_mismatches = total_type_mismatches / total_samples
    pct_value_mismatches = total_value_mismatches / total_samples

    if total_samples_correct > 0:
        avg_time_correct = total_time_correct / total_samples_correct
        avg_llm_time_correct = total_llm_time_correct / total_samples_correct
        avg_blockchain_time = total_blockchain_time / total_samples_correct
    else:
        avg_time_correct = 0.0
        avg_llm_time_correct = 0.0
        avg_blockchain_time = 0.0

    metrics["overall"] = {
        "total_runtime": total_runtime,
        "num_samples": total_samples,
        "num_samples_correct": total_samples_correct,
        "num_llm_call_exceptions": total_llm_call_exceptions,
        "num_parsing_exceptions": total_parsing_exceptions,
        "num_missing_keys": total_missing_keys,
        "num_type_mismatches": total_type_mismatches,
        "num_value_mismatches": total_value_mismatches,
        "total_time_correct": total_time_correct,
        "total_llm_time_correct": total_llm_time_correct,
        "total_blockchain_time": total_blockchain_time,
        "pct_samples_correct": pct_samples_correct,
        "pct_llm_call_exceptions": pct_llm_call_exceptions,
        "pct_parsing_exceptions": pct_parsing_exceptions,
        "pct_missing_keys": pct_missing_keys,
        "pct_type_mismatches": pct_type_mismatches,
        "pct_value_mismatches": pct_value_mismatches,
        "avg_time_correct": avg_time_correct,
        "avg_llm_time_correct": avg_llm_time_correct,
        "avg_blockchain_time": avg_blockchain_time,
    }

    output_file_path = os.path.join(run_dir, f"metrics.json")
    with open(output_file_path, "w") as f:
        json.dump(metrics, f, indent=4)


def evaluate_mapping_function(run_dir: str):
    # Create the directory if it doesn't exist
    os.makedirs(os.path.join(run_dir, "raw_results"), exist_ok=True)

    metrics = {
        "num_samples": 0,
        "num_samples_correct": 0,
        "num_llm_call_exceptions": 0,
        "num_no_code_block": 0,
        "num_function_not_found": 0,
        "num_function_not_callable": 0,
        "num_function_execution_exception": 0,
        "num_function_return_type": 0,
    }
    total_runtime = 0.0

    # loop through the json files
    for file_name in os.listdir(run_dir):
        if not file_name.endswith("_result.json"):
            continue

        metrics["num_samples"] += 1

        # Read the json file
        input_file_path = os.path.join(run_dir, file_name)

        with open(input_file_path, "r") as f:
            machine_results = json.load(f)

        # Move the raw results
        machine_id = file_name.split("_")[0]
        output_file_path = os.path.join(run_dir, "raw_results", f"{machine_id}.json")
        with open(output_file_path, "w") as f:
            json.dump(machine_results, f, indent=4)
        os.remove(input_file_path)

        # Evaluate the results
        total_runtime += machine_results["total_time"]

        mapping_result = machine_results["llm_mapping"]
        if mapping_result["error_type"] == "LLM_CALL_EXCEPTION":
            metrics["num_llm_call_exceptions"] += 1
            continue

        if mapping_result["error_type"] == "NO_CODE_BLOCK":
            metrics["num_no_code_block"] += 1
            continue

        if mapping_result["error_type"] == "FUNCTION_NOT_FOUND":
            metrics["num_function_not_found"] += 1
            continue

        if mapping_result["error_type"] == "FUNCTION_NOT_CALLABLE":
            metrics["num_function_not_callable"] += 1
            continue

        if mapping_result["error_type"] == "FUNCTION_EXECUTION_EXCEPTION":
            metrics["num_function_execution_exception"] += 1
            continue

        if mapping_result["error_type"] == "FUNCTION_RETURN_TYPE":
            metrics["num_function_return_type"] += 1
            continue

        # If we reach here, the mapping was successful
        metrics["num_samples_correct"] += 1

    # Calculate the metrics
    metrics["pct_samples_correct"] = (
        metrics["num_samples_correct"] / metrics["num_samples"]
    )
    metrics["pct_llm_call_exceptions"] = (
        metrics["num_llm_call_exceptions"] / metrics["num_samples"]
    )
    metrics["pct_no_code_block"] = metrics["num_no_code_block"] / metrics["num_samples"]
    metrics["pct_function_not_found"] = (
        metrics["num_function_not_found"] / metrics["num_samples"]
    )
    metrics["pct_function_not_callable"] = (
        metrics["num_function_not_callable"] / metrics["num_samples"]
    )
    metrics["pct_function_execution_exception"] = (
        metrics["num_function_execution_exception"] / metrics["num_samples"]
    )
    metrics["pct_function_return_type"] = metrics["num_function_return_type"] / (
        metrics["num_samples"]
    )
    metrics["total_runtime"] = total_runtime
    metrics["avg_runtime"] = total_runtime / metrics["num_samples"]

    output_file_path = os.path.join(run_dir, f"metrics.json")
    with open(output_file_path, "w") as f:
        json.dump(metrics, f, indent=4)
