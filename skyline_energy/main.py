from core.event_bus import EventBus
from core.device_registry.registry_manager import DeviceRegistry
import app  # This connects the UI to your logic

def on_device_registered(event_data):
    """Callback for when a new hardware device is detected."""
    print("📡 EVENT RECEIVED: Device Registered")
    print(event_data)

def initialize_backend():
    """Sets up the Digital Twin infrastructure."""
    event_bus = EventBus()

    # Subscribe to device registration events
    event_bus.subscribe(
        event_type="device_registered",
        callback=on_device_registered
    )

    registry = DeviceRegistry(event_bus=event_bus)

    # Register the Victron battery (simulating hardware discovery)
    registry.register_device(
        device_id="battery_001",
        device_info={
            "type": "battery",
            "brand": "Victron",
            "model": "Lithium Smart",
            "capacity_kwh": 10
        }
    )
    return event_bus, registry

if __name__ == "__main__":
    # 1. Start the backend logic
    bus, reg = initialize_backend()
    
    # 2. Launch the Streamlit UI (This keeps the app alive)
    # This prevents the "Stopping..." message in your logs
    app.main_dashboard()