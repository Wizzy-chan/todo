from datetime import datetime
from os import environ
from pathlib import Path
from sys import argv
from typing import Callable, List, NoReturn, Optional, TypeVar
from sqlite3 import Connection, connect

from todo.ANSI import ANSI, print_with_format

DEBUG = bool("VIRTUAL_ENV" in environ)
T = TypeVar("T")


class Task:
    @staticmethod
    def initialise_table(conn: Connection):
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY,
                name TEXT,
                description TEXT,
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
    def new(conn: Connection, name: str, description: str) -> "Task":
        result = conn.execute(
            "INSERT INTO tasks(name, description) VALUES (?, ?) RETURNING *",
            (name, description),
        )
        task = Task(conn, *result.fetchone())
        conn.commit()
        return task

    def __init__(
        self,
        conn: Connection,
        id: str,
        name: str,
        description: str,
        completedat: Optional[int] = None,
    ) -> None:
        self.conn = conn
        self.id = id
        self.name = name
        self.description = description
        self.completedat = datetime.fromtimestamp(completedat) if completedat else None

    def completed(self) -> bool:
        return bool(self.completedat)

    def save(self) -> None:
        self.conn.execute(
            "UPDATE tasks SET name = ?, description = ?, completedat = ? WHERE id = ?",
            (
                self.name,
                self.description,
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
            + f"{repr(self.name)}, "
            + f"{repr(self.description)}, "
            + f"{self.completedat.timestamp() if self.completedat else None})"
        )


def shift(arr: List[T]) -> Optional[T]:
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


# TODO: Callable[[List[str]], None] is kind of annoying.
#       Maybe we can use the inspect module to work out
#       arity (min/max) and automatically split the input
#       Also maybe the function could return an exit code.
def command(function: Callable[[List[str]], None]) -> Callable[[List[str]], None]:
    commands[function.__name__.replace("_", "-")] = function
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
    print(f"[{task.id}] {task.name}")
    print(f"    {task.description}")
    if task.completedat:
        print(f"    Completed at {task.completedat.strftime('%x %X')}")


@command
def add(args: List[str]) -> None:
    """Create a new task"""
    if len(args) != 0:
        # TODO: Maybe we can add a way to make a task from arguments
        error("The add command does not take any arguments")
    conn = connect_to_db()
    print("Creating a new task")
    name = input("Name: ")
    description = input("Description: ")
    task = Task.new(conn, name, description)
    print(f"Successfully created task '{name}' with id {task.id}")


@command
def show(args: List[str]) -> None:
    """Show uncompleted tasks, this is the default behaviour if no command is provided"""
    if len(args) != 0:
        error("The list command does not take any arguments")
    conn = connect_to_db()
    tasks = Task.get_uncompleted(conn)
    for task in tasks:
        print_task(task)


@command
def show_all(args: List[str]) -> None:
    """Show all tasks"""
    if len(args) != 0:
        error("The list-all command does not take any arguments")
    conn = connect_to_db()
    tasks = Task.get_all(conn)
    for task in tasks:
        print_task(task)


@command
def mark(args: List[str]) -> None:
    """Mark a task as completed"""
    if len(args) != 1:
        error("The mark command takes in exactly one argument: id")
    id = args[0]
    conn = connect_to_db()
    task = Task.get(conn, id) or error(f"No task with id {id}")
    task.completedat = datetime.now()
    task.save()
    print(f"Successfully marked task '{task.name}' as completed")


@command
def unmark(args: List[str]) -> None:
    """Unmark a task as completed"""
    if len(args) != 1:
        error("The unmark command takes in exactly one argument: id")
    id = args[0]
    conn = connect_to_db()
    task = Task.get(conn, id) or error(f"No task with id {id}")
    task.completedat = None
    task.save()
    print(f"Successfully unmarked task '{task.name}'")
    pass


@command
def delete(args: List[str]) -> None:
    """Delete a task"""
    if len(args) != 1:
        error("The delete command takes exactly one argument: id")
    id = args[0]
    conn = connect_to_db()
    task = Task.get(conn, id) or error(f"No task with id {id}")
    task.delete()
    print(f"Successfully deleted task {task.name}")


def main():
    args = argv[1:]
    command = shift(args) or "show"
    command_fn = commands.get(command)

    if not command_fn:
        print("Usage:")
        print(f"\t{argv[0]} [command]")
        print()
        print("Commands:")
        longest = max(len(name) for name in commands.keys())
        for name, function in commands.items():
            print(f"\t{name:<{longest}} - {function.__doc__}")
        print(f"\t{'help':<{longest}} - Print this help message")
        if command != "help":
            error(f"Unknown command {command}")
        exit(0)

    command_fn(args)
