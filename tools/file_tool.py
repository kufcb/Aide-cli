from pathlib import Path

from langchain_core.tools import tool


def _resolve_path(file_path: str) -> Path:
    """将输入路径解析为绝对路径。"""
    target_path = Path(file_path).expanduser()
    return target_path if target_path.is_absolute() else Path.cwd() / target_path


@tool
def read_file(file_path):
    """用于读取文件内容。file_path 支持绝对路径和相对路径（相对当前工作目录）。"""
    resolved_path = _resolve_path(file_path)

    if not resolved_path.exists():
        return f"读取失败：文件不存在 -> {resolved_path}"
    if not resolved_path.is_file():
        return f"读取失败：目标不是文件 -> {resolved_path}"

    with resolved_path.open("r", encoding="utf-8") as f:
        return f.read()


@tool
def write_to_file(file_path, content):
    """
    将指定内容写入指定文件。
    file_path 支持绝对路径和相对路径（相对当前工作目录）。
    写入前会检查文件是否存在。
    """
    resolved_path = _resolve_path(file_path)

    if not resolved_path.exists():
        return f"写入失败：文件不存在 -> {resolved_path}"
    if not resolved_path.is_file():
        return f"写入失败：目标不是文件 -> {resolved_path}"

    with resolved_path.open("w", encoding="utf-8") as f:
        f.write(content.replace("\\n", "\n"))
    return "写入成功"


__all__ = ["write_to_file","read_file"]
