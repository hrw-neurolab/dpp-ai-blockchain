from datetime import datetime, timedelta
import random


def machine_01(target: dict) -> dict:
    """
    ### Machine 01 - Inconsistent Casing & Field Variants

    Field names use inconsistent casing, delimiter styles, and synonym keys.
    """
    return {
        "CurrentDate": target["date"],
        "Operation_Hours": target["operation_hours"],
        "Power_kwh": target["energy_consumption_kWh"],
        "MaterialUsedKG": target["material_used_kg"],
        "MaterialWaste_kg": target["material_waste_kg"],
        "CO2KG": target["CO2_emissions_kg"],
        "Water-Usage": target["water_consumption_liters"],
        "WaterReclaimed": target["water_recycled_liters"],
        "TEMP_C": target["operating_temperature_C"],
        "HumidityPercent": target["ambient_humidity_percent"],
        "VibrationLevel": target["vibration_level_mmps"],
        "RenewEnergy%": target["renewable_energy_percent"],
        "Yield": target["product_output_units"],
        "Downtime_mins": target["downtime_minutes"],
        "NoiseDB": target["noise_level_dB"],
        "Workers": target["worker_count"],
        "LubeLevel": target["lubrication_level"],
        "CoolingStatus": target["cooling_system_status"],
        "NeedsMaint": target["maintenance_required"],
        "FuelType": target["fuel_type"],
    }


def machine_02(target: dict) -> dict:
    """
    ### Machine 02 - Deeply Nested Structures

    Data is deeply nested within categorized sections like
    "metrics", "environment", "production", and "settings".
    """
    return {
        "date_info": {"reported_on": target["date"]},
        "metrics": {
            "operation": {
                "hours": target["operation_hours"],
                "downtime": target["downtime_minutes"],
            },
            "energy": {
                "consumption": {"kwh": target["energy_consumption_kWh"]},
                "renewable_ratio": target["renewable_energy_percent"],
            },
            "material": {
                "used": target["material_used_kg"],
                "waste": target["material_waste_kg"],
            },
            "environmental": {
                "CO2": {"emitted": target["CO2_emissions_kg"]},
                "water": {
                    "used_liters": target["water_consumption_liters"],
                    "recycled_liters": target["water_recycled_liters"],
                },
                "noise_dB": target["noise_level_dB"],
                "humidity": target["ambient_humidity_percent"],
            },
            "vibration": {"level_mmps": target["vibration_level_mmps"]},
        },
        "production": {"output_units": target["product_output_units"]},
        "settings": {
            "temperature_C": target["operating_temperature_C"],
            "lubrication": target["lubrication_level"],
            "cooling_status": target["cooling_system_status"],
            "fuel": {"type": target["fuel_type"]},
        },
        "maintenance": {
            "required": target["maintenance_required"],
            "workers_on_shift": target["worker_count"],
        },
    }


def machine_03(target: dict) -> dict:
    """
    ### Machine 03 - Units Embedded in Strings

    Numeric values are stored as strings with unit suffixes (e.g., "367.96 kWh").
    """
    return {
        "date": target["date"],
        "operation_hours": f"{target['operation_hours']} hrs",
        "energy": f"{round(target['energy_consumption_kWh'] / 1000, 5)} MWh",
        "material_used": f"{target['material_used_kg']} kg",
        "material_waste": f"{target['material_waste_kg']} kg",
        "CO2_emitted": f"{target['CO2_emissions_kg']} kg",
        "water_used": f"{target["water_consumption_liters"] * 1000} mL",
        "water_recycled": f"{target["water_recycled_liters"] * 1000} mL",
        "temperature": f"{target['operating_temperature_C']} Celsius",
        "humidity": f"{target['ambient_humidity_percent']}%",
        "vibration": f"{target['vibration_level_mmps']} mm/s",
        "renewables": f"{target['renewable_energy_percent']}%",
        "output": f"{target['product_output_units']} units",
        "downtime": f"{target['downtime_minutes']} minutes",
        "noise": f"{target['noise_level_dB']} dB",
        "workers": f"{target['worker_count']} persons",
        "lubrication": f"{target['lubrication_level']} level",
        "cooling": f"{target['cooling_system_status']} mode",
        "maintenance": "yes" if target["maintenance_required"] else "no",
        "fuel": f"{target['fuel_type']} power",
    }


def machine_04(target: dict) -> dict:
    """
    ### Machine 04 - Multilingual Field Names

    Field names are in multiple languages, including Spanish, French, and German.
    """
    return {
        "datum": datetime.strptime(target["date"], "%Y-%m-%d").strftime("%d.%m.%Y"),
        "horas_operativas": target["operation_hours"],
        "consumo_energía_kWh": target["energy_consumption_kWh"],
        "matériel_utilisé_kg": target["material_used_kg"],
        "matériau_déchet_kg": target["material_waste_kg"],
        "émissions_CO2_kg": target["CO2_emissions_kg"],
        "utilisation_eau_litres": target["water_consumption_liters"],
        "eau_recyclée_litres": target["water_recycled_liters"],
        "température_fonctionnement_C": target["operating_temperature_C"],
        "humidité_ambiante_%": target["ambient_humidity_percent"],
        "niveau_de_vibration_mmps": target["vibration_level_mmps"],
        "énergie_renouvelable_%": target["renewable_energy_percent"],
        "unidades_producidas": target["product_output_units"],
        "minutos_inactivos": target["downtime_minutes"],
        "laermpegel_dB": target["noise_level_dB"],
        "nombre_trabajadores": target["worker_count"],
        "niveau_lubrification": target["lubrication_level"],
        "état_du_refroidissement": target["cooling_system_status"],
        "wartung_erforderlich": target["maintenance_required"],
        "carburant": target["fuel_type"],
    }


def machine_05(target: dict) -> dict:
    """
    ### Machine 05 - Tabular Format with Units

    Data is presented in a tabular format with units specified in a separate column.
    """
    return {
        "data": [
            ["field", "value", "unit"],
            ["date", target["date"], "YYYY-MM-DD"],
            ["operation_hours", target["operation_hours"], "hours"],
            ["energy_consumption", target["energy_consumption_kWh"], "kWh"],
            ["material_used", target["material_used_kg"], "kg"],
            ["material_waste", target["material_waste_kg"], "kg"],
            ["CO2_emissions", target["CO2_emissions_kg"], "kg"],
            ["water_consumption", target["water_consumption_liters"], "liters"],
            ["water_recycled", target["water_recycled_liters"], "liters"],
            ["temperature", target["operating_temperature_C"], "Celsius"],
            ["humidity", target["ambient_humidity_percent"], "%"],
            ["vibration", target["vibration_level_mmps"], "mm/s"],
            ["renewable_energy", target["renewable_energy_percent"], "%"],
            ["output_units", target["product_output_units"], "units"],
            ["downtime", target["downtime_minutes"], "minutes"],
            ["noise_level", target["noise_level_dB"], "dB"],
            ["workers", target["worker_count"], "count"],
            ["lubrication_level", target["lubrication_level"], "level"],
            ["cooling_status", target["cooling_system_status"], "status"],
            ["maintenance_required", str(target["maintenance_required"]), "boolean"],
            ["fuel_type", target["fuel_type"], "type"],
        ]
    }


def machine_06(target: dict) -> dict:
    """
    ### Machine 06 - JSON Log Format

    Data is structured as a JSON log with timestamps and event types.
    """
    base_time = datetime.strptime(target["date"], "%Y-%m-%d")

    def make_event(event_type, value, unit=None):
        timestamp = (base_time + timedelta(minutes=random.randint(0, 1439))).isoformat()
        return {
            "timestamp": timestamp,
            "event_type": event_type,
            "value": value if unit is None else f"{value} {unit}",
        }

    return {
        "log": [
            make_event("operation_hours", target["operation_hours"], "h"),
            make_event("energy_consumption", target["energy_consumption_kWh"], "kWh"),
            make_event("material_used", target["material_used_kg"], "kg"),
            make_event("material_waste", target["material_waste_kg"], "kg"),
            make_event("CO2_emissions", target["CO2_emissions_kg"], "kg"),
            make_event("water_used", target["water_consumption_liters"], "L"),
            make_event("water_recycled", target["water_recycled_liters"], "L"),
            make_event("temperature", target["operating_temperature_C"], "C"),
            make_event("humidity", target["ambient_humidity_percent"], "%"),
            make_event("vibration", target["vibration_level_mmps"], "mm/s"),
            make_event(
                "renewable_energy_percent", target["renewable_energy_percent"], "%"
            ),
            make_event("product_output_units", target["product_output_units"]),
            make_event("downtime_minutes", target["downtime_minutes"], "min"),
            make_event("noise_level", target["noise_level_dB"], "dB"),
            make_event("worker_count", target["worker_count"]),
            make_event("lubrication_status", target["lubrication_level"]),
            make_event("cooling_status", target["cooling_system_status"]),
            make_event(
                "maintenance_status",
                "required" if target["maintenance_required"] else "not_required",
            ),
            make_event("fuel", target["fuel_type"]),
        ]
    }


def machine_07(target: dict) -> dict:
    """
    ### Machine 07 - Log File

    Data is structured as a log file with timestamps and additional metadata.
    """
    base_time = datetime.strptime(target["date"], "%Y-%m-%d")

    def log_line(event, value, unit=None):
        timestamp = (base_time + timedelta(minutes=random.randint(0, 1439))).isoformat()
        msg = f"{event}: {value}{(' ' + unit) if unit else ''}"
        return f"[{timestamp}] IP=192.168.10.77 Facility=Plant-A Floor=2 Section=23/C :: {msg}"

    log_entries = [
        log_line("operation_hours", target["operation_hours"], "h"),
        log_line("energy_consumption", target["energy_consumption_kWh"], "kWh"),
        log_line("material_used", target["material_used_kg"], "kg"),
        log_line("material_waste", target["material_waste_kg"], "kg"),
        log_line("CO2_emissions", target["CO2_emissions_kg"], "kg"),
        log_line("water_consumed", target["water_consumption_liters"], "L"),
        log_line("water_recycled", target["water_recycled_liters"], "L"),
        log_line("temperature", target["operating_temperature_C"], "C"),
        log_line("humidity", target["ambient_humidity_percent"], "%"),
        log_line("vibration", target["vibration_level_mmps"], "mm/s"),
        log_line("renewable_energy", target["renewable_energy_percent"], "%"),
        log_line("product_output", target["product_output_units"], "units"),
        log_line("downtime", target["downtime_minutes"], "min"),
        log_line("noise_level", target["noise_level_dB"], "dB"),
        log_line("worker_count", target["worker_count"]),
        log_line("lubrication_status", target["lubrication_level"]),
        log_line("cooling_status", target["cooling_system_status"]),
        log_line(
            "maintenance_required", "yes" if target["maintenance_required"] else "no"
        ),
        log_line("fuel_type", target["fuel_type"]),
    ]

    return {"machine_log": "\n".join(sorted(log_entries))}


def machine_08(target: dict) -> dict:
    """
    ### Machine 08 - Embedded CSV in JSON

    The machine reports its data as a single CSV string embedded inside a JSON field.
    The CSV includes headers and a single row of values.
    Column order is non-standardized, and all values are quoted strings.
    """
    fields = [
        ("date", target["date"]),
        ("operation_hours", target["operation_hours"]),
        ("energy_kWh", target["energy_consumption_kWh"]),
        ("material_used_kg", target["material_used_kg"]),
        ("material_waste_kg", target["material_waste_kg"]),
        ("CO2_kg", target["CO2_emissions_kg"]),
        ("water_used_liters", target["water_consumption_liters"]),
        ("water_recycled_liters", target["water_recycled_liters"]),
        ("temperature_C", target["operating_temperature_C"]),
        ("humidity_percent", target["ambient_humidity_percent"]),
        ("vibration_mmps", target["vibration_level_mmps"]),
        ("renewables_percent", target["renewable_energy_percent"]),
        ("output_units", target["product_output_units"]),
        ("downtime_minutes", target["downtime_minutes"]),
        ("noise_dB", target["noise_level_dB"]),
        ("worker_count", target["worker_count"]),
        ("lubrication_level", target["lubrication_level"]),
        ("cooling_status", target["cooling_system_status"]),
        ("maintenance_required", str(target["maintenance_required"])),
        ("fuel_type", target["fuel_type"]),
    ]

    random.shuffle(fields)  # Non-standardized order

    headers = [f[0] for f in fields]
    values = [f'"{f[1]}"' for f in fields]

    csv_string = ",".join(headers) + "\n" + ",".join(values)

    return {"data_csv": csv_string}


def machine_09(target: dict) -> dict:
    """
    ### Machine 09 - Conflicting & Redundant Fields

    The machine outputs data with conflicting values (e.g., both uptime and downtime and availability_percent)
    and redundant computed fields (e.g., output_per_hour, CO2_per_unit).
    """
    total_minutes = 24 * 60
    availability_percent = 100 * (target["operation_hours"] * 60) / total_minutes
    output_per_hour = (
        round(target["product_output_units"] / target["operation_hours"], 2)
        if target["operation_hours"]
        else 0
    )
    CO2_per_unit = (
        round(target["CO2_emissions_kg"] / target["product_output_units"], 4)
        if target["product_output_units"]
        else 0
    )
    material_yield_percent = (
        round(100 * (target["product_output_units"] / target["material_used_kg"]), 2)
        if target["material_used_kg"]
        else 0
    )
    waste_rate_percent = (
        round(100 * (target["material_waste_kg"] / target["material_used_kg"]), 2)
        if target["material_used_kg"]
        else 0
    )
    energy_efficiency = (
        round(target["product_output_units"] / target["energy_consumption_kWh"], 3)
        if target["energy_consumption_kWh"]
        else 0
    )

    return {
        "timestamp": target["date"],
        "uptime": target["operation_hours"],
        "downtime": target["downtime_minutes"],
        "availability_percent": availability_percent,  # Redundant
        "shifttime_hours": target["operation_hours"] + 1,  # Conflicting
        "CO2_emissions_total": target["CO2_emissions_kg"],
        "CO2_per_unit": CO2_per_unit,  # Redundant
        "units_produced": target["product_output_units"],
        "output_per_hour": output_per_hour,  # Redundant
        "material_input_kg": target["material_used_kg"],
        "material_yield_percent": material_yield_percent,  # Redundant
        "material_scrap_kg": target["material_waste_kg"],
        "waste_rate_percent": waste_rate_percent,  # Redundant
        "energy_used_kWh": target["energy_consumption_kWh"],
        "energy_efficiency": energy_efficiency,  # Redundant
        "renewables_used_percent": target["renewable_energy_percent"],
        "temperature": target["operating_temperature_C"],
        "temp_max_threshold": target["operating_temperature_C"] + 10,  # Redundant
        "humidity": target["ambient_humidity_percent"],
        "vibration": target["vibration_level_mmps"],
        "loudness_dB": target["noise_level_dB"],
        "vibration_max_threshold": target["vibration_level_mmps"] + 0.5,  # Redundant
        "water_used": target["water_consumption_liters"],
        "water_reclaimed": target["water_recycled_liters"],
        "cooling": target["cooling_system_status"],
        "lubricant_status": target["lubrication_level"],
        "fuel_type_primary": target["fuel_type"],
        "fuel_type_backup": (
            "battery" if target["fuel_type"] != "battery" else "diesel"
        ),  # Redundant
        "maintenance_flag": target["maintenance_required"],
        "staff_on_duty": target["worker_count"],
        "worker_estimate": target["worker_count"] + 1,  # Conflicting
    }


def machine_10(target: dict) -> dict:
    """
    ### Machine 10 - Freeform Summary Report

    The machine produces a single natural-language paragraph with embedded metrics, descriptions,
    and context, mimicking human-written operator logs or AI-generated summaries.
    """
    summary = (
        f"On {target['date']}, Machine 10 operated for {target['operation_hours']} hours "
        f"and produced {target['product_output_units']} units. It consumed {target['energy_consumption_kWh']} kilowatt-hours "
        f"of electricity (primary fuel: {target['fuel_type']}). "
        f"Material input was estimated at {target['material_used_kg']} kg, with {target['material_waste_kg']} kg wasted. "
        f"CO2 emissions were reported near {target['CO2_emissions_kg']} kg. "
        f"Water usage was high — {target['water_consumption_liters']}L drawn, but {target['water_recycled_liters']}L could be reclaimed. "
        f"Internal temperature peaked at {target['operating_temperature_C']}°C, "
        f"and ambient humidity hovered around {target['ambient_humidity_percent']}%. "
        f"The system experienced downtime of {target['downtime_minutes']} minutes, but no maintenance was flagged. "
        f"Sound levels reached {target['noise_level_dB']} dB; vibration at {target['vibration_level_mmps']} mm/s. "
        f"Lubrication level was {target['lubrication_level']}; cooling system was turned {target['cooling_system_status']}. "
        f"On this day, {target['worker_count']} workers were present to maintain the machine. "
        f"Renewables contributed {target['renewable_energy_percent']}% to total energy."
    )

    return {"operator_summary": summary}


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
