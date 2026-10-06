import tkinter as tk
import getpass
import socket
import argparse


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
        description="Эмулятор оболочки ОС"
    )
    parser.add_argument(
        "--vfs",
        default=None,
        help="Путь к файлу виртуальной файловой системы"
    )
    parser.add_argument(
        "--log",
        default=None,
        help="Путь к лог-файлу (XML)"
    )
    parser.add_argument(
        "--script",
        default=None,
        help="Путь к стартовому скрипту"
    )
    return parser.parse_args()


def main():
    user = getpass.getuser()
    host = socket.gethostname()

    root = tk.Tk()
    root.title("Эмулятор - [" + user + "@" + host + "]")
    root.geometry("700x500")

    output_1 = tk.Text(root, height=20, width=80)
    output_1.pack(padx=10, pady=10)

    input_1 = tk.Entry(root, width=80)
    input_1.pack(padx=10, pady=5)

    output_1.insert(tk.END, "Добро пожаловать!\n")
    output_1.insert(tk.END, "Доступные команды: ls, cd, exit\n")
    output_1.insert(tk.END, "\n")

    def on_run():
        line = input_1.get()
        input_1.delete(0, tk.END)

        if not line.strip():
            return

        command, args = parse_command(line)
        result, should_exit = run_command(command, args)

        output_1.insert(tk.END, "> " + line + "\n")
        output_1.insert(tk.END, result + "\n\n")
        output_1.see(tk.END)

        if should_exit:
            root.destroy()

    run_1 = tk.Button(root, text="Выполнить", command=on_run)
    run_1.pack(pady=5)

    input_1.bind("<Return>", lambda event: on_run())

    input_1.focus()

    root.mainloop()


if __name__ == "__main__":
    args = parse_args()
    print("=== Параметры запуска ===")
    print("VFS:", args.vfs)
    print("Лог:", args.log)
    print("Скрипт:", args.script)
    print("=========================")
    main()
