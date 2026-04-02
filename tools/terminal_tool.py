from config import TERMINAL_COMMAND_CONFIRM_ENABLED
from langchain_core.tools import tool


def _confirm_command_execution(command: str) -> bool:
    if not TERMINAL_COMMAND_CONFIRM_ENABLED:
        return True

    print("[提醒] 即将执行终端命令：")
    print(f"    {command}")
    print("请输入 y/yes 确认执行，其他输入将取消。")
    try:
        user_answer = input("确认执行？[y/n]: ").strip().lower()
    except EOFError:
        return False
    return user_answer in {"y", "yes"}


@tool
def run_terminal_command(command):
    """用于执行终端命令"""
    import subprocess

    if not _confirm_command_execution(command):
        return "已取消执行终端命令。"

    run_result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return run_result.stdout if run_result.returncode == 0 else run_result.stderr


__all__ = ["run_terminal_command"]
