from abc import ABC, abstractmethod
from typing import List

class MailerInterface(ABC):
    @abstractmethod
    def send(self, subject: str, recipients: List[str], html_body: str, sender: str) -> None:
        pass

    @abstractmethod
    def connect(self):
        pass