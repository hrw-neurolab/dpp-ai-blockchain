import random
from typing import Literal
from datetime import datetime, timedelta

import numpy as np

from src.dataset.preparation import (
    PERTURBATION_FUNCTIONS_SIMPLE,
    PERTURBATION_FUNCTIONS_MODERATE,
    PERTURBATION_FUNCTIONS_COMPLEX,
)


BASE_TARGET_SIMPLE = {
    # float values
    "operation_hours": lambda: round(np.random.uniform(7, 10), 2),
    "energy_consumption_kWh": lambda: round(np.random.uniform(300, 500), 2),
    "material_used_kg": lambda: round(np.random.uniform(400, 700), 2),
    "material_waste_kg": lambda: round(np.random.uniform(30, 50), 2),
    "CO2_emissions_kg": lambda: round(np.random.uniform(200, 400), 2),
    "water_consumption_liters": lambda: round(np.random.uniform(800, 1200), 2),
    "water_recycled_liters": lambda: round(np.random.uniform(400, 800), 2),
    # integer values
    "product_output_units": lambda: round(np.random.uniform(200, 400)),
}

BASE_TARGET = {
    **BASE_TARGET_SIMPLE,
    # float values
    "operating_temperature_C": lambda: round(np.random.uniform(70, 80), 2),
    "ambient_humidity_percent": lambda: round(np.random.uniform(45, 55), 2),
    "vibration_level_mmps": lambda: round(np.random.uniform(1, 3), 2),
    "renewable_energy_percent": lambda: round(np.random.uniform(40, 60), 2),
    # integer values
    "downtime_minutes": lambda: round(np.random.uniform(5, 40)),
    "noise_level_dB": lambda: round(np.random.uniform(70, 90)),
    "worker_count": lambda: round(np.random.uniform(1, 4)),
    # categorical values
    "lubrication_level": lambda: random.choice(["low", "medium", "high"]),
    "cooling_system_status": lambda: random.choice(["operational", "faulty", "off"]),
    "maintenance_required": lambda: random.choice([True, False]),
    "fuel_type": lambda: random.choice(
        ["electric", "fossil_fuel", "renewable_fuel", "hybrid"]
    ),
}


PERTURBATION_FUNCTIONS = {
    "simple": PERTURBATION_FUNCTIONS_SIMPLE,
    "moderate": PERTURBATION_FUNCTIONS_MODERATE,
    "complex": PERTURBATION_FUNCTIONS_COMPLEX,
}


def generate_target_sample(
    date: datetime, difficulty: Literal["simple", "moderate", "complex"]
) -> dict:
    """Generates a target sample for a given date.

    Args:
        date (datetime): The date for which to generate the sample.
        difficulty (Literal["simple", "moderate", "complex"]): The difficulty level of the sample.

    Returns:
        dict: A dictionary containing the generated sample.
    """
    base_target = BASE_TARGET_SIMPLE if difficulty == "simple" else BASE_TARGET

    return {
        "date": date.strftime("%Y-%m-%d"),
        **{key: base_target[key]() for key in base_target.keys()},
    }


def all_days_in_year_datetime(year: int):
    """Generates all days in a given year as datetime objects.

    Args:
        year (int): The year for which to generate the dates.

    Yields:
        datetime: A datetime object representing each day in the year.
    """
    start_date = datetime(year, 1, 1)
    end_date = datetime(year + 1, 1, 1)
    delta = timedelta(days=1)

    current_date = start_date
    while current_date < end_date:
        yield current_date
        current_date += delta


def generate_dataset(
    difficulty: Literal["simple", "moderate", "complex"],
) -> tuple[dict, dict]:
    """Generates a dataset of target and source samples.

    Args:
        difficulty (Literal["simple", "moderate", "complex"]): The difficulty level of the dataset.

    Returns:
        tuple: A tuple containing the source and target datasets.
    """
    np.random.seed(42)
    random.seed(42)

    target_dataset = {}
    source_dataset = {}

    pf = PERTURBATION_FUNCTIONS[difficulty]

    for machine_index in range(10):
        machine_id = f"M{machine_index + 1:03}"
        target_dataset[machine_id] = []
        source_dataset[machine_id] = []

        for day in all_days_in_year_datetime(2024):
            target_sample = generate_target_sample(day, difficulty)
            target_dataset[machine_id].append(target_sample)

            source_sample = pf[machine_index](target_sample)
            source_dataset[machine_id].append(source_sample)

    return source_dataset, target_dataset


def generate_few_shot_examples(
    difficulty: Literal["simple", "moderate", "complex"],
) -> list[dict]:
    """Generates 5 few-shot examples for the dataset.

    Args:
        difficulty (Literal["simple", "moderate", "complex"]): The difficulty level of the dataset.

    Returns:
        list: A list of dictionaries containing the few-shot examples.
    """
    np.random.seed(50)
    random.seed(50)

    few_shot_examples = []
    pf = PERTURBATION_FUNCTIONS[difficulty]

    for machine_index in [0, 3, 6, 9]:
        target_sample = generate_target_sample(datetime(2024, 1, 1), difficulty)
        source_sample = pf[machine_index](target_sample)

        few_shot_examples.append(
            {
                "input": source_sample,
                "output": target_sample,
            }
        )

    return few_shot_examples
