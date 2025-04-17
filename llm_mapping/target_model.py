from pydantic import BaseModel, Field
from langchain.output_parsers import PydanticOutputParser


class TargetModel(BaseModel):
    date: str = Field(description="Date of the observation. Format: YYYY-MM-DD")
    operation_hours: int = Field(
        description="Number of hours the machine was running on that day."
    )
    energy_consumption_kWh: int = Field(
        description="Energy consumption in kWh for that day."
    )
    material_used_kg: int = Field(
        description="Amount of material used in kg for that day."
    )
    material_waste_kg: int = Field(
        description="Amount of material waste in kg for that day."
    )
    CO2_emissions_kg: int = Field(
        description="Amount of CO2 emissions in kg for that day."
    )
    water_consumption_liters: int = Field(
        description="Amount of water consumed in liters for that day."
    )
    water_recycled_liters: int = Field(
        description="Amount of water recycled in liters for that day."
    )
    product_output_units: int = Field(
        description="Number of product units produced on that day."
    )


OUTPUT_PARSER = PydanticOutputParser(pydantic_object=TargetModel)
