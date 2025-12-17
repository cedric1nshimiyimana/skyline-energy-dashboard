from core.event_bus import EventBus
from core.device_registry.registry_manager import DeviceRegistry


def on_device_registered(event_data):
    print("📡 EVENT RECEIVED: Device Registered")
    print(event_data)


def main():
    event_bus = EventBus()

    # Subscribe to device registration events
    event_bus.subscribe(
        event_type="device_registered",
        callback=on_device_registered
    )

    registry = DeviceRegistry(event_bus=event_bus)

    # Register a fake device (simulating discovery)
    registry.register_device(
        device_id="battery_001",
        device_info={
            "type": "battery",
            "brand": "Victron",
            "model": "Lithium Smart",
            "capacity_kwh": 10
        }
    )


if __name__ == "__main__":
    main()
