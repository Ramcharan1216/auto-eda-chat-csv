"""
sandbox_executor.py
--------------------
This is the safety-critical piece of Week 2. We are about to run Python
code that an LLM wrote, based on a user's question, against real data.
That is NOT safe to run with plain exec() -- an LLM could (accidentally
or via a crafted question) generate code that reads files, imports os,
or hangs forever.

Two layers of defense:
  1. STATIC: walk the code's AST before running it at all, and reject
     anything that imports modules, touches dunder attributes, or calls
     known-dangerous builtins (open, eval, exec, __import__, etc).
  2. RUNTIME: execute in a restricted namespace that doesn't even
     HAVE those builtins available, with a timeout so a slow/hanging
     computation can't block the app forever.

Neither layer alone is bulletproof (that's true of sandboxing arbitrary
Python in general -- CPython was never designed to be sandboxed). For a
resume project this is a strong, well-reasoned defense-in-depth approach,
and the honest limitation is worth stating explicitly in your README:
true isolation would mean running generated code in a separate process
or container, not just a restricted exec() in-process.
"""

import ast
import concurrent.futures
import math
import pandas as pd
import numpy as np


class UnsafeCodeError(Exception):
    """Raised when generated code fails the static safety check."""
    pass


class ExecutionError(Exception):
    """Raised when generated code fails or times out at runtime."""
    pass


BLOCKED_NAMES = {
    "os", "sys", "subprocess", "shutil", "socket", "requests", "urllib",
    "importlib", "pathlib", "pickle", "shelve", "ctypes", "multiprocessing",
    "open", "exec", "eval", "compile", "__import__", "input",
    "globals", "locals", "vars", "getattr", "setattr", "delattr",
    "breakpoint", "exit", "quit", "help",
}


def _is_dunder(name: str) -> bool:
    return name.startswith("__") and name.endswith("__")


def validate_code(code: str) -> None:
    """
    Raises UnsafeCodeError if the code does anything outside the
    "compute something from df using pandas/numpy" contract.
    Returns None (i.e. does nothing) if the code looks safe.
    """
    try:
        tree = ast.parse(code, mode="exec")
    except SyntaxError as e:
        raise UnsafeCodeError(f"Generated code is not valid Python: {e}")

    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            raise UnsafeCodeError("Generated code attempted an import, which is not allowed.")

        if isinstance(node, ast.Name) and node.id in BLOCKED_NAMES:
            raise UnsafeCodeError(f"Generated code referenced a blocked name: '{node.id}'.")

        if isinstance(node, ast.Attribute):
            if _is_dunder(node.attr):
                raise UnsafeCodeError(f"Generated code accessed a dunder attribute: '{node.attr}'.")
            if node.attr in BLOCKED_NAMES:
                raise UnsafeCodeError(f"Generated code accessed a blocked attribute: '{node.attr}'.")

        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in BLOCKED_NAMES:
                raise UnsafeCodeError(f"Generated code called a blocked function: '{node.func.id}'.")


def _safe_builtins() -> dict:
    """A deliberately small allowlist of builtins -- everything else is
    simply absent from the execution namespace, so even if validate_code
    somehow missed something, most dangerous calls would raise NameError."""
    names = [
        "len", "range", "abs", "round", "min", "max", "sum", "sorted",
        "list", "dict", "set", "tuple", "str", "int", "float", "bool",
        "enumerate", "zip", "map", "filter", "print", "isinstance",
        "True", "False", "None",
    ]
    return {name: __builtins__[name] if isinstance(__builtins__, dict) else getattr(__builtins__, name)
            for name in names}


def _run(code: str, df: pd.DataFrame) -> dict:
    """Actually exec the code in a restricted namespace. Runs in a worker
    thread so the caller can enforce a timeout around it."""
    local_ns = {"df": df, "pd": pd, "np": np, "math": math}
    global_ns = {"__builtins__": _safe_builtins()}
    exec(code, global_ns, local_ns)
    if "result" not in local_ns:
        raise ExecutionError(
            "Generated code ran but did not set a variable named 'result'."
        )
    return local_ns["result"]


def execute_safely(code: str, df: pd.DataFrame, timeout_seconds: int = 8):
    """
    Validates then executes LLM-generated code against `df`.
    Returns the value of the `result` variable the code was instructed to set.
    Raises UnsafeCodeError (failed static check) or ExecutionError
    (raised an exception, or exceeded timeout_seconds).
    """
    validate_code(code)

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(_run, code, df)
        try:
            return future.result(timeout=timeout_seconds)
        except concurrent.futures.TimeoutError:
            raise ExecutionError(f"Code did not finish within {timeout_seconds} seconds.")
        except Exception as e:
            raise ExecutionError(f"{type(e).__name__}: {e}")


if __name__ == "__main__":
    df = pd.DataFrame({"age": [22, 38, 26, 35, 40], "fare": [7.25, 71.28, 7.92, 53.1, 8.05]})

    print("-- safe code --")
    safe_code = "result = df['age'].mean()"
    print(execute_safely(safe_code, df))

    print("-- safe groupby code --")
    safe_code2 = "result = df.groupby(df['age'] > 30)['fare'].mean()"
    print(execute_safely(safe_code2, df))

    unsafe_examples = [
        "import os\nresult = os.listdir('.')",
        "result = open('secrets.txt').read()",
        "result = eval('1+1')",
        "result = ().__class__.__bases__[0].__subclasses__()",
        "result = exec('x=1')",
    ]
    for i, bad_code in enumerate(unsafe_examples, 1):
        try:
            execute_safely(bad_code, df)
            print(f"-- unsafe example {i}: FAILED TO BLOCK (bug!) --")
        except UnsafeCodeError as e:
            print(f"-- unsafe example {i}: correctly blocked -- {e}")
