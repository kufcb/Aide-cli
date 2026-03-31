
from datetime import datetime
import warnings

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.shortcuts import CompleteStyle, clear
from agent.react_agent import agent_run
from config import STYLE

try:
    from jwt import InsecureKeyLengthWarning

    warnings.filterwarnings("ignore", category=InsecureKeyLengthWarning)
except Exception:
    pass

COMMANDS = {
    "/help": "显示命令列表",
    "/time": "显示当前时间",
    "/clear": "清空屏幕",
    "/exit": "退出程序",
}



class SlashCommandCompleter(Completer):
    def __init__(self, commands: dict[str, str]):
        self.commands = commands

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor.strip()
        if not text.startswith("/"):
            return

        head = text.split()[0]
        for cmd, desc in self.commands.items():
            if cmd.startswith(head):
                yield Completion(
                    cmd,
                    start_position=-len(head),
                    display=f"{cmd:<8} {desc}",
                )


def print_welcome():
    print("Aide CLI")
    print("输入普通文本开始对话，输入 / 触发命令提示。")
    print("输入 /help 查看所有命令。")
    print("-" * 48)


def print_help():
    print("\n可用命令")
    for cmd, desc in COMMANDS.items():
        print(f"  {cmd:<8} {desc}")
    print()


def handle_command(message: str) -> bool:
    if message == "/exit":
        print("Bye.")
        return False

    if message == "/help":
        print_help()
        return True

    if message == "/time":
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"当前时间: {now}")
        return True

    if message == "/clear":
        clear()
        print_welcome()
        return True

    print(f"未知命令: {message}，输入 /help 查看可用命令。")
    return True


def main():
    print_welcome()

    completer = SlashCommandCompleter(COMMANDS)
    key_bindings = KeyBindings()

    @key_bindings.add("/")
    def _(event):
        buffer = event.app.current_buffer
        buffer.insert_text("/")
        buffer.start_completion(select_first=False)

    session = PromptSession()

    while True:
        try:
            user_input = session.prompt(
                message=HTML(
                    "<prompt.dim>[Aide]</prompt.dim> "
                    "<prompt.symbol>></prompt.symbol> "
                ),
                completer=completer,
                complete_style=CompleteStyle.MULTI_COLUMN,
                complete_while_typing=True,
                reserve_space_for_menu=8,
                key_bindings=key_bindings,
                bottom_toolbar=HTML(
                    "<toolbar> Tab补全  |  /help命令  |  /clear清空行  |  /exit退出 </toolbar>"
                ),
                style=STYLE,
            ).strip()
        except KeyboardInterrupt:
            print("\n已取消本次输入。")
            continue
        except EOFError:
            print("\nBye.")
            break

        if not user_input:
            continue

        if user_input.startswith("/"):
            should_continue = handle_command(user_input)
            if not should_continue:
                break
            continue

        try:
            agent_run(user_input)
        except Exception as exc:
            print(f"调用模型失败: {exc}")


if __name__ == "__main__":
    main()
