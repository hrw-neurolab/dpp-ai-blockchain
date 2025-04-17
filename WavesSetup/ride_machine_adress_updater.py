import re

class RideMachineAddressUpdater:
    def __init__(self, ride_file_path: str):
        self.ride_file_path = ride_file_path
        self.machine_addresses = []

    def set_addresses(self, addresses: list[str]):
        if len(addresses) != 10:
            raise ValueError("You must provide exactly 10 machine addresses.")
        self.machine_addresses = addresses

    def generate_machine_lines(self) -> list[str]:
        return [
            f"let machine{i+1}_address = Address(base58'{addr}')"
            for i, addr in enumerate(self.machine_addresses)
        ]

    def update_ride_file(self, output_path: str = None):
        with open(self.ride_file_path, "r") as f:
            lines = f.readlines()

        new_lines = []
        machine_line_pattern = re.compile(r"let machine\d+_address = Address\(base58'[A-Za-z0-9]+'\)")
        machine_idx = 0

        for line in lines:
            if machine_line_pattern.match(line.strip()) and machine_idx < 10:
                new_lines.append(self.generate_machine_lines()[machine_idx] + "\n")
                machine_idx += 1
            else:
                new_lines.append(line)

        if output_path:
            with open(output_path, "w") as f:
                f.writelines(new_lines)
        else:
            print("".join(new_lines))

