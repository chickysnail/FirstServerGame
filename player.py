from random import randint


class Player:
    def __init__(self, username: str) -> None:
        self.username = username.decode('utf-8').rstrip()
        self.order = None
        self.score = None

    def reset(self) -> None:
        self.order = None
        self.score = None

    def roll(self) -> None:
        self.score = randint(1, 6)

    def __str__(self) -> str:
        return self.username
