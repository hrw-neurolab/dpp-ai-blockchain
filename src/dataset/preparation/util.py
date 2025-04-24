from datetime import datetime


h_to_s = lambda h: round(h * 3600, 2)

min_to_s = lambda s: round(s * 60)

kwh_to_mwh = lambda kWh: round(kWh / 1000, 5)

kg_to_g = lambda kg: round(kg * 1000, 2)

kg_to_mg = lambda kg: round(kg * 1e6, 2)

kg_to_t = lambda kg: round(kg / 1000, 5)

l_to_ml = lambda l: round(l * 1000, 2)

to_thousands = lambda units: round(units / 1000, 5)

c_to_k = lambda c: round(c + 273.15, 2)

pct_to_frac = lambda pct: round(pct / 100, 4)

mmps_to_mmpmin = lambda mmps: round(mmps * 60, 2)

date_to_iso = lambda date: datetime.strptime(date, "%Y-%m-%d").isoformat()

categorical = {
    "low": "reduced",
    "medium": "normal",
    "high": "increased",
    "operational": "ok",
    "faulty": "problem",
    "off": "disabled",
    True: "yes",
    False: "no",
    "electric": "battery_powered",
    "diesel": "fossil_fuel",
    "natural_gas": "compressed_gas",
    "hybrid": "dual_source",
}


def convert_units_simple(sample: dict) -> dict:
    return {
        "date": date_to_iso(sample["date"]),
        "operation_hours": h_to_s(sample["operation_hours"]),
        "energy_consumption_kWh": kwh_to_mwh(sample["energy_consumption_kWh"]),
        "material_used_kg": kg_to_g(sample["material_used_kg"]),
        "material_waste_kg": kg_to_mg(sample["material_waste_kg"]),
        "CO2_emissions_kg": kg_to_t(sample["CO2_emissions_kg"]),
        "water_consumption_liters": l_to_ml(sample["water_consumption_liters"]),
        "water_recycled_liters": l_to_ml(sample["water_recycled_liters"]),
        "product_output_units": to_thousands(sample["product_output_units"]),
    }


def convert_units(sample: dict) -> dict:
    return {
        **convert_units_simple(sample),
        "operating_temperature_C": c_to_k(sample["operating_temperature_C"]),
        "ambient_humidity_percent": pct_to_frac(sample["ambient_humidity_percent"]),
        "vibration_level_mmps": mmps_to_mmpmin(sample["vibration_level_mmps"]),
        "renewable_energy_percent": pct_to_frac(sample["renewable_energy_percent"]),
        "downtime_minutes": min_to_s(sample["downtime_minutes"]),
        "noise_level_dB": sample["noise_level_dB"],
        "worker_count": sample["worker_count"],
        "lubrication_level": categorical[sample["lubrication_level"]],
        "cooling_system_status": categorical[sample["cooling_system_status"]],
        "maintenance_required": categorical[sample["maintenance_required"]],
        "fuel_type": categorical[sample["fuel_type"]],
    }
