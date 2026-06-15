from __future__ import annotations


class TokenStore:
    def __init__(self) -> None:
        self._tokens: dict[int, str] = {}

    def save(self, chat_id: int, token: str) -> None:
        self._tokens[chat_id] = token

    def get(self, chat_id: int) -> str | None:
        return self._tokens.get(chat_id)

    def delete(self, chat_id: int) -> None:
        self._tokens.pop(chat_id, None)


token_store = TokenStore()
