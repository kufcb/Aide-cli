import json
import re
from concurrent.futures import Future, ThreadPoolExecutor
from threading import Lock
from pathlib import Path
from models.zhipu_chat import model as llm
from langchain_core.messages import SystemMessage, HumanMessage
from logs.logging_server import logger

# 项目根目录下的 memory/Aide.md
MEMORY_DIR = Path(__file__).resolve().parent.parent / "memory"
AIDE_MEMORY_FILE = MEMORY_DIR / "Aide.md"
MEMORY_LOCK = Lock()
MEMORY_EXECUTOR = ThreadPoolExecutor(max_workers=1, thread_name_prefix="aide-memory")

DEFAULT_MEMORY_TEMPLATE = """# 用户偏好记忆
## 已确认偏好
- 暂无

## 回复风格偏好
- 暂无

## 约束与禁忌
- 暂无

## 最近更新
- 暂无
"""

MEMORY_UPDATE_SYSTEM_PROMPT = """你是 AI 助手的“用户偏好记忆整理器”。
你的目标：从新输入中识别长期偏好，并把偏好整理进记忆文档。

请严格遵守：
1. 只记录长期有效、可复用的偏好和约束（例如语言偏好、输出风格、禁忌、工作习惯）。
2. 一次性问题、临时指令、与偏好无关的普通对话不要写入。
3. 在保留已有有效信息的前提下去重、合并、精炼表达。
4. 输出必须是合法 JSON，且只输出 JSON，不要额外解释。

返回 JSON 结构：
{
  "is_preference": true/false,
  "should_update": true/false,
  "reason": "简短原因",
  "updated_memory_markdown": "整理后的完整记忆 Markdown（无需更新时可返回原文）"
}
"""


def init_aide_memory_file() -> Path:
    """初始化 memory/Aide.md。若目录或文件不存在，则自动创建。"""
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    if not AIDE_MEMORY_FILE.exists():
        AIDE_MEMORY_FILE.write_text(DEFAULT_MEMORY_TEMPLATE, encoding="utf-8")
    elif not AIDE_MEMORY_FILE.read_text(encoding="utf-8").strip():
        AIDE_MEMORY_FILE.write_text(DEFAULT_MEMORY_TEMPLATE, encoding="utf-8")
    return AIDE_MEMORY_FILE


def read_all_memory() -> str:
    """读取 Aide.md 全部内容。"""
    init_aide_memory_file()
    return AIDE_MEMORY_FILE.read_text(encoding="utf-8")


def write_all_memory(content: str) -> None:
    """全量覆盖写入 Aide.md。"""
    init_aide_memory_file()
    AIDE_MEMORY_FILE.write_text(content, encoding="utf-8")


def append_memory(content: str, add_newline: bool = False) -> None:
    """向 Aide.md 追加写入内容。"""
    init_aide_memory_file()
    text = f"{content}\n" if add_newline else content
    with AIDE_MEMORY_FILE.open("a", encoding="utf-8") as f:
        f.write(text)


def _coerce_message_content_to_text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text")
                if text:
                    parts.append(str(text))
            else:
                parts.append(str(item))
        return "".join(parts)
    return str(content)


def _extract_json(text: str) -> dict:
    raw = text.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
        raw = re.sub(r"\s*```$", "", raw)

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    matched = re.search(r"\{[\s\S]*\}", raw)
    if not matched:
        raise ValueError("模型输出中未找到 JSON 对象")
    return json.loads(matched.group(0))


def _normalize_markdown(content: str) -> str:
    normalized = content.strip()
    return f"{normalized}\n" if normalized else DEFAULT_MEMORY_TEMPLATE


def _build_memory_update(current_memory: str, user_input: str) -> dict:
    prompt = (
        f"当前记忆文档：\n{current_memory}\n\n"
        f"新用户输入：\n{user_input}\n\n"
        "请输出约定 JSON。"
    )
    response = llm.invoke(
        [
            SystemMessage(content=MEMORY_UPDATE_SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ]
    )

    raw = _coerce_message_content_to_text(getattr(response, "content", ""))
    data = _extract_json(raw)
    data.setdefault("is_preference", False)
    data.setdefault("should_update", False)
    data.setdefault("reason", "")
    data.setdefault("updated_memory_markdown", current_memory)
    return data


def update_user_preference_memory(user_input: str) -> dict:
    """同步更新用户偏好记忆。可被异步线程调用。"""
    if not user_input or not user_input.strip():
        return {"status": "skipped", "reason": "empty_input"}

    with MEMORY_LOCK:
        current_memory = read_all_memory()

    try:
        result = _build_memory_update(current_memory=current_memory, user_input=user_input)
    except Exception:
        logger.exception("记忆分析失败，已跳过本次记忆更新")
        return {"status": "error", "reason": "llm_analyze_failed"}

    should_update = bool(result.get("should_update"))
    updated_markdown = _normalize_markdown(result.get("updated_memory_markdown", current_memory))

    if not should_update:
        return {
            "status": "unchanged",
            "is_preference": bool(result.get("is_preference")),
            "reason": result.get("reason", ""),
        }

    with MEMORY_LOCK:
        latest_memory = read_all_memory()
        if updated_markdown.strip() == latest_memory.strip():
            return {
                "status": "unchanged",
                "is_preference": bool(result.get("is_preference")),
                "reason": "memory_same_after_merge",
            }

        write_all_memory(updated_markdown)

    return {
        "status": "updated",
        "is_preference": bool(result.get("is_preference")),
        "reason": result.get("reason", ""),
    }


def read_memory_snapshot() -> str:
    """线程安全地读取记忆内容，供主 Agent 构建上下文。"""
    with MEMORY_LOCK:
        return read_all_memory()


def trigger_memory_update_async(user_input: str) -> Future:
    """异步触发偏好记忆更新（不阻塞主对话）。"""
    return MEMORY_EXECUTOR.submit(update_user_preference_memory, user_input)


def agent_run() -> None:
    read_all_memory()
