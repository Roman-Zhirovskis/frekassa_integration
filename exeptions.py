from dataclasses import dataclass


@dataclass(eq=False)
class FrekassaException(Exception):
    text: dict
    status_code: int

    @property
    def message(self) -> str:
        if self.status_code == 400:
            return self.text.get("error")

        return self.text.get("message")
