from abc import ABC, abstractmethod

class Notifier(ABC):
    @abstractmethod
    def send(self, to: str, message: str) -> None:
        pass

class EmailNotifier(Notifier):
    def send(self, to: str, message: str) -> None:
        print(f"[EMAIL] to={to} msg={message}")

class SmsNotifier(Notifier):
    def send(self, to: str, message: str) -> None:
        print(f"[SMS] to={to} msg={message}")

class AlertService:
    def __init__(self, notifier: Notifier):
        self.notifier = notifier

    def critical_alert(self, user: str) -> None:
        self.notifier.send(user, "🚨 Critical alert: action required!")


AlertService(EmailNotifier()).critical_alert("manava@mail.com")
AlertService(SmsNotifier()).critical_alert("+91xxxxxxxxxx")
