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
    def __init__(self, args: Namespace, is_continue: bool = False):
        """Initialize the RunPipeline class.

        Args:
            args (Namespace): CLI arguments containing configuration options.
            is_continue (bool): Only used when continuing from a previous run.
        """
        self.args = args
        self.metric_caller = MetricCaller()

        if is_continue:
            return

        self.__init_run_dir()
        self.__init_dataset()
        self.__init_llm_mapping()

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

    def __init_dataset(self):
        """Initialize the dataset based on the specified difficulty level and last index."""
        num_samples = (
            1 if self.args.prompt == "mapping-function" else self.args.num_samples
        )
        self.dataset = MappingDataset(
            self.args.difficulty, self.args.cache_dir, num_samples
        )

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
            self.args.wrap_thinking,
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

    def __save_last_index(self, index: int):
        """Save the last dataset index to a file.

        Args:
            index (int): The index to be saved (zero-indexed).
        """
        index_file_path = os.path.join(self.run_dir, "last_index.txt")
        with open(index_file_path, "w") as f:
            f.write(str(index))

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

        for index, machine_id, source, target in self.dataset:
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

            self.__save_last_index(index)

            if self.args.blockchain and self.dataset.is_last_machine():
                logger.info(f"Aggregating metrics for date: {target['date']}")
                self.metric_caller.call_aggregate_metrics(target["date"])

    def __run_function_mapping(self):
        """Run the mapping process once for each machine using the `mapping-function` prompt.

        This function generates a mapping function to transform the source data into
        the target format.
        """
        total_samples = len(self.dataset)

        for index, machine_id, source, target in self.dataset:
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

            self.__save_last_index(index)

    @classmethod
    def from_run_dir(cls, run_dir: str):
        """Create an instance of RunPipeline from a given run directory.

        Args:
            run_dir (str): The path to the run directory.

        Returns:
            RunPipeline: An instance of the RunPipeline class.
        """
        if not os.path.exists(run_dir):
            raise ValueError(f"Path `{run_dir}` does not exist.")

        # Load the configuration
        config_file_path = os.path.join(run_dir, "config.json")
        with open(config_file_path, "r") as f:
            args = json.load(f)
        args = Namespace(**args)
        run_pipeline = cls(args, True)

        # Set the dirs and add the logger
        run_pipeline.run_dir = run_dir
        run_pipeline.raw_results_dir = os.path.join(run_dir, "raw_results")

        log_file_path = os.path.join(run_dir, "run.log")
        logger.add(
            log_file_path,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> "
            "| <level>{level: <8}</level> "
            "| <cyan>{file: <15}</cyan>:<cyan>{line: <3}</cyan> "
            "-> <level>{message}</level>",
        )

        # Init the dataset and load the last index + 1
        run_pipeline.__init_dataset()
        last_index_file_path = os.path.join(run_dir, "last_index.txt")
        if not os.path.exists(last_index_file_path):
            raise FileNotFoundError(f"Path {run_dir} does not contain last_index.txt.")

        with open(last_index_file_path, "r") as f:
            last_index = int(f.read().strip())
        run_pipeline.dataset.set_index(last_index + 1)

        # Init the llm mapping
        run_pipeline.__init_llm_mapping()
        logger.info(f"Successfully loaded run pipeline from {run_dir}")
        logger.info(f"Resuming from index: {last_index + 1}")

        return run_pipeline

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
