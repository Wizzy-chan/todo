from datetime import datetime
from functools import wraps
from inspect import signature
from os import environ
from pathlib import Path
from sqlite3 import Connection, connect
from sys import argv
from typing import List, NoReturn, Optional

from todo.ANSI import ANSI, print_with_format

DEBUG = bool("TODO_DEBUG" in environ)


class Task:
    @staticmethod
    def initialise_table(conn: Connection):
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY,
                content TEXT,
                completedat DATETIME
            )
            """)

    @staticmethod
    def get(conn: Connection, id: str) -> Optional["Task"]:
        result = conn.execute("SELECT * FROM tasks WHERE id = ?", id)
        return Task(conn, *result.fetchone())

    @staticmethod
    def get_all(conn: Connection) -> List["Task"]:
        result = conn.execute("SELECT * FROM tasks")
        return [Task(conn, *row) for row in result.fetchall()]

    @staticmethod
    def get_uncompleted(conn: Connection) -> List["Task"]:
        result = conn.execute("SELECT * FROM tasks WHERE completedat IS NULL")
        return [Task(conn, *row) for row in result.fetchall()]

    @staticmethod
    def new(conn: Connection, content: str) -> "Task":
        result = conn.execute(
            "INSERT INTO tasks(content) VALUES (?) RETURNING *",
            (content,),
        )
        task = Task(conn, *result.fetchone())
        conn.commit()
        return task

    def __init__(
        self,
        conn: Connection,
        id: str,
        content: str,
        completedat: Optional[int] = None,
    ) -> None:
        self.conn = conn
        self.id = id
        self.content = content
        self.completedat = datetime.fromtimestamp(completedat) if completedat else None

    def completed(self) -> bool:
        return bool(self.completedat)

    def save(self) -> None:
        self.conn.execute(
            "UPDATE tasks SET content = ?, completedat = ? WHERE id = ?",
            (
                self.content,
                self.completedat.timestamp() if self.completedat else None,
                self.id,
            ),
        )
        self.conn.commit()

    def delete(self) -> None:
        self.conn.execute("DELETE FROM tasks WHERE id = ?", (self.id,))
        self.conn.commit()

    def __repr__(self) -> str:
        return (
            f"Task({repr(self.id)}, "
            + f"{repr(self.content)}, "
            + f"{self.completedat.timestamp() if self.completedat else None})"
        )


def shift[T](arr: List[T]) -> Optional[T]:
    if len(arr) == 0:
        return None
    return arr.pop(0)


def error(string: str, exit_code: int = 1) -> NoReturn:
    print_with_format(ANSI.RED, "Error: " + string)
    exit(exit_code)


def xdg_data_home() -> Path:
    default_path = Path.home() / ".local/share"
    xdg_data_home = environ.get("XDG_DATA_HOME")
    if not xdg_data_home:
        return default_path
    xdg_data_home_path = Path(xdg_data_home)
    if not xdg_data_home_path.is_absolute():
        return default_path
    return xdg_data_home_path


commands = {}


def command(function):
    """
    Registers a command that can be run from the terminal
    `function` MUST accept a fixed number of non-optional string arguments.
    """
    command_name = function.__name__.replace("_", "-")

    @wraps(function)
    def wrapped_function(command_line: List[str]):
        sig = signature(function)
        arity = len(sig.parameters)
        if len(command_line) != arity:
            error(
                f"Command '{command_name}' accepts {arity} arguments but {len(command_line)} were provided"
            )

        args = []
        for i in range(arity):
            args.append(command_line[i])

        function(*args)

    commands[command_name] = wrapped_function
    return function


def connect_to_db() -> Connection:
    if DEBUG:
        db_path = Path.cwd() / "tasks.db"
    else:
        db_path = xdg_data_home() / "tasks.db"

    conn = connect(db_path)
    Task.initialise_table(conn)
    return conn


def print_task(task: Task) -> None:
    print(f"[{task.id}] {task.content}")
    if task.completedat:
        print(f"    Completed at {task.completedat.strftime('%x %X')}")


@command
def add() -> None:
    """Create a new task"""
    # TODO: Maybe we can add a way to make a task from arguments
    conn = connect_to_db()
    print("Creating a new task")
    name = input("Name: ")
    task = Task.new(conn, name)
    print(f"Successfully created task '{name}' with id {task.id}")


@command
def show() -> None:
    """Show uncompleted tasks, this is the default behaviour if no command is provided"""
    conn = connect_to_db()
    tasks = Task.get_uncompleted(conn)
    for task in tasks:
        print_task(task)


@command
def show_all() -> None:
    """Show all tasks"""
    conn = connect_to_db()
    tasks = Task.get_all(conn)
    for task in tasks:
        print_task(task)


@command
def mark(id: str) -> None:
    """Mark a task as completed"""
    conn = connect_to_db()
    task = Task.get(conn, id) or error(f"No task with id {id}")
    task.completedat = datetime.now()
    task.save()
    print(f"Successfully marked task '{task.content}' as completed")


@command
def unmark(id: str) -> None:
    """Unmark a task as completed"""
    conn = connect_to_db()
    task = Task.get(conn, id) or error(f"No task with id {id}")
    task.completedat = None
    task.save()
    print(f"Successfully unmarked task '{task.content}'")
    pass


@command
def delete(id: str) -> None:
    """Delete a task"""
    conn = connect_to_db()
    task = Task.get(conn, id) or error(f"No task with id {id}")
    task.delete()
    print(f"Successfully deleted task {task.content}")


@command
def help() -> None:
    """Print this help message"""
    print("Usage:")
    print(f"\t{argv[0]} [command]")
    print()
    print("Commands:")
    longest = max(len(name) for name in commands.keys())
    for name, function in commands.items():
        print(f"\t{name:<{longest}} - {function.__doc__}")


def main():
    args = argv[1:]
    command = shift(args) or "show"
    command_fn = commands.get(command)

    if not command_fn:
        help()
        error(f"Unknown command {command}")

    command_fn(args)
