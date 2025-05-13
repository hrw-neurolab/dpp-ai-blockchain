import json
import time
import os

import pywaves as pw
import requests
from dotenv import load_dotenv
from loguru import logger


class MetricCaller:
    def __init__(self):
        load_dotenv()
        seed = os.getenv("SEED")
        self.node_url = "https://nodes-testnet.wavesnodes.com"
        pw.setNode(node=self.node_url, chain_id="T")
        pw.setChain("testnet")
        self.caller = pw.Address(seed=seed)

        addresses_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "waves_addresses.json"
        )

        with open(addresses_path, "r") as f:
            self.addresses = json.load(f)

        self.machine_map = {
            f"M{i+1:03d}": data for i, data in enumerate(self.addresses["machines"])
        }
        self.aggregated = self.addresses["aggregated"]

    def scale_floats_in_dict(self, data: dict, factor: int = 100) -> dict:
        def scale(value):
            try:
                float_val = float(value)
                scaled_val = int(float_val * factor)
                return str(scaled_val)
            except (ValueError, TypeError):
                return value

        return {k: scale(v) for k, v in data.items()}

    def call_store_metrics(self, machine_id: str, json_payload: dict):
        if machine_id not in self.machine_map:
            raise ValueError(f"Invalid machine ID: {machine_id}")

        seed = self.machine_map[machine_id]["seedPhrase"]
        addr = pw.Address(seed=seed)
        json_payload = self.scale_floats_in_dict(json_payload)
        stringified_payload = self.stringify_non_strings(json_payload)
        json_str = json.dumps(stringified_payload, separators=(",", ":"))

        tx = self.caller.invokeScript(
            dappAddress=addr.address,
            functionName="storeMetrics",
            params=[{"type": "string", "value": json_str}],
            payments=[],
        )
        print(tx)

        return tx

    def stringify_non_strings(self, data: dict) -> dict:
        def stringify(value):
            if isinstance(value, dict):
                return {k: stringify(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [stringify(v) for v in value]
            elif not isinstance(value, str):
                return str(value)
            return value

        return stringify(data)

    def call_aggregate_metrics(self, date_str: str):
        self.caller.invokeScript(
            dappAddress=self.aggregated["address"],
            functionName="aggregateBatchData",
            params=[{"type": "string", "value": date_str}],
            payments=[],
        )

    def wait_for_transaction(self, tx: dict, timeout: int = 60, interval: int = 1):
        tx_id = tx["id"]
        elapsed = 0

        while elapsed < timeout:
            tx_info = self.get_json_data(f"{self.node_url}/transactions/info/{tx_id}")

            if tx_info and "height" in tx_info:
                return tx_info

            time.sleep(interval)
            elapsed += interval

        logger.warning("Timeout reached while waiting for transaction confirmation")
        return None

    def get_json_data(self, api_url: str):
        try:
            response = requests.get(api_url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            if response.status_code != 404:
                logger.error(f"Error fetching transaction data: {e}")
            return None
