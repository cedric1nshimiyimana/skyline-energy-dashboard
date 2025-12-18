class EventBus:
    """
    Simple event bus for decoupled communication
    between system components.
    """

    def __init__(self):
        self.subscribers = {}

    def subscribe(self, event_type: str, callback):
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)

    def publish(self, event_type: str, data=None):
        callbacks = self.subscribers.get(event_type, [])
        for callback in callbacks:
            callback(data)
