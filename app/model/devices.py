from typing import List, Tuple

import torch
from pypylon import pylon


class Devices:
    @classmethod
    def get_available_cameras(cls) -> List[str]:
        devices = list(pylon.TlFactory.GetInstance().EnumerateDevices())
        return [device.GetSerialNumber() for device in devices]

    @classmethod
    def get_computation_devices(cls) -> List[Tuple[str, str]]:
        devices = [("cpu", "CPU")]

        if torch.cuda.is_available():
            for i in range(torch.cuda.device_count()):
                device_name = torch.cuda.get_device_name(i)
                device_id = f"cuda:{i}"
                devices.append((device_id, device_name))

        # Add number to duplicate device names
        device_names = [device_name for _, device_name in devices]
        for i, (device_id, device_name) in enumerate(devices):
            if device_names.count(device_name) > 1:
                devices[i] = (device_id, f"{device_name} ({device_names[:i].count(device_name)})")

        return devices
