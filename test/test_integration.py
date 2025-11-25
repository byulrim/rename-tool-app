import sys
import os
from pathlib import Path
import tempfile
import shutil

# ensure src is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
import rename_with_dirs as rw


def test_file_rename_basic():
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        f = td_path / 'file_ORIG.txt'
        f.write_text('hello')
        log = td_path / 'log.csv'
        changed, errors, _ = rw.run_main('ORIG', 'NEW', td_path, False, log)
        assert changed == 1
        assert (td_path / 'file_NEW.txt').exists()


def test_conflict_indexing():
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        (td_path / 'a_NEW.txt').write_text('exists')
        (td_path / 'a_ORIG.txt').write_text('to rename')
        log = td_path / 'log.csv'
        changed, errors, _ = rw.run_main('ORIG', 'NEW', td_path, False, log)
        assert changed == 1
        # the renamed file should be a_NEW(1).txt
        assert (td_path / 'a_NEW(1).txt').exists()


def test_rename_dirs_flag():
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        d = td_path / 'dir_ORIG'
        d.mkdir()
        (d / 'inner.txt').write_text('x')
        log = td_path / 'log.csv'
        changed, errors, _ = rw.run_main('ORIG', 'NEW', td_path, True, log)
        assert changed == 1
        assert (td_path / 'dir_NEW').exists() or (td_path / 'dir_NEW(1)').exists()
