from enum import Enum

from pydantic import BaseModel, Field
from langchain.output_parsers import PydanticOutputParser


class TargetModelSimple(BaseModel):
    date: str = Field(description="Date of the observation. Format: YYYY-MM-DD")
    operation_hours: float = Field(
        description="Number of hours the machine was running on that day."
    )
    energy_consumption_kWh: float = Field(description="Energy consumption in kWh.")
    material_used_kg: float = Field(description="Amount of material used in kg.")
    material_waste_kg: float = Field(description="Amount of material waste in kg.")
    CO2_emissions_kg: float = Field(description="Amount of CO2 emissions in kg.")
    water_consumption_liters: float = Field(
        description="Amount of water consumed in liters."
    )
    water_recycled_liters: float = Field(
        description="Amount of water recycled in liters."
    )
    product_output_units: int = Field(
        description="Number of product units produced on that day."
    )


class LubricationLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class CoolingSystemStatus(str, Enum):
    OPERATIONAL = "operational"
    FAULTY = "faulty"
    OFF = "off"


class FuelType(str, Enum):
    ELECTRIC = "electric"
    DIESEL = "diesel"
    NATURAL_GAS = "natural_gas"
    HYBRID = "hybrid"


class TargetModel(TargetModelSimple):
    operating_temperature_C: float = Field(
        description="Operating temperature in Celsius."
    )
    ambient_humidity_percent: float = Field(description="Ambient humidity percentage.")
    vibration_level_mmps: float = Field(description="Vibration level in mm/s.")
    renewable_energy_percent: float = Field(
        description="Percentage of energy from renewable sources."
    )
    downtime_minutes: int = Field(description="Total downtime in minutes.")
    noise_level_dB: int = Field(description="Noise level in decibels.")
    worker_count: int = Field(description="Number of workers present.")
    lubrication_level: LubricationLevel = Field(
        description="Lubrication level of the machine."
    )
    cooling_system_status: CoolingSystemStatus = Field(
        description="Status of the cooling system."
    )
    maintenance_required: bool = Field(
        description="Whether maintenance is required or not."
    )
    fuel_type: FuelType = Field(description="Type of fuel used by the machine.")


OUTPUT_PARSERS = {
    "simple": PydanticOutputParser(pydantic_object=TargetModelSimple),
    "moderate": PydanticOutputParser(pydantic_object=TargetModel),
    "complex": PydanticOutputParser(pydantic_object=TargetModel),
}
