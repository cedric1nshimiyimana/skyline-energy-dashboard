from core.event_bus import EventBus


class DeviceRegistry:
    """
    Central registry for all energy system devices.
    """

    def __init__(self, event_bus: EventBus):
        self.devices = {}
        self.event_bus = event_bus

    def register_device(self, device_id: str, device_info: dict):
        self.devices[device_id] = device_info

        # Notify the system that a device was registered
        self.event_bus.publish(
            event_type="device_registered",
            data={
                "device_id": device_id,
                "device_info": device_info
            }
        )

    def get_device(self, device_id: str):
        return self.devices.get(device_id)

    def list_devices(self):
        return self.devices
