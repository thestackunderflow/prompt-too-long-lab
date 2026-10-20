"""A simulated coding-agent session: a system prompt, six tool definitions, then turns where the agent reads real
Python standard-library source files inside the container. Pure and deterministic for a given image."""
import glob, os, random

STDLIB = '/usr/local/lib/python3.12'

SYSTEM = (
    "You are a coding agent working in a Python repository. Use the tools to inspect files, run the tests and make "
    "small, safe edits. Read a file before you change it. Explain each change in one sentence. Never delete files. "
    "When the tests pass, stop and summarise what you changed and why. If a tool fails, read its error message and "
    "try a different approach instead of repeating the same call. Keep edits minimal and keep the existing style."
)


def _tool(name, desc, props, required):
    return {'name': name, 'description': desc,
            'input_schema': {'type': 'object', 'properties': props, 'required': required}}


S = {'type': 'string'}
TOOLS = [
    _tool('read_file', 'Read a text file from the repository and return its full contents.',
          {'path': {**S, 'description': 'Path relative to the repository root.'}}, ['path']),
    _tool('list_dir', 'List the files and folders in a directory.',
          {'path': {**S, 'description': 'Directory path relative to the repository root.'}}, ['path']),
    _tool('grep', 'Search files for a regular expression and return matching lines with file names.',
          {'pattern': {**S, 'description': 'Regular expression.'}, 'path': {**S, 'description': 'Where to search.'}},
          ['pattern']),
    _tool('run_tests', 'Run the test suite (or one test file) and return the output.',
          {'target': {**S, 'description': 'Optional test file or test id.'}}, []),
    _tool('edit_file', 'Replace one exact string in a file with another.',
          {'path': S, 'old': {**S, 'description': 'Exact text to replace.'}, 'new': {**S, 'description': 'Replacement.'}},
          ['path', 'old', 'new']),
    _tool('git_diff', 'Show the uncommitted changes in the repository.', {}, []),
]

TASK = ("The test suite got slow after last week's changes. Find out which module is responsible and fix it. "
        "Start by reading the modules involved.")


def source_files():
    """Real .py files from the standard library, 20-120 KB, in a fixed shuffled order."""
    fs = [f for f in glob.glob(f'{STDLIB}/**/*.py', recursive=True)
          if '/test' not in f and 'site-packages' not in f and 20_000 <= os.path.getsize(f) <= 120_000]
    fs.sort()
    random.Random(153).shuffle(fs)
    return fs


def build(turns, files=None):
    """System + tools + the task, then `turns` (read_file tool_use, tool_result) pairs."""
    files = files or source_files()
    msgs = [{'role': 'user', 'content': TASK}]
    for i in range(turns):
        path = files[i % len(files)]
        rel = os.path.relpath(path, STDLIB)
        tid = f'toolu_{i:04d}'
        msgs.append({'role': 'assistant', 'content': [
            {'type': 'tool_use', 'id': tid, 'name': 'read_file', 'input': {'path': rel}}]})
        msgs.append({'role': 'user', 'content': [
            {'type': 'tool_result', 'tool_use_id': tid, 'content': open(path, encoding='utf8').read()}]})
    return {'system': SYSTEM, 'tools': TOOLS, 'messages': msgs}
