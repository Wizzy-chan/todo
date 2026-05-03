from datetime import datetime
from os import environ
import pathlib
import sys
from typing import List, Optional, TypeVar
import sqlite3
from xdg_base_dirs import xdg_data_home

from todo.ANSI import ANSI, print_with_format

DEBUG = bool("VIRTUAL_ENV" in environ)
T = TypeVar("T")


class Task:
    @staticmethod
    def initialise_table(conn: sqlite3.Connection):
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY,
                name TEXT,
                description TEXT,
                completedat DATETIME
            )
            """)

    @staticmethod
    def get(conn: sqlite3.Connection, id: str) -> Optional["Task"]:
        result = conn.execute("SELECT * FROM tasks WHERE id = ?", id)
        return Task(conn, *result.fetchone())

    @staticmethod
    def get_all(conn: sqlite3.Connection) -> List["Task"]:
        result = conn.execute("SELECT * FROM tasks")
        return [Task(conn, *row) for row in result.fetchall()]

    @staticmethod
    def new(conn: sqlite3.Connection, name: str, description: str) -> "Task":
        result = conn.execute(
            "INSERT INTO tasks(name, description) VALUES (?, ?) RETURNING *",
            (name, description),
        )
        task = Task(conn, *result.fetchone())
        conn.commit()
        return task

    def __init__(
        self,
        conn: sqlite3.Connection,
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


def print_task(task: Task):
    print(f"[{task.id}] {task.name}")
    print(f"    {task.description}")
    if task.completedat:
        print(f"    Completed at {task.completedat.strftime('%x %X')}")


def add_task(conn: sqlite3.Connection):
    print("Creating a new task")
    name = input("Name: ")
    description = input("Description: ")
    task = Task.new(conn, name, description)
    print(f"Successfully created task {name} with id {task.id}")


def list_tasks(conn: sqlite3.Connection):
    tasks = Task.get_all(conn)
    for task in tasks:
        print_task(task)


def complete_task(conn: sqlite3.Connection, id: str):
    task = Task.get(conn, id)
    if not task:
        print_err(f"Error: No task with id {id}")
        return

    task.completedat = datetime.now()
    task.save()
    print(f"Successfully marked task {task.name} as completed")


def delete_task(conn: sqlite3.Connection, id: str):
    task = Task.get(conn, id)
    if not task:
        print_err(f"Error: No task with id {id}")
        return

    task.delete()
    print(f"Successfully deleted task {task.name}")


def print_usage(program_name: str):
    print("Usage:")
    print(f"\t{program_name} [command]")
    print()
    print("Commands:")
    print("\tadd      - Add a task")
    print("\tcomplete - Complete a task")
    print("\tdelete   - Delete a task")
    print("\thelp     - Print this message")
    print("\tlist     - Lists all saved tasks")


def shift(arr: List[T]) -> Optional[T]:
    if len(arr) == 0:
        return None
    return arr.pop(0)


def print_err(string: str):
    print_with_format(ANSI.RED, string)


def main() -> int:
    args = sys.argv
    program_name = shift(args)
    assert program_name is not None  # argv[0] is always present

    cmd = shift(args) or "list"

    db_path = (pathlib.Path.cwd() if DEBUG else xdg_data_home()) / "tasks.db"
    with sqlite3.connect(db_path) as conn:
        Task.initialise_table(conn)
        if cmd == "add":
            add_task(conn)
        elif cmd == "complete":
            id = shift(args)
            if not id:
                print_err("Error: complete command requires id")
                return 1
            complete_task(conn, id)
        elif cmd == "delete":
            id = shift(args)
            if not id:
                print_err("Error: delete command requires id")
                return 1
            delete_task(conn, id)
        elif cmd == "help":
            print_usage(program_name)
        elif cmd == "list":
            list_tasks(conn)
        else:
            print_with_format(ANSI.RED, f"Error: Unknown command {cmd}")
            print_usage(program_name)

    return 0
