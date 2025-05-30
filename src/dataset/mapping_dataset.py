import os
import json

from loguru import logger

from src.dataset.preparation import generate_dataset
from src.types import Difficulty


class MappingDataset:
    def __init__(
        self,
        difficulty: Difficulty,
        cache_dir: str,
        num_samples: int | None = None,
    ):
        """Initializes the MappingDataset class.

        Args:
            difficulty (Difficulty): The difficulty level of the dataset.
            cache_dir (str): The directory where the dataset will be cached.
            num_samples (int, optional): The number of samples to use. Defaults to None.
        """
        logger.info("Initializing dataset...")

        self.difficulty = difficulty
        self.num_samples = num_samples

        self.dataset_path = os.path.join(cache_dir, difficulty)

        self.__load()
        self.machine_ids: list[str] = list(self.source.keys())
        self.__validate()

        if self.num_samples is not None:
            self.__apply_num_samples()

        self.__idx = 0

    def __load(self):
        src_file_path = os.path.join(self.dataset_path, "source.json")
        tgt_file_path = os.path.join(self.dataset_path, "target.json")

        exist = os.path.exists(src_file_path) and os.path.exists(tgt_file_path)

        if not exist:
            logger.info("Dataset files not found. Generating the dataset...")

            self.source, self.target = generate_dataset(self.difficulty)

            logger.info("Dataset generated successfully.")
            logger.info(f"Storing dataset files in {self.dataset_path} ...")

            os.makedirs(self.dataset_path, exist_ok=True)
            with open(src_file_path, "w") as src_file:
                json.dump(self.source, src_file, indent=4)
            with open(tgt_file_path, "w") as tgt_file:
                json.dump(self.target, tgt_file, indent=4)

        else:
            logger.info(f"Loading existing dataset files from {self.dataset_path} ...")

            with open(src_file_path, "r") as src_file:
                self.source = json.load(src_file)
            with open(tgt_file_path, "r") as tgt_file:
                self.target = json.load(tgt_file)

            logger.info("Dataset files loaded successfully.")

    def __validate(self):
        first_machine_id = self.machine_ids[0]
        samples_per_machine = len(self.source[first_machine_id])

        src = all(
            len(self.source[machine_id]) == samples_per_machine
            for machine_id in self.machine_ids
        )
        tgt = all(
            len(self.target[machine_id]) == samples_per_machine
            for machine_id in self.machine_ids
        )

        if not src or not tgt:
            raise ValueError(
                "The source and target datasets must have the same number of samples for each machine."
            )

    def __apply_num_samples(self):
        logger.warning(f"Limiting dataset to {self.num_samples} samples per machine...")

        for machine_id in self.source.keys():
            self.source[machine_id] = self.source[machine_id][: self.num_samples]
            self.target[machine_id] = self.target[machine_id][: self.num_samples]

    def __len__(self):
        return sum(len(self.source[machine_id]) for machine_id in self.machine_ids)

    def __iter__(self):
        return self

    def __next__(self) -> tuple[int, str, dict, dict]:
        if self.__idx >= len(self):
            raise StopIteration

        machine_id = self.machine_ids[self.__idx % len(self.machine_ids)]
        sample_idx = self.__idx // len(self.machine_ids)

        sample = (
            self.__idx,
            machine_id,
            self.source[machine_id][sample_idx],
            self.target[machine_id][sample_idx],
        )

        self.__idx += 1
        return sample

    def set_index(self, index: int):
        """Set the current index for iteration.

        Args:
            index (int): The index to set.
        """
        if index < 0 or index >= len(self):
            raise IndexError("Index out of range.")

        self.__idx = index

        logger.warning(f"Dataset index set to {self.__idx}.")

    def is_last_machine(self) -> bool:
        """Check if the current machine is the last one in the iteration.

        Returns:
            bool: True if the current machine is the last one, False otherwise.
        """
        return self.__idx % len(self.machine_ids) == 0
