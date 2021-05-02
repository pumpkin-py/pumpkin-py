from typing import List


class LogCache:
    """Singleton class used to send bot log data to dedicated discord channel."""

    __instance = None
    messages: List[str] = list()

    def __init__(self):
        if LogCache.__instance is not None:
            raise Exception(f"{self.__class__.__name__} has to be a singleton!")
        LogCache.__instance = self

    @staticmethod
    def cache():
        """Get singleton instance of the LogCache object."""
        if LogCache.__instance is None:
            LogCache()
        return LogCache.__instance

    def add(self, message: str, *args, **kwargs) -> None:
        """Add new log message."""
        self.messages.append(message.strip("\n"))

    def get(self):
        """Get oldest log message."""
        if not len(self.messages):
            return None
        return self.messages.pop(0)

    def get_all(self):
        """Get all log messages."""
        messages = self.messages[:]
        self.messages = list()
        return messages

    #

    def __repr__(self) -> str:
        return f"{self.__class__.__name__} messages={self.messages}>"
