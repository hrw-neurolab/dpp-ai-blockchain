import time
import os
import json
from argparse import Namespace

from loguru import logger

from llm_mapping import LlmMapping
from WavesConnector import MetricCaller
from study.evaluation import evaluate_direct_mapping, evaluate_mapping_function


class RunPipeline:
    @logger.catch(reraise=True)
    def __init__(self, args: Namespace):
        """Initialize the RunPipeline class.

        Args:
            args (Namespace): CLI arguments containing configuration options.
        """
        self.args = args
        self.__init_run_dir()
        self.__init_datasets()

        self.llm_mapping = LlmMapping(args.model_provider, args.model_name, args.prompt)
        self.metric_caller = MetricCaller()
        self.__save_config()
        self.__save_prompt()

    def __init_run_dir(self):
        """Initialize the run directory for saving results."""
        run_name = f"run_{self.args.prompt}_{time.strftime('%Y%m%d_%H%M%S')}"
        self.run_dir = os.path.join(self.args.output_dir, run_name)
        os.makedirs(self.run_dir, exist_ok=True)

        log_file_path = os.path.join(self.run_dir, "run.log")
        logger.add(
            log_file_path,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> "
            "| <level>{level: <8}</level> "
            "| <cyan>{file: <15}</cyan>:<cyan>{line: <3}</cyan> "
            "-> <level>{message}</level>",
        )
        logger.info(f"Run directory created: {self.run_dir}")

    def __save_config(self):
        config_file_path = os.path.join(self.run_dir, "config.json")
        with open(config_file_path, "w") as f:
            json.dump(vars(self.args), f, indent=4)

    def __save_prompt(self):
        prompt_file_path = os.path.join(self.run_dir, "prompt.txt")
        with open(prompt_file_path, "w") as f:
            f.write(self.llm_mapping.prompt.invoke({}).to_string())

    def __init_datasets(self):
        """Initialize the datasets for the run.

        Raises:
            FileNotFoundError: If the dataset files are not found.
        """
        logger.info("Loading datasets...")
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

        # Ensure the machines have the same number of samples
        first_machine_id = list(self.source_data.keys())[0]

        num_samples = len(self.source_data[first_machine_id])
        src = all(
            len(self.source_data[machine_id]) == num_samples
            for machine_id in self.source_data.keys()
        )
        tgt = all(
            len(self.target_data[machine_id]) == num_samples
            for machine_id in self.target_data.keys()
        )

        if not src or not tgt:
            raise ValueError(
                "The source and target datasets must have the same number of samples for each machine."
            )

        if self.args.single_sample:
            logger.info(
                "Running in single sample mode. Reducing datasets to one sample."
            )
            self.source_data = {
                first_machine_id: self.source_data[first_machine_id][0:1]
            }
            self.target_data = {
                first_machine_id: self.target_data[first_machine_id][0:1]
            }

    def __push_to_blockchain(self, machine_id: str, data: dict) -> tuple[str, int]:
        """Push the parsed data to the blockchain.

        Args:
            machine_id (str): The ID of the machine.
            data (dict): The parsed data to be pushed.

        Returns:
            tuple[str, int]: A tuple containing the transaction ID and height.
        """
        tx = self.metric_caller.call_store_metrics(machine_id, data)
        tx_info = self.metric_caller.wait_for_transaction(tx)

        return tx["id"], tx_info["height"]

    def __run_direct_mapping(self):
        """Run the mapping process for each machine and sample.

        This function directly maps the source data to the target format using either
        `few-shot` or `schema-driven` prompts. It also pushes the results to the blockchain
        and aggregates metrics.
        """
        reference_machine_id = list(self.source_data.keys())[0]
        total_samples = len(self.source_data[reference_machine_id])

        for sample_idx in range(total_samples):
            for machine_id in self.source_data.keys():
                prefix = f"[{sample_idx + 1:03}/{total_samples}: {machine_id}]"

                source = self.source_data[machine_id][sample_idx]
                target = self.target_data[machine_id][sample_idx]
                result = {"source": source, "target": target}

                logger.info(f"{prefix} Running LLM mapping")
                sample_time_start = time.time()

                mapping_result = self.llm_mapping(source)
                result["llm_mapping"] = mapping_result

                parsed = mapping_result.get("response_parsed", None)

                if parsed is not None:
                    logger.info(f"{prefix} Pushing to blockchain")
                    blockchain_time_start = time.time()

                    tx_id, block = self.__push_to_blockchain(machine_id, parsed)

                    result["blockchain_time"] = time.time() - blockchain_time_start
                    logger.info(f"{prefix} Transaction ID: {tx_id}")
                    logger.info(f"{prefix} Block height: {block}")

                result["total_time"] = time.time() - sample_time_start

                machine_file_path = os.path.join(
                    self.run_dir, f"{machine_id}_result.jsonl"
                )
                with open(machine_file_path, "a") as f:
                    f.write(json.dumps(result) + "\n")

            logger.info(f"Aggregating metrics for date: {target['date']}")
            self.metric_caller.call_aggregate_metrics(target["date"])

    def __run_function_mapping(self):
        """Run the mapping process once for each machine using the `mapping-function` prompt.

        This function generates a mapping function to transform the source data into
        the target format.
        """
        for machine_id in self.source_data.keys():
            logger.info(f"[{machine_id}] Generating mapping function")

            source = self.source_data[machine_id][0]
            target = self.target_data[machine_id][0]
            result = {"source": source, "target": target}

            sample_time_start = time.time()

            result["llm_mapping"] = self.llm_mapping(source)

            result["total_time"] = time.time() - sample_time_start

            machine_file_path = os.path.join(self.run_dir, f"{machine_id}_result.json")
            with open(machine_file_path, "w") as f:
                json.dump(result, f, indent=4)

    @logger.catch(reraise=True)
    def run(self):
        """Run the pipeline based on the specified prompt type."""
        logger.info("Starting pipeline")

        if self.args.prompt in ["few_shot", "schema_driven"]:
            self.__run_direct_mapping()
        else:
            self.__run_function_mapping()

    @logger.catch(reraise=True)
    def evaluate(self):
        """Evaluate the results based on the specified prompt type."""
        logger.info("Starting evaluation")

        if self.args.prompt in ["few_shot", "schema_driven"]:
            evaluate_direct_mapping(self.run_dir)
        else:
            evaluate_mapping_function(self.run_dir)
