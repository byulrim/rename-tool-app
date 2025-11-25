import os
import subprocess
import tempfile
import sys
from pathlib import Path


def test_cmd_invocation_empty_replacement():
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        (td_path / 'a_aa.txt').write_text('x')
        script_path = Path(__file__).parents[1].joinpath('src', 'rename_with_dirs.py').resolve()
        python_exe = Path(sys.executable).resolve()
        # Build a cmd command string that uses cmd /c to pass an empty string as replacement
        # We need to quote python and script paths since they include backslashes
        command = '"{}" "{}" "{}" "" "{}"'.format(python_exe, script_path, 'aa', td_path)
        # Run via cmd using shell so cmd parses the quotes; this ensures empty "" is passed
        result = subprocess.run(command, capture_output=True, text=True, shell=True)
        assert result.returncode == 0, f"cmd invocation failed: {result.stdout} {result.stderr}"
        # Check the rename happened: a_aa -> a_
        # Check the rename happened to either a_.txt or a_NEW-style indexed name
        assert (td_path / 'a_.txt').exists() or any(p.name.startswith('a_(') for p in td_path.iterdir())
