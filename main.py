
from pathlib import Path
import shutil
import unicodedata
import warnings

from prompt_toolkit import PromptSession, print_formatted_text
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.shortcuts import CompleteStyle, clear
from agent.react_agent import agent_run
from chat.session_logger import ChatSessionLogger
from config import STYLE

try:
    from jwt import InsecureKeyLengthWarning

    warnings.filterwarnings("ignore", category=InsecureKeyLengthWarning)
except Exception:
    pass

COMMANDS = {
    "/help": "显示命令列表",
    "/new": "新建会话",
    "/clear": "清空屏幕",
    "/exit": "退出程序",
}



def _text_width(text: str) -> int:
    width = 0
    for char in text:
        width += 2 if unicodedata.east_asian_width(char) in {"F", "W"} else 1
    return width


def _truncate_to_width(text: str, width: int) -> str:
    result = []
    current = 0
    for char in text:
        char_width = 2 if unicodedata.east_asian_width(char) in {"F", "W"} else 1
        if current + char_width > width:
            break
        result.append(char)
        current += char_width
    return "".join(result)


def _pad_line(text: str, width: int) -> str:
    raw = _truncate_to_width(text, width)
    return raw + (" " * max(0, width - _text_width(raw)))


def _center_line(text: str, width: int) -> str:
    raw = _truncate_to_width(text, width)
    space = max(0, width - _text_width(raw))
    left = space // 2
    right = space - left
    return (" " * left) + raw + (" " * right)


def _render_box_line(text: str, width: int, *, centered: bool = False) -> str:
    formatter = _center_line if centered else _pad_line
    return f"| {formatter(text, width - 4)} |"


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


def print_welcome(session_logger: ChatSessionLogger):
    terminal_width = shutil.get_terminal_size((88, 24)).columns
    box_width = max(56, min(96, terminal_width - 2))
    border = "+" + ("-" * (box_width - 2)) + "+"

    sections = [
        ("welcome.border", border),
        ("welcome.title", _render_box_line("AIDE CLI", box_width, centered=True)),
        (
            "welcome.subtitle",
            _render_box_line("Your terminal copilot for chat, tools, and memory.", box_width, centered=True),
        ),
        ("welcome.border", border),
        ("welcome.section", _render_box_line("快速开始", box_width)),
        ("welcome.body", _render_box_line("1) 输入普通文本，直接开始对话。", box_width)),
        ("welcome.body", _render_box_line("2) 输入 /help 查看全部命令。", box_width)),
        ("welcome.body", _render_box_line("3) 输入 /new 开启新的会话。", box_width)),
        ("welcome.border", border),
        ("welcome.section", _render_box_line("当前会话", box_width)),
        ("welcome.body", _render_box_line(f"Session ID: {session_logger.session.session_id}", box_width)),
        ("welcome.border", border)
    ]


    print()
    for style_name, line in sections:
        print_formatted_text(HTML(f"<{style_name}>{line}</{style_name}>"), style=STYLE)
    print()


def print_help():
    print("\n可用命令")
    for cmd, desc in COMMANDS.items():
        print(f"  {cmd:<8} {desc}")
    print()


def handle_command(message: str, session_logger: ChatSessionLogger) -> bool:
    if message == "/exit":
        print("Bye.")
        return False

    if message == "/help":
        print_help()
        return True

    if message == "/new":
        session_logger.new_session()
        print_formatted_text(HTML("<output.ok>已创建新会话。</output.ok>"), style=STYLE)
        print_formatted_text(
            HTML(
                f"<output.info>Session ID: {session_logger.session.session_id}  |  日志文件: "
                f"chat/{session_logger.session.file_path.name}</output.info>"
            ),
            style=STYLE,
        )
        print_welcome(session_logger)
        return True

    if message == "/clear":
        clear()
        print_welcome(session_logger)
        return True

    print(f"未知命令: {message}，输入 /help 查看可用命令。")
    return True


def main():
    session_logger = ChatSessionLogger(Path("chat"))
    print_welcome(session_logger)

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
                    "<toolbar> Tab补全  |  /help命令  |  /new新会话  |  /clear清空行  |  /exit退出 </toolbar>"
                ),
                style=STYLE,
            ).strip()
        except KeyboardInterrupt:
            continue
        except EOFError:
            print("\nBye.")
            break

        if not user_input:
            continue

        if user_input.startswith("/"):
            should_continue = handle_command(user_input, session_logger)
            if not should_continue:
                break
            continue

        try:
            assistant_output = agent_run(user_input)
            session_logger.record_turn(user_input, assistant_output)
        except Exception as exc:
            print(f"调用模型失败: {exc}")
            session_logger.record_error(user_input, str(exc))


if __name__ == "__main__":
    main()
