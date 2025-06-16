# singleton/singleton.py
class SingletonType(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(SingletonType, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class NotificationManager(metaclass=SingletonType):
    def __init__(self):
        self.messages = []

    def send_notification(self, user, message):
        self.messages.append((user.username, message))
        # You could later expand to actually send emails or store them
        print(f"Notification sent to {user.username}: {message}")

    def get_all_notifications(self):
        return self.messages
