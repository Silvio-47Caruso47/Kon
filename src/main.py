import tkinter as tk
import getpass
import socket
import argparse
import xml.etree.ElementTree as et
from datetime import datetime

current_path = "/"


def parse_command(line):
    parts = line.split()
    if not parts:
        return "", []
    command = parts[0]
    args = parts[1:]
    return command, args


def get_node(vfs, path):
    if not vfs or not path:
        return None
    parts = path.strip("/").split("/")
    parts = [p for p in parts if p]
    node = vfs
    for part in parts:
        if node.get("type") != "dir":
            return None
        children = node.get("children", {})
        if part not in children:
            return None
        node = children[part]
    return node


def build_tree(node, prefix=""):
    lines = []
    if node.get("type") != "dir":
        return ""
    children = node.get("children", {})
    names = list(children.keys())
    for i, name in enumerate(names):
        is_last = (i == len(names) - 1)
        child = children[name]
        if is_last:
            branch = "└── "
            new_prefix = prefix + "    "
        else:
            branch = "├── "
            new_prefix = prefix + "│   "
        if child.get("type") == "dir":
            lines.append(prefix + branch + name + "/")
            lines.append(build_tree(child, new_prefix))
        else:
            lines.append(prefix + branch + name)
    return "\n".join(lines)


def make_abs_path(name):
    if name.startswith("/"):
        return name
    if current_path == "/":
        return "/" + name
    return current_path + "/" + name


def cmd_ls(vfs, args):
    target = current_path
    if args:
        target = args[0]
    node = get_node(vfs, target)
    if node is None:
        return "Ошибка: папка не найдена", False
    if node.get("type") != "dir":
        return "Ошибка: это не папка", False
    children = node.get("children", {})
    if not children:
        return "(пусто)", False
    names = list(children.keys())
    return "  ".join(names), False


def cmd_cd(vfs, args):
    global current_path
    if not args:
        current_path = "/"
        return "", False
    target = args[0]
    if target == "..":
        parts = current_path.strip("/").split("/")
        parts = [p for p in parts if p]
        if parts:
            parts.pop()
        new_path = "/" + "/".join(parts)
    elif target.startswith("/"):
        new_path = target
    else:
        new_path = make_abs_path(target)
    node = get_node(vfs, new_path)
    if node is None:
        return "Ошибка: папка не найдена", False
    if node.get("type") != "dir":
        return "Ошибка: это не папка", False
    current_path = new_path
    return "", False


def cmd_cat(vfs, args):
    if not args:
        return "Ошибка: укажите файл", False
    target = make_abs_path(args[0])
    node = get_node(vfs, target)
    if node is None:
        return "Ошибка: файл не найден", False
    if node.get("type") != "file":
        return "Ошибка: это не файл", False
    return node.get("content", ""), False


def cmd_tree(vfs, args):
    if vfs is None:
        return "Ошибка: VFS не загружена", False
    if vfs.get("type") != "dir":
        return "Ошибка: VFS не папка", False
    body = build_tree(vfs)
    if not body:
        return "(пусто)", False
    return "/\n" + body, False


def run_command(command, args, vfs):
    if command == "exit":
        return "Выход.", True
    elif command == "ls":
        return cmd_ls(vfs, args)
    elif command == "cd":
        return cmd_cd(vfs, args)
    elif command == "cat":
        return cmd_cat(vfs, args)
    elif command == "tree":
        return cmd_tree(vfs, args)
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


def run_script(path, output_field, root, vfs):
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
        result, should_exit = run_command(command, args, vfs)
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
    output_field.insert(tk.END, "Команды: ls, cd, cat, tree, exit\n")
    output_field.insert(tk.END, "\n")
    def on_run():
        """Срабатывает при нажатии кнопки или Enter."""
        line = input_field.get()
        input_field.delete(0, tk.END)
        if not line.strip():
            return
        command, args = parse_command(line)
        result, should_exit = run_command(command, args, vfs)
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
        run_script(script_path, output_field, root, vfs)
    root.mainloop()


if __name__ == "__main__":
    args = parse_args()
    print("=== Параметры запуска ===")
    print("VFS:", args.vfs)
    print("Лог:", args.log)
    print("Скрипт:", args.script)
    print("=========================")
    main(args.log, args.script, args.vfs)
