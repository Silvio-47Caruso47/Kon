# Эмулятор оболочки ОС

Эмулятор командной строки UNIX-подобной ОС с графическим интерфейсом.
Реализован на Python с использованием библиотеки Tkinter.

## Общее описание

Программа представляет собой REPL (Read-Eval-Print Loop) —
цикл «прочитай → выполни → покажи». Пользователь вводит команду,
программа её разбирает на имя и аргументы и выполняет.

Реализованные команды:

- `ls` — выводит содержимое папки.
- `cd` — переходит в другую папку.
- `exit` — закрывает приложение.

Дополнительные возможности:

- Приём параметров командной строки (`--vfs`, `--log`, `--script`).
- Логирование всех команд в XML-файл.
- Выполнение стартового скрипта при запуске.
- Загрузка виртуальной файловой системы (VFS) из XML.
- Вывод сообщения из файла `motd` при старте.

## Виртуальная файловая система (VFS)

VFS загружается из XML-файла и хранится в памяти программы.
Изменения VFS не сохраняются на диск.

Формат VFS:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<vfs>
  <dir name="/">
    <file name="motd">
      <content>Добро пожаловать!</content>
    </file>
    <dir name="home">
      <file name="user.txt">
        <content>Данные</content>
      </file>
    </dir>
  </dir>
</vfs>
```

Если в корне VFS есть файл `motd`, его содержимое выводится
в начале работы.

## Описание функций и настроек

**`parse_command(line)`** — разбирает строку на команду и аргументы.

**`run_command(command, args, vfs)`** — выполняет команду.

**`parse_args()`** — разбирает параметры командной строки.

**`log_event(file_path, command, error)`** — пишет событие в XML-лог.

**`xml_to_dict(element)`** — превращает XML-элемент в словарь.

**`load_vfs(path)`** — загружает VFS из XML-файла.

**`get_motd(vfs)`** — ищет файл motd в корне VFS.

**`get_node(vfs, path)`** — ищет папку или файл по пути.

**`run_script(path, output_field, root, vfs)`** — выполняет стартовый скрипт.

**`main(log_path, script_path, vfs_path)`** — создаёт окно.

### Параметры командной строки

- `--vfs` — путь к файлу VFS.
- `--log` — путь к лог-файлу.
- `--script` — путь к стартовому скрипту.

### Настройки окна

- Заголовок: `Эмулятор - [username@hostname]`.
- Размер: 700x500.
- Поле вывода: 20 строк, 80 символов.
- Поле ввода: 80 символов.

## Команды для сборки и запуска

Требуется Python 3.10+.

### Запуск без параметров

```
python src/main.py
```

### Запуск с VFS

```
python src/main.py --vfs vfs_files.xml
```

### Запуск с VFS и скриптом

```
python src/main.py --vfs vfs_deep.xml --script scripts/start.txt
```

### Запуск через .bat

- `run.bat` — обычный запуск.
- `run_vfs_minimal.bat` — минимальный VFS.
- `run_vfs_files.bat` — VFS с файлами.
- `run_vfs_deep.bat` — глубокий VFS.

## Примеры использования

### Пример 1. Минимальный VFS

```
python src/main.py --vfs vfs_minimal.xml
```

В окне при вводе `ls` выводится `(пусто)`.

### Пример 2. VFS с файлами

```
python src/main.py --vfs vfs_files.xml
```

При старте — «Добро пожаловать!» (motd).

Команды:

```
> ls
motd  readme.txt  home

> ls home
user.txt

> cd home
> ls
user.txt
```

### Пример 3. Глубокий VFS

```
python src/main.py --vfs vfs_deep.xml --script scripts/start.txt
```

Motd «Глубокий VFS», потом выполняются команды из скрипта.

### Пример 4. Логирование

```
python src/main.py --log test.xml
```

Все команды записываются в `test.xml`:

```xml
<log>
  <event>
    <command>ls</command>
    <timestamp>2026-10-13 14:23:11</timestamp>
    <error />
  </event>
</log>
```
