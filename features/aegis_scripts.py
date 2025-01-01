"""
Aegis script interpreter (.aegis files)

Syntax:
  # comment
  $VAR = value
  echo Running step $VAR
  if python --version:
      pip install flask
  end
"""
import re
import os
from pathlib import Path
from colorama import Fore, Style


def run_script(filepath: str, executor) -> bool:
    path = Path(filepath)
    if not path.exists():
        print(Fore.RED + f'[Aegis] Script not found: {filepath}' + Style.RESET_ALL)
        return False

    lines = path.read_text(encoding='utf-8').splitlines()
    _run_block(lines, executor, {})
    return True


def _expand(line: str, env: dict) -> str:
    def _rep(m):
        name = m.group(1)
        return env.get(name, os.environ.get(name, m.group(0)))
    return re.sub(r'\$([A-Za-z_][A-Za-z0-9_]*)', _rep, line)


def _run_block(lines: list, executor, env: dict):
    i = 0
    while i < len(lines):
        raw = lines[i]
        line = raw.strip()
        i += 1

        if not line or line.startswith('#'):
            continue

        # Variable assignment: $VAR = value
        m = re.match(r'^\$([A-Za-z_]\w*)\s*=\s*(.+)$', line)
        if m:
            name, value = m.group(1), _expand(m.group(2).strip(), env)
            env[name] = value
            os.environ[name] = value
            print(Fore.CYAN + f'  ${name} = {value}' + Style.RESET_ALL)
            continue

        # if <command>:
        if line.startswith('if ') and line.endswith(':'):
            cond_cmd = _expand(line[3:-1].strip(), env)
            success, _ = executor.execute_command(cond_cmd)
            # Collect block until 'end' or 'else'
            block_true, block_false, in_else = [], [], False
            depth = 1
            while i < len(lines) and depth > 0:
                inner = lines[i].strip()
                i += 1
                if inner.startswith('if ') and inner.endswith(':'):
                    depth += 1
                if inner == 'end':
                    depth -= 1
                    if depth == 0:
                        break
                if inner == 'else' and depth == 1:
                    in_else = True
                    continue
                if not in_else:
                    block_true.append(lines[i - 1])
                else:
                    block_false.append(lines[i - 1])

            if success:
                _run_block(block_true, executor, env)
            else:
                _run_block(block_false, executor, env)
            continue

        # repeat N: ... end
        if line.startswith('repeat ') and line.endswith(':'):
            try:
                n = int(_expand(line[7:-1].strip(), env))
            except ValueError:
                n = 1
            block = []
            depth = 1
            while i < len(lines) and depth > 0:
                inner = lines[i].strip()
                i += 1
                if inner.startswith('repeat ') and inner.endswith(':'):
                    depth += 1
                if inner == 'end':
                    depth -= 1
                    if depth == 0:
                        break
                block.append(lines[i - 1])
            for _ in range(n):
                _run_block(block, executor, env)
            continue

        # print / echo
        if line.startswith('print ') or line.startswith('echo '):
            msg = _expand(line.split(None, 1)[1], env)
            print(msg)
            continue

        # Regular command
        cmd = _expand(line, env)
        print(Fore.YELLOW + f'  >> {cmd}' + Style.RESET_ALL)
        success, error = executor.execute_command(cmd)
        if not success and error:
            print(Fore.RED + f'[Script] Error: {error}' + Style.RESET_ALL)
