import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Union
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

    @staticmethod
    def _current_date_folder() -> str:
        return datetime.now().strftime("%Y-%m-%d")

    def _append(self, payload: dict) -> None:
        self.session.file_path.parent.mkdir(parents=True, exist_ok=True)
        with self.session.file_path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(payload, ensure_ascii=False) + "\n")

    def new_session(self) -> SessionMeta:
        session_id = self._generate_session_id()
        date_dir = self.chat_dir / self._current_date_folder()
        date_dir.mkdir(parents=True, exist_ok=True)
        file_path = date_dir / f"{session_id}.jsonl"
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

    def list_session_files(self) -> list[Path]:
        session_files = [path for path in self.chat_dir.rglob("*.jsonl") if path.is_file()]
        return sorted(session_files, key=lambda path: path.stat().st_mtime, reverse=True)

    @staticmethod
    def _read_jsonl_records(file_path: Path) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        with file_path.open("r", encoding="utf-8") as file:
            for line in file:
                raw = line.strip()
                if not raw:
                    continue
                try:
                    parsed = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                if isinstance(parsed, dict):
                    records.append(parsed)
        return records

    def read_history(self, limit: int = 10) -> list[dict[str, Any]]:
        if limit <= 0:
            return []

        history: list[dict[str, Any]] = []
        for file_path in self.list_session_files()[:limit]:
            records = self._read_jsonl_records(file_path)
            session_start = next((item for item in records if item.get("type") == "session_start"), {})
            turns = [item for item in records if item.get("type") == "chat_turn"]
            errors = [item for item in records if item.get("type") == "chat_error"]
            last_timestamp = next(
                (item.get("timestamp") for item in reversed(records) if item.get("timestamp")),
                "",
            )

            history.append(
                {
                    "session_id": session_start.get("session_id", file_path.stem),
                    "started_at": session_start.get("timestamp", ""),
                    "last_timestamp": last_timestamp,
                    "turn_count": len(turns),
                    "error_count": len(errors),
                    "file_path": file_path,
                    "turns": turns,
                }
            )

        return history
