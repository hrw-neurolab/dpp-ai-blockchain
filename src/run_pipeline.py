import time
import os
import json
from argparse import Namespace

from loguru import logger

from src.dataset.mapping_dataset import MappingDataset
from src.llm_mapping import LlmMapping
from src.blockchain.WavesConnector import MetricCaller
from src.evaluation import evaluate_direct_mapping, evaluate_mapping_function
from src.llm_mapping.function_refiner import FunctionRefiner
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

        num_samples = 1 if args.prompt == "mapping_function" else args.num_samples

        self.dataset = MappingDataset(args.difficulty, args.cache_dir, num_samples)
        self.llm_mapping = LlmMapping(
            args.model_provider,
            args.model_name,
            args.prompt,
            args.difficulty,
            args.cache_dir,
            args.ollama_host,
        )
        if (args.model_provider == "ollama" and args.prompt in ["few_shot", "schema_driven"]):
            max_try = getattr(args, "max_refinement_attempts", 3)
            self.llm_mapping = IterativeRefiner(self.llm_mapping, max_attempts=max_try)
        elif args.prompt == "mapping_function":
                max_try = getattr(args, "max_refinement_attempts", 3)
                self.llm_mapping = FunctionRefiner(self.llm_mapping, max_attempts=max_try)    
        
        self.metric_caller = MetricCaller()

        self.__save_config()
        self.__save_prompt()

    def __init_run_dir(self):
        """Initialize the run directory for saving results."""
        run_name_parts = [
            time.strftime("%Y-%m-%d_%H-%M-%S"),
            self.args.difficulty,
            self.args.prompt.replace("_", "-"),
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

    def __save_config(self):
        config_file_path = os.path.join(self.run_dir, "config.json")
        with open(config_file_path, "w") as f:
            json.dump(vars(self.args), f, indent=4)

    def __save_prompt(self):
        prompt_file_path = os.path.join(self.run_dir, "prompt.txt")
        with open(prompt_file_path, "w") as f:
            f.write(self.llm_mapping.prompt.invoke({}).to_string())

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

            mapping_result = self.llm_mapping(source)
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

            result["llm_mapping"] = self.llm_mapping(source)

            result["total_time"] = time.time() - sample_time_start

            file_path = os.path.join(self.raw_results_dir, f"{machine_id}.json")
            with open(file_path, "w") as f:
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
