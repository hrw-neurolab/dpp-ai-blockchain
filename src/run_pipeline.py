import time
import os
import json
from argparse import Namespace

from loguru import logger

from src.dataset.mapping_dataset import MappingDataset
from src.llm_mapping import LlmMapping
from src.blockchain.WavesConnector import MetricCaller
from src.evaluation import evaluate_direct_mapping, evaluate_mapping_function
from src.llm_mapping.iterative_refiner import IterativeRefiner


class RunPipeline:
    @logger.catch(reraise=True)
    def __init__(self, args: Namespace):
        """Initialize the RunPipeline class.

        Args:
            args (Namespace): CLI arguments containing configuration options.
        """
        self.args = args
        self.__init_run_dir()

        num_samples = 1 if args.prompt == "mapping-function" else args.num_samples

        self.dataset = MappingDataset(args.difficulty, args.cache_dir, num_samples)
        self.__init_llm_mapping()

        self.metric_caller = MetricCaller()

        self.__save_config()
        self.__save_prompt()

    def __init_run_dir(self):
        """Initialize the run directory for saving results."""
        run_name_parts = [
            time.strftime("%Y-%m-%d_%H-%M-%S"),
            self.args.difficulty,
            self.args.prompt,
        ]
        run_name = "_".join(run_name_parts)

        model_name = self.args.model_name.replace("/", "-").replace(":", "-")

        self.run_dir = os.path.join(self.args.output_dir, model_name, run_name)
        os.makedirs(self.run_dir, exist_ok=True)

        self.raw_results_dir = os.path.join(self.run_dir, "raw_results")
        os.makedirs(self.raw_results_dir, exist_ok=True)

        log_file_path = os.path.join(self.run_dir, "run.log")
        logger.add(
            log_file_path,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> "
            "| <level>{level: <8}</level> "
            "| <cyan>{file: <15}</cyan>:<cyan>{line: <3}</cyan> "
            "-> <level>{message}</level>",
        )
        logger.info(f"Run directory created: {self.run_dir}")

    def __init_llm_mapping(self):
        """Initialize the LLM mapping based on the specified model provider and prompt type."""
        self.llm_mapping = LlmMapping(
            self.args.model_provider,
            self.args.model_name,
            self.args.prompt,
            self.args.include_schema,
            self.args.difficulty,
            self.args.cache_dir,
            self.args.ollama_host,
            self.args.structured_output,
        )

        max_attempts = self.args.max_refinement_attempts

        if max_attempts <= 0:
            return

        if self.args.model_provider != "ollama":
            raise ValueError("Iterative refinement is intended for Ollama models only.")

        self.llm_mapping = IterativeRefiner(self.llm_mapping, max_attempts)
        logger.info(f"Refinement attempts set to {max_attempts}.")

    def __save_config(self):
        config_file_path = os.path.join(self.run_dir, "config.json")
        with open(config_file_path, "w") as f:
            json.dump(vars(self.args), f, indent=4)

    def __save_prompt(self):
        formatted_prompt = self.llm_mapping.prompt.format(
            input_json="{input_json}",
            correction_msg="{correction_msg}",
        )

        prompt_file_path = os.path.join(self.run_dir, "prompt.txt")
        with open(prompt_file_path, "w") as f:
            f.write(formatted_prompt)

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
        total_samples = len(self.dataset)

        for index, (machine_id, source, target) in enumerate(self.dataset):
            prefix = f"[{index + 1:03}/{total_samples}: {machine_id}]"

            result = {"source": source, "target": target}

            logger.info(f"{prefix} Running LLM mapping")
            sample_time_start = time.time()

            template_vars = {"input_json": json.dumps(source)}
            mapping_result = self.llm_mapping(template_vars, source)
            result["llm_mapping"] = mapping_result

            parsed = mapping_result.get("response_parsed", None)

            if parsed is not None and self.args.blockchain:
                logger.info(f"{prefix} Pushing to blockchain")
                blockchain_time_start = time.time()

                tx_id, block = self.__push_to_blockchain(machine_id, parsed)

                result["blockchain_time"] = time.time() - blockchain_time_start
                logger.info(f"{prefix} Transaction ID: {tx_id}")
                logger.info(f"{prefix} Block height: {block}")

            result["total_time"] = time.time() - sample_time_start

            file_path = os.path.join(self.raw_results_dir, f"{machine_id}.jsonl")
            with open(file_path, "a") as f:
                f.write(json.dumps(result) + "\n")

        if self.args.blockchain:
            logger.info(f"Aggregating metrics for date: {target['date']}")
            self.metric_caller.call_aggregate_metrics(target["date"])

    def __run_function_mapping(self):
        """Run the mapping process once for each machine using the `mapping-function` prompt.

        This function generates a mapping function to transform the source data into
        the target format.
        """
        total_samples = len(self.dataset)

        for index, (machine_id, source, target) in enumerate(self.dataset):
            logger.info(
                f"[{index + 1:03}/{total_samples}: {machine_id}] Generating mapping function"
            )

            result = {"source": source, "target": target}

            sample_time_start = time.time()

            template_vars = {"input_json": json.dumps(source)}
            result["llm_mapping"] = self.llm_mapping(template_vars, source)

            result["total_time"] = time.time() - sample_time_start

            file_path = os.path.join(self.raw_results_dir, f"{machine_id}.json")
            with open(file_path, "w") as f:
                json.dump(result, f, indent=4)

    @logger.catch(reraise=True)
    def run(self):
        """Run the pipeline based on the specified prompt type."""
        logger.info("Starting pipeline")

        if self.args.prompt == "mapping-function":
            self.__run_function_mapping()
        else:
            self.__run_direct_mapping()

    @logger.catch(reraise=True)
    def evaluate(self):
        """Evaluate the results based on the specified prompt type."""
        logger.info("Starting evaluation")

        if self.args.prompt == "mapping-function":
            evaluate_mapping_function(self.run_dir)
        else:
            evaluate_direct_mapping(self.run_dir)
