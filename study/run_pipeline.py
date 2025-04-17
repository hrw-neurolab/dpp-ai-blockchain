import time
import os
import json

from llm_mapping import LlmMapping
from WavesConnector import MetricCaller
from study.evaluation import evaluate_direct_mapping, evaluate_mapping_function


class RunPipeline:
    def __init__(self, args):
        self.args = args
        self.__init_run_dir()
        self.__init_datasets()

        self.llm_mapping = LlmMapping(args.model_provider, args.model_name, args.prompt)
        self.metric_caller = MetricCaller()
        self.__save_config()
        self.__save_prompt()

    def __init_run_dir(self):
        run_name = f"run_{self.args.prompt}_{time.strftime('%Y%m%d_%H%M%S')}"
        self.run_dir = os.path.join(self.args.output_dir, run_name)
        os.makedirs(self.run_dir, exist_ok=True)

    def __save_config(self):
        config_file_path = os.path.join(self.run_dir, "config.json")
        with open(config_file_path, "w") as f:
            json.dump(vars(self.args), f, indent=4)

    def __save_prompt(self):
        prompt_file_path = os.path.join(self.run_dir, "prompt.txt")
        with open(prompt_file_path, "w") as f:
            f.write(self.llm_mapping.prompt.invoke({}).to_string())

    def __init_datasets(self):
        dataset_dir = "./dataset"

        source_file_path = os.path.join(dataset_dir, "synthetic_data_src.json")
        target_file_path = os.path.join(dataset_dir, "synthetic_data_target.json")

        if not os.path.exists(source_file_path):
            raise FileNotFoundError(
                f"Source dataset file not found: {source_file_path}. Please run the data generation notebook first."
            )

        if not os.path.exists(target_file_path):
            raise FileNotFoundError(
                f"Target dataset file not found: {target_file_path}. Please run the data generation notebook first."
            )

        with open(source_file_path, "r") as src_file:
            self.source_data: dict[str, list[dict]] = json.load(src_file)

        with open(target_file_path, "r") as target_file:
            self.target_data: dict[str, list[dict]] = json.load(target_file)

        if self.args.single_sample:
            first_machine_id = list(self.source_data.keys())[0]
            self.source_data = {
                first_machine_id: self.source_data[first_machine_id][0:1]
            }
            self.target_data = {
                first_machine_id: self.target_data[first_machine_id][0:1]
            }

    def __push_to_blockchain(self, machine_id: str, data: dict):
        tx = self.metric_caller.call_store_metrics(machine_id, data)
        self.metric_caller.wait_for_transaction(tx)

    def __run_direct_mapping(self):

        reference_machine_id = list(self.source_data.keys())[0]
        total_days = len(self.source_data[reference_machine_id])

        for day_index in range(total_days):
            current_date = None

            for machine_id in self.source_data.keys():
                machine_file_path = os.path.join(
                    self.run_dir, f"{machine_id}_result.jsonl"
                )

                source = self.source_data[machine_id][day_index]
                target = self.target_data[machine_id][day_index]
                result = {"source": source, "target": target}

                sample_time_start = time.time()

                mapping_result = self.llm_mapping(source)
                result["llm_mapping"] = mapping_result

                parsed = mapping_result.get("response_parsed", None)

                if current_date is None and "date" in source:
                    current_date = source["date"]

                if parsed is not None:
                    blockchain_time_start = time.time()
                    self.__push_to_blockchain(machine_id, parsed)
                    result["blockchain_time"] = time.time() - blockchain_time_start

                result["total_time"] = time.time() - sample_time_start

                with open(machine_file_path, "a") as f:
                    f.write(json.dumps(result) + "\n")

            if current_date is not None:
                print(f"Calling aggregate_metrics for {current_date}")
                self.metric_caller.call_aggregate_metrics(current_date)

    def __run_function_mapping(self):
        for machine_id in self.source_data.keys():
            sample_time_start = time.time()

            source = self.source_data[machine_id][0]
            target = self.target_data[machine_id][0]

            result = {"source": source, "target": target}
            result["llm_mapping"] = self.llm_mapping(source)

            result["total_time"] = time.time() - sample_time_start

            output_file_path = os.path.join(self.run_dir, f"{machine_id}_result.json")
            with open(output_file_path, "w") as f:
                json.dump(result, f, indent=4)

    def run(self):
        if self.args.prompt in ["few_shot", "schema_driven"]:
            self.__run_direct_mapping()
        else:
            self.__run_function_mapping()

    def evaluate(self):
        if self.args.prompt in ["few_shot", "schema_driven"]:
            evaluate_direct_mapping(self.run_dir)
        else:
            evaluate_mapping_function(self.run_dir)
