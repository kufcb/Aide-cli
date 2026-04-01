from pathlib import Path

# 项目根目录下的 memory/Aide.md
MEMORY_DIR = Path(__file__).resolve().parent.parent / "memory"
AIDE_MEMORY_FILE = MEMORY_DIR / "Aide.md"


def init_aide_memory_file() -> Path:
    """初始化 memory/Aide.md。若目录或文件不存在，则自动创建。"""
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    if not AIDE_MEMORY_FILE.exists():
        AIDE_MEMORY_FILE.write_text("", encoding="utf-8")
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


def agent_run() -> None:
    read_all_memory()
