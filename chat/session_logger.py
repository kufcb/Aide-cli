import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Union
from uuid import uuid4


@dataclass
class SessionMeta:
    session_id: str
    file_path: Path
    turn_id: int = 0


class ChatSessionLogger:
    def __init__(self, chat_dir: Union[Path, str]):
        self.chat_dir = Path(chat_dir)
        self.chat_dir.mkdir(parents=True, exist_ok=True)
        self.session = SessionMeta(session_id="", file_path=self.chat_dir / "placeholder.jsonl")
        self.new_session()

    @staticmethod
    def _generate_session_id() -> str:
        now = datetime.now().strftime("%Y%m%d-%H%M%S")
        suffix = uuid4().hex[:6]
        return f"{now}-{suffix}"

    @staticmethod
    def _now_iso() -> str:
        return datetime.now().astimezone().isoformat(timespec="seconds")

    def _append(self, payload: dict) -> None:
        with self.session.file_path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(payload, ensure_ascii=False) + "\n")

    def new_session(self) -> SessionMeta:
        session_id = self._generate_session_id()
        file_path = self.chat_dir / f"{session_id}.jsonl"
        self.session = SessionMeta(session_id=session_id, file_path=file_path, turn_id=0)
        self._append(
            {
                "type": "session_start",
                "session_id": self.session.session_id,
                "timestamp": self._now_iso(),
            }
        )
        return self.session

    def record_turn(self, user_input: str, assistant_output: str) -> None:
        self.session.turn_id += 1
        self._append(
            {
                "type": "chat_turn",
                "session_id": self.session.session_id,
                "turn_id": self.session.turn_id,
                "timestamp": self._now_iso(),
                "user_input": user_input,
                "assistant_output": assistant_output,
            }
        )

    def record_error(self, user_input: str, error_message: str) -> None:
        self.session.turn_id += 1
        self._append(
            {
                "type": "chat_error",
                "session_id": self.session.session_id,
                "turn_id": self.session.turn_id,
                "timestamp": self._now_iso(),
                "user_input": user_input,
                "error": error_message,
            }
        )
