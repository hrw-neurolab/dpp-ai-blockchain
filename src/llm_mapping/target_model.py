from enum import Enum

from pydantic import BaseModel, Field, create_model
from langchain.output_parsers import PydanticOutputParser

from src.types import Difficulty


class TargetModelSimple(BaseModel):
    date: str = Field(
        description="Date of the observation. Format: YYYY-MM-DD", strict=True
    )
    operation_hours: float = Field(
        description="Number of hours the machine was running on that day.", strict=True
    )
    energy_consumption_kWh: float = Field(
        description="Energy consumption in kWh.", strict=True
    )
    material_used_kg: float = Field(
        description="Amount of material used in kg.", strict=True
    )
    material_waste_kg: float = Field(
        description="Amount of material waste in kg.", strict=True
    )
    CO2_emissions_kg: float = Field(
        description="Amount of CO2 emissions in kg.", strict=True
    )
    water_consumption_liters: float = Field(
        description="Amount of water consumed in liters.", strict=True
    )
    water_recycled_liters: float = Field(
        description="Amount of water recycled in liters.", strict=True
    )
    product_output_units: int = Field(
        description="Number of product units produced on that day.", strict=True
    )


class LubricationLevel(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


class CoolingSystemStatus(str, Enum):
    OPERATIONAL = "operational"
    FAULTY = "faulty"
    OFF = "off"


class FuelType(str, Enum):
    ELECTRIC = "electric"
    FOSSIL_FUEL = "fossil_fuel"
    RENEWABLE_FUEL = "renewable_fuel"
    HYBRID = "hybrid"


class TargetModel(TargetModelSimple):
    operating_temperature_C: float = Field(
        description="Operating temperature in Celsius.", strict=True
    )
    ambient_humidity_percent: float = Field(
        description="Ambient humidity percentage.", strict=True
    )
    vibration_level_mmps: float = Field(
        description="Vibration level in mm/s.", strict=True
    )
    renewable_energy_percent: float = Field(
        description="Percentage of energy from renewable sources.", strict=True
    )
    downtime_minutes: int = Field(description="Total downtime in minutes.", strict=True)
    noise_level_dB: int = Field(description="Noise level in decibels.", strict=True)
    worker_count: int = Field(description="Number of workers present.", strict=True)
    lubrication_level: LubricationLevel = Field(
        description="Lubrication level of the machine."
    )
    cooling_system_status: CoolingSystemStatus = Field(
        description="Status of the cooling system."
    )
    maintenance_required: bool = Field(
        description="Whether maintenance is required or not.", strict=True
    )
    fuel_type: FuelType = Field(description="Type of fuel used by the machine.")


OUTPUT_PARSERS: dict[Difficulty, PydanticOutputParser] = {
    "simple": PydanticOutputParser(pydantic_object=TargetModelSimple),
    "moderate": PydanticOutputParser(pydantic_object=TargetModel),
    "complex": PydanticOutputParser(pydantic_object=TargetModel),
}


def wrap_thinking_model(pydantic_model: type[BaseModel]) -> type[BaseModel]:
    """Wraps a Pydantic model with a thinking field."""
    return create_model("ThinkingResponse", thinking=str, response=pydantic_model)
