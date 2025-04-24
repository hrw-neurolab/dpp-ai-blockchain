from src.dataset.preparation.util import convert_units_simple


def machine_01(target: dict) -> dict:
    """
    ### Machine 01 - Different Key | Correct Unit | Unit in Key
    """
    return {
        "CurrentDate": target["date"],
        "UptimeHours": target["operation_hours"],
        "PowerKWh": target["energy_consumption_kWh"],
        "SubstanceUsedKg": target["material_used_kg"],
        "SubstanceWasteKg": target["material_waste_kg"],
        "CarbonDioxideKg": target["CO2_emissions_kg"],
        "WaterUsageLiters": target["water_consumption_liters"],
        "WaterReclaimedLiters": target["water_recycled_liters"],
        "YieldUnits": target["product_output_units"],
    }


def machine_02(target: dict) -> dict:
    """
    ### Machine 02 - Different Key | Different Unit | Unit in Key
    """
    target = convert_units_simple(target)
    return {
        "CurrentDateIso": target["date"],
        "UptimeSeconds": target["operation_hours"],
        "PowerMWh": target["energy_consumption_kWh"],
        "SubstanceUsedGrams": target["material_used_kg"],
        "SubstanceWasteMilligrams": target["material_waste_kg"],
        "CarbonDioxideTonnes": target["CO2_emissions_kg"],
        "WaterUsageMilliliters": target["water_consumption_liters"],
        "WaterReclaimedMilliliters": target["water_recycled_liters"],
        "YieldUnitsThousands": target["product_output_units"],
    }


def machine_03(target: dict) -> dict:
    """
    ### Machine 03 - Different Key | Correct Unit | Unit in Value
    """
    return {
        "CurrentDate": target["date"],
        "Uptime": f"{target["operation_hours"]} h",
        "Power": f"{target["energy_consumption_kWh"]} kWh",
        "SubstanceUsed": f"{target["material_used_kg"]} kg",
        "SubstanceWaste": f"{target["material_waste_kg"]} kg",
        "CarbonDioxide": f"{target["CO2_emissions_kg"]} kg",
        "WaterUsage": f"{target["water_consumption_liters"]} L",
        "WaterReclaimed": f"{target["water_recycled_liters"]} L",
        "Yield": f"{target["product_output_units"]} units",
    }


def machine_04(target: dict) -> dict:
    """
    ### Machine 04 - Different Key | Different Unit | Unit in Value
    """
    target = convert_units_simple(target)
    return {
        "CurrentDate": target["date"],
        "Uptime": f"{target["operation_hours"]} s",
        "Power": f"{target["energy_consumption_kWh"]} MWh",
        "SubstanceUsed": f"{target["material_used_kg"]} g",
        "SubstanceWaste": f"{target["material_waste_kg"]} mg",
        "CarbonDioxide": f"{target["CO2_emissions_kg"]} t",
        "WaterUsage": f"{target["water_consumption_liters"]} mL",
        "WaterReclaimed": f"{target["water_recycled_liters"]} mL",
        "Yield": f"{target["product_output_units"]} k units",
    }


def machine_05(target: dict) -> dict:
    """
    ### Machine 05 - Same Key | Different Unit | Unit in Key
    """
    target = convert_units_simple(target)
    return {
        "data_iso": target["date"],
        "operation_seconds": target["operation_hours"],
        "energy_consumption_MWh": target["energy_consumption_kWh"],
        "material_used_g": target["material_used_kg"],
        "material_waste_mg": target["material_waste_kg"],
        "CO2_emissions_t": target["CO2_emissions_kg"],
        "water_consumption_mL": target["water_consumption_liters"],
        "water_recycled_mL": target["water_recycled_liters"],
        "product_output_k_units": target["product_output_units"],
    }


def machine_06(target: dict) -> dict:
    """
    ### Machine 06 - Same Key | Different Unit | Unit in Value
    """
    target = convert_units_simple(target)
    return {
        "date": target["date"],
        "operation": f"{target["operation_hours"]} s",
        "energy_consumption": f"{target["energy_consumption_kWh"]} MWh",
        "material_used": f"{target["material_used_kg"]} g",
        "material_waste": f"{target["material_waste_kg"]} mg",
        "CO2_emissions": f"{target["CO2_emissions_kg"]} t",
        "water_consumption": f"{target["water_consumption_liters"]} mL",
        "water_recycled": f"{target["water_recycled_liters"]} mL",
        "product_output": f"{target["product_output_units"]} k units",
    }


def machine_07(target: dict) -> dict:
    """
    ### Machine 07 - Same Key | Correct Unit | Unit in Value
    """
    return {
        "date": target["date"],
        "operation": f"{target["operation_hours"]} h",
        "energy_consumption": f"{target["energy_consumption_kWh"]} kWh",
        "material_used": f"{target["material_used_kg"]} kg",
        "material_waste": f"{target["material_waste_kg"]} kg",
        "CO2_emissions": f"{target["CO2_emissions_kg"]} kg",
        "water_consumption": f"{target["water_consumption_liters"]} L",
        "water_recycled": f"{target["water_recycled_liters"]} L",
        "product_output": f"{target["product_output_units"]} units",
    }


def machine_08(target: dict) -> dict:
    """
    ### Machine 08 - Same Key | Correct Unit | Unit in Key (IDENTITY MAPPING)
    """
    return {**target}


def machine_09(target: dict) -> dict:
    """
    ### Machine 09 - Same Key | Nested Value and Unit (different unit)
    """
    target = convert_units_simple(target)
    return {
        "date": {
            "value": target["date"],
            "unit": "iso",
        },
        "operation": {
            "value": target["operation_hours"],
            "unit": "s",
        },
        "energy_consumption": {
            "value": target["energy_consumption_kWh"],
            "unit": "MWh",
        },
        "material_used": {
            "value": target["material_used_kg"],
            "unit": "g",
        },
        "material_waste": {
            "value": target["material_waste_kg"],
            "unit": "mg",
        },
        "CO2_emissions": {
            "value": target["CO2_emissions_kg"],
            "unit": "t",
        },
        "water_consumption": {
            "value": target["water_consumption_liters"],
            "unit": "mL",
        },
        "water_recycled": {
            "value": target["water_recycled_liters"],
            "unit": "mL",
        },
        "product_output": {
            "value": target["product_output_units"],
            "unit": "k units",
        },
    }


def machine_10(target: dict) -> dict:
    """
    ### Machine 10 - Same Key | Nested Value and Unit (correct unit)
    """
    return {
        "date": {
            "value": target["date"],
            "unit": "yyyy-mm-dd",
        },
        "operation": {
            "value": target["operation_hours"],
            "unit": "h",
        },
        "energy_consumption": {
            "value": target["energy_consumption_kWh"],
            "unit": "kWh",
        },
        "material_used": {
            "value": target["material_used_kg"],
            "unit": "kg",
        },
        "material_waste": {
            "value": target["material_waste_kg"],
            "unit": "kg",
        },
        "CO2_emissions": {
            "value": target["CO2_emissions_kg"],
            "unit": "kg",
        },
        "water_consumption": {
            "value": target["water_consumption_liters"],
            "unit": "L",
        },
        "water_recycled": {
            "value": target["water_recycled_liters"],
            "unit": "L",
        },
        "product_output": {
            "value": target["product_output_units"],
            "unit": "units",
        },
    }


PERTURBATION_FUNCTIONS = [
    machine_01,
    machine_02,
    machine_03,
    machine_04,
    machine_05,
    machine_06,
    machine_07,
    machine_08,
    machine_09,
    machine_10,
]
