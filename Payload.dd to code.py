import pyautogui
import time
import os
import re

# Map Duckyscript keys to pyautogui
KEY_MAP = {
    "ENTER": "enter",
    "RETURN": "enter",
    "TAB": "tab",
    "SPACE": "space",
    "ESCAPE": "esc",
    "ESC": "esc",
    "DELETE": "delete",
    "DEL": "delete",
    "BACKSPACE": "backspace",
    "CAPSLOCK": "capslock",
    "HOME": "home",
    "END": "end",
    "UPARROW": "up",
    "DOWNARROW": "down",
    "LEFTARROW": "left",
    "RIGHTARROW": "right",
    "PRINTSCREEN": "printscreen",
    "PAUSE": "pause",
    "BREAK": "pause",
    "MENU": "menu",
    "APPLICATION": "menu",
    "GUI": "win",
    "WINDOWS": "win",
    "COMMAND": "command",
    "CTRL": "ctrl",
    "CONTROL": "ctrl",
    "SHIFT": "shift",
    "ALT": "alt",
}

def dd_to_python(dd_file, py_file):
    with open(dd_file, "r") as f:
        lines = [line.rstrip() for line in f.readlines()]

    py_lines = [
        "import pyautogui",
        "import time",
        "import os",
        "",
        "# Focus target window before running",
        "time.sleep(3)",
        ""
    ]

    i = 0
    indent_stack = [0]  # track nested REPEAT indentation

    def write_line(cmd, indent):
        py_lines.append("    " * indent + cmd)

    def process_line(line, indent):
        line = line.strip()
        if not line or line.startswith("REM"):
            write_line(f"# {line}" if line else "", indent)
            return None

        # Delay
        if line.startswith("DELAY "):
            ms = int(re.findall(r"\d+", line)[0])
            cmd = f"time.sleep({ms}/1000)"
            write_line(cmd, indent)
            return cmd

        # STRING with optional ENTER
        if line.startswith("STRING "):
            text = line[len("STRING "):]
            cmd = f"pyautogui.write({repr(text)})"
            write_line(cmd, indent)
            return cmd

        # Single key
        if line.upper() in KEY_MAP:
            key = KEY_MAP[line.upper()]
            cmd = f"pyautogui.press('{key}')"
            write_line(cmd, indent)
            return cmd

        # Key combos
        combo_keys = line.split()
        mapped_keys = [KEY_MAP.get(k.upper(), k.lower()) for k in combo_keys]
        if len(mapped_keys) > 1:
            cmd = f"pyautogui.hotkey({', '.join([repr(k) for k in mapped_keys])})"
            write_line(cmd, indent)
            return cmd

        # System commands
        if line.upper() == "REBOOT":
            cmd = "os.system('shutdown -r -t 0')"
            write_line(cmd, indent)
            return cmd
        if line.upper() == "SHUTDOWN":
            cmd = "os.system('shutdown -s -t 0')"
            write_line(cmd, indent)
            return cmd

        # Layouts
        if line.startswith("LAYOUT "):
            write_line(f"# {line}", indent)
            return None

        write_line(f"# Unknown command: {line}", indent)
        return None

    while i < len(lines):
        line = lines[i].strip()
        # Multi-line REPEAT
        if line.startswith("REPEAT "):
            count = int(re.findall(r"\d+", line)[0])
            i += 1
            block_lines = []
            # Collect all lines under this REPEAT until next REPEAT at same level or EOF
            while i < len(lines) and not lines[i].strip().startswith("REPEAT "):
                cmd = process_line(lines[i], indent=0)
                if cmd:
                    block_lines.append(cmd)
                i += 1
            # Write the repeat block
            write_line(f"for _ in range({count}):", indent_stack[-1])
            for cmd in block_lines:
                write_line(cmd, indent_stack[-1]+1)
            continue

        # Normal line
        process_line(line, indent_stack[-1])
        i += 1

    with open(py_file, "w") as f:
        f.write("\n".join(py_lines))
    print(f"Translated {dd_file} → {py_file} successfully!")

# Example usage
dd_to_python("payload.dd", "code.py")
