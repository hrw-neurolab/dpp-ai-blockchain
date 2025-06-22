import json
import time
import os

import pywaves as pw
import requests
from dotenv import load_dotenv
from loguru import logger

from src.blockchain.blockchain_connector import BlockchainConnector


class WavesConnector(BlockchainConnector):
    """Connector implementation for the Waves blockchain."""

    def __init__(self):
        load_dotenv()

        self.__node_url = "https://nodes-testnet.wavesnodes.com"

        pw.setNode(node=self.__node_url, chain_id="T")
        pw.setChain("testnet")

        self.__init_addresses()

    def __init_addresses(self):
        """Initialize addresses for the caller, machines, and aggregate."""
        self.__caller_address = pw.Address(seed=os.getenv("SEED"))

        addresses_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "waves_addresses.json"
        )

        with open(addresses_path, "r") as f:
            machine_addresses = json.load(f)

        self.__machine_addresses: dict[str, pw.Address] = {}

        for i, data in enumerate(machine_addresses["machines"]):
            machine_id = f"M{i+1:03d}"
            seed = data["seedPhrase"]
            self.__machine_addresses[machine_id] = pw.Address(seed=seed)

        seed = machine_addresses["aggregated"]["seedPhrase"]
        self.__aggregate_address = pw.Address(seed=seed)

    def __scale_floats(self, data: dict, factor: int = 100) -> dict:
        """Helper function to scale float values in the dictionary by a given factor.
        This is necessary because Waves Smart Contracts do not support float values.

        Args:
            data (dict): The dictionary containing float values to scale.
            factor (int): The factor by which to scale the float values. Default is 100.

        Returns:
            dict: A new dictionary with float values scaled to integers.
        """

        def scale(value):
            try:
                float_val = float(value)
                scaled_val = int(float_val * factor)
                return str(scaled_val)
            except (ValueError, TypeError):
                return value

        return {k: scale(v) for k, v in data.items()}

    def __stringify_values(self, data: dict) -> dict:
        """Helper function to convert all non-string values in a dictionary to strings.
        This is necessary because Waves Smart Contracts only accept string values.

        Args:
            data (dict): The dictionary containing values to stringify.

        Returns:
            dict: A new dictionary with all non-string values converted to strings.
        """

        def stringify(value):
            if isinstance(value, dict):
                return {k: stringify(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [stringify(v) for v in value]
            elif not isinstance(value, str):
                return str(value)
            return value

        return stringify(data)

    def __get_tx_info(self, tx_id: str) -> dict | None:
        """Helper function to fetch transaction information from the Waves blockchain.

        Args:
            tx_id (str): The transaction ID to fetch information for.

        Returns:
            dict: A dictionary containing transaction information, or None if not found.
        """
        api_url = f"{self.__node_url}/transactions/info/{tx_id}"

        try:
            response = requests.get(api_url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            if response.status_code != 404:
                logger.error(f"Error fetching transaction data: {e}")
            return None

    def wait_for_transaction(self, tx_id: str, timeout: int = 60, interval: int = 1):
        """Wait for a transaction to be confirmed on the Waves blockchain.

        Args:
            tx_id (str): The transaction ID to wait for.
            timeout (int): The maximum time to wait for confirmation in seconds. Default is 60 seconds.
            interval (int): The interval between checks in seconds. Default is 1 second.

        Returns:
            dict: A dictionary containing transaction information if confirmed, or None if timeout is reached.
        """
        elapsed = 0

        while elapsed < timeout:
            tx_info = self.__get_tx_info(tx_id)

            if tx_info and "height" in tx_info:
                return tx_info

            time.sleep(interval)
            elapsed += interval

        logger.warning("Timeout reached while waiting for transaction confirmation")
        return None

    def call_store_metrics(self, machine_id: str, payload: dict) -> str:
        if machine_id not in self.__machine_addresses:
            raise ValueError(f"Invalid machine ID: {machine_id}")

        machine_address = self.__machine_addresses[machine_id]

        payload = self.__scale_floats(payload)
        payload = self.__stringify_values(payload)
        payload = json.dumps(payload, separators=(",", ":"))

        tx = self.__caller_address.invokeScript(
            dappAddress=machine_address.address,
            functionName="storeMetrics",
            params=[{"type": "string", "value": payload}],
            payments=[],
        )

        return tx["id"]

    def call_aggregate_metrics(self, date_str: str) -> str:
        tx = self.__caller_address.invokeScript(
            dappAddress=self.__aggregate_address.address,
            functionName="aggregateBatchData",
            params=[{"type": "string", "value": date_str}],
            payments=[],
        )

        return tx["id"]
