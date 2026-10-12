import tkinter as tk
import getpass
import socket
import argparse
import xml.etree.ElementTree as et
from datetime import datetime

def parse_command(line):
    parts = line.split()
    if not parts:
        return "", []
    command = parts[0]
    args = parts[1:]
    return command, args

def run_command(command, args):
    if command == "exit":
        return "Выход.", True
    elif command == "ls":
        return "ls\n" + " ".join(args), False
    elif command == "cd":
        return "cd\n" + " ".join(args), False
    else:
        return "Ошибка: неизвестная команда '" + command + "'", False

def parse_args():
    parser = argparse.ArgumentParser(
        description="Эмулятор оболочки ОС")
    parser.add_argument(
        "--vfs",
        default=None,
        help="Путь к файлу виртуальной файловой системы")
    parser.add_argument(
        "--log",
        default=None,
        help="Путь к лог-файлу (XML)")
    parser.add_argument(
        "--script",
        default=None,
        help="Путь к стартовому скрипту")
    return parser.parse_args()

def log_event(file_path, command, error=""):
    if not file_path:
        return
    try:
        tree = et.parse(file_path)
        root = tree.getroot()
    except (FileNotFoundError, et.ParseError):
        root = et.Element("log")
        tree = et.ElementTree(root)
    event = et.SubElement(root, "event")
    cmd_elem = et.SubElement(event, "command")
    cmd_elem.text = command
    time_elem = et.SubElement(event, "timestamp")
    time_elem.text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    err_elem = et.SubElement(event, "error")
    err_elem.text = error
    tree.write(file_path, encoding="UTF-8", xml_declaration=True)
    
def xml_to_dict(element):
    name = element.get("name", "")
    tag = element.tag
    if tag == "file":
        content_elem = element.find("content")
        content = content_elem.text if content_elem is not None else ""
        return {
            "type": "file",
            "content": content}
    elif tag == "dir":
        children = {}
        for child in element:
            child_dict = xml_to_dict(child)
            children[child.get("name", "")] = child_dict
        return {
            "type": "dir",
            "name": name,
            "children": children}
    return None

def load_vfs(path):
    if not path:
        return None
    try:
        tree = et.parse(path)
        root = tree.getroot()
    except FileNotFoundError:
        print("Ошибка: файл VFS не найден:", path)
        return None
    except et.ParseError:
        print("Ошибка: неверный формат VFS:", path)
        return None
    root_dir = root.find("dir")
    if root_dir is None:
        print("Ошибка: неверная структура VFS (нет корневой папки)")
        return None
    return xml_to_dict(root_dir)


def get_motd(vfs):
    if not vfs:
        return None
    if vfs.get("type") != "dir":
        return None
    children = vfs.get("children", {})
    motd = children.get("motd")
    if motd and motd.get("type") == "file":
        return motd.get("content")
    return None

def run_script(path, output_field, root):
    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        output_field.insert(tk.END, "Ошибка: файл скрипта не найден\n")
        return
    for line in lines:
        line = line.strip()
        if not line:
            continue
        output_field.insert(tk.END, "> " + line + "\n")
        command, args = parse_command(line)
        result, should_exit = run_command(command, args)
        output_field.insert(tk.END, result + "\n\n")
        output_field.see(tk.END)
        if result.startswith("Ошибка"):
            output_field.insert(
                tk.END,
                "=== Скрипт остановлен: " + result + " ===\n\n")
            output_field.see(tk.END)
            return
        if should_exit:
            root.destroy()
            return

def main(log_path=None, script_path=None, vfs_path=None):
    user = getpass.getuser()
    host = socket.gethostname()
    vfs = load_vfs(vfs_path)
    root = tk.Tk()
    root.title("Эмулятор - [" + user + "@" + host + "]")
    root.geometry("700x500")
    output_field = tk.Text(root, height=20, width=80)
    output_field.pack(padx=10, pady=10)
    input_field = tk.Entry(root, width=80)
    input_field.pack(padx=10, pady=5)
    motd = get_motd(vfs)
    if motd:
        output_field.insert(tk.END, motd + "\n\n")
    output_field.insert(tk.END, "Добро пожаловать!\n")
    output_field.insert(tk.END, "Доступные команды: ls, cd, exit\n")
    output_field.insert(tk.END, "\n")
    def on_run():
        """Срабатывает при нажатии кнопки или Enter."""
        line = input_field.get()
        input_field.delete(0, tk.END)
        if not line.strip():
            return
        command, args = parse_command(line)
        result, should_exit = run_command(command, args)
        error_text = ""
        if result.startswith("Ошибка"):
            error_text = result
        log_event(log_path, line, error_text)
        output_field.insert(tk.END, "> " + line + "\n")
        output_field.insert(tk.END, result + "\n\n")
        output_field.see(tk.END)
        if should_exit:
            root.destroy()
    run_button = tk.Button(root, text="Выполнить", command=on_run)
    run_button.pack(pady=5)
    input_field.bind("<Return>", lambda event: on_run())
    input_field.focus()
    if script_path:
        run_script(script_path, output_field, root)
    root.mainloop()

if __name__ == "__main__":
    args = parse_args()
    print("=== Параметры запуска ===")
    print("VFS:", args.vfs)
    print("Лог:", args.log)
    print("Скрипт:", args.script)
    print("=========================")
    main(args.log, args.script, args.vfs)
