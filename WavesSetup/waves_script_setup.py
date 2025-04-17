import os
import time
import random
import string
import json
import pywaves as pw
from dotenv import load_dotenv
from ride_machine_adress_updater import RideMachineAddressUpdater  

class WavesScriptSetup:
    def __init__(self):
        load_dotenv()
        bank_seed = os.getenv("BANK_SEED")

        pw.setNode(node='https://nodes-testnet.wavesnodes.com', chain_id='T')
        pw.setChain('testnet')

        self.bank_account = pw.Address(seed=bank_seed)
        self.machine_addresses = []
        self.aggregated_address = None

    def generate_seed_phrase(self, length=15):
        words = [''.join(random.choices(string.ascii_letters + string.digits, k=8)) for _ in range(length)]
        return ' '.join(words)

    def create_waves_address(self):
        seed = self.generate_seed_phrase()
        return {
            "seedPhrase": seed,
            "address_obj": pw.Address(seed=seed)
        }

    def setup_addresses(self):
        for i in range(10):
            addr_info = self.create_waves_address()
            addr_info["address"] = addr_info["address_obj"].address
            self.machine_addresses.append(addr_info)

        self.aggregated_address = self.create_waves_address()
        self.aggregated_address["address"] = self.aggregated_address["address_obj"].address

        # Prepare addresses for JSON serialization
        json_serializable = {
            "machines": [
                {
                    "address": entry["address"],
                    "seedPhrase": entry["seedPhrase"]
                } for entry in self.machine_addresses
            ],
            "aggregated": {
                "address": self.aggregated_address["address"],
                "seedPhrase": self.aggregated_address["seedPhrase"]
            }
        }

        with open("waves_addresses.json", "w") as f:
            json.dump(json_serializable, f, indent=4)

        print("Addresses created and saved to waves_addresses.json")

        # Update aggregate Ride script with the new machine addresses
        machine_base58_list = [entry["address"] for entry in self.machine_addresses]
        updater = RideMachineAddressUpdater("aggregate_contract.ride")
        updater.set_addresses(machine_base58_list)
        updater.update_ride_file("aggregate_contract_updated.ride")

    def transfer_tokens(self, address_list, amount=10000000):
        for entry in address_list:
            recip = entry["address_obj"]
            tx = self.bank_account.sendWaves(recip, amount)
            print(f"Sent {amount} to {recip.address}: TX {tx}")

    def set_script_for_address(self, address_obj, script_path):
        try:
            with open(script_path, 'r') as file:
                script = file.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"Script file not found: {script_path}")

        max_attempts = 5
        for attempt in range(1, max_attempts + 1):
            tx = address_obj.setScript(script, 900000)
            if isinstance(tx, dict) and "error" in tx:
                print(f"Error setting script (attempt {attempt}): {tx}. Waiting 10s...")
                time.sleep(10)
            else:
                print(f"Script set successfully for {address_obj.address}, TX: {tx}")
                return tx

        raise Exception("Failed to set script after 5 attempts.")

    def deploy_all(self, machine_script="Machine_Smart_Contracts.ride", aggregated_script="aggregate_contract_updated.ride"):
        print("Transferring tokens to machine addresses...")
        self.transfer_tokens(self.machine_addresses)

        print("Transferring tokens to aggregated address...")
        self.transfer_tokens([self.aggregated_address])

        print("Setting machine scripts...")
        for entry in self.machine_addresses:
            self.set_script_for_address(entry["address_obj"], machine_script)

        print("Setting aggregated script...")
        self.set_script_for_address(self.aggregated_address["address_obj"], aggregated_script)


if __name__ == "__main__":
    setup = WavesScriptSetup()
    setup.setup_addresses()  
    setup.deploy_all()      
