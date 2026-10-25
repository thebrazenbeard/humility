"""Fail closed on concealed workspace startup paths and executable font impostors.

Source checks do not establish whether a historical workstation executed a task.
"""
from __future__ import annotations

import os
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SKIP = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", "node_modules"}
BAD_FONT_SUFFIXES = {".lkf", ".js", ".mjs", ".cjs", ".ps1", ".bat", ".cmd", ".sh", ".py"}

class EditorStartupGuardTests(unittest.TestCase):
    def test_workspace_files_cannot_autoexecute(self) -> None:
        for directory, subdirs, files in os.walk(ROOT, followlinks=False):
            base = Path(directory)
            subdirs[:] = [name for name in subdirs if name not in SKIP]
            for name in [*subdirs, *files]:
                candidate = base / name
                relative = candidate.relative_to(ROOT).parts
                editor_path = any(part.casefold() == ".vscode" for part in relative)
                font_path = len(relative) >= 2 and tuple(
                    part.casefold() for part in relative[:2]
                ) == ("public", "fonts")
                if editor_path or font_path or name.casefold().endswith(".code-workspace"):
                    self.assertFalse(candidate.is_symlink(), f"unsafe symlink: {candidate}")
            for name in files:
                path = base / name
                relative = path.relative_to(ROOT).parts
                editor_path = any(part.casefold() == ".vscode" for part in relative)
                if editor_path and name.casefold() in {"tasks.json", "settings.json"}:
                    self._check_editor_file(path)
                if name.casefold().endswith(".code-workspace"):
                    self._check_editor_file(path)

    def test_fonts_are_fonts_not_programs(self) -> None:
        for directory, subdirs, files in os.walk(ROOT, followlinks=False):
            base = Path(directory)
            subdirs[:] = [x for x in subdirs if x not in SKIP]
            parts = tuple(p.casefold() for p in base.relative_to(ROOT).parts)
            if len(parts) < 2 or parts[:2] != ("public", "fonts"):
                continue
            for name in files:
                path = base / name
                self.assertNotIn(path.suffix.casefold(), BAD_FONT_SUFFIXES, str(path))
                if path.suffix.casefold() == ".woff2":
                    with path.open("rb") as fp:
                        self.assertEqual(fp.read(4), b"wOF2", f"invalid WOFF2: {path}")

    def _check_editor_file(self, path: Path) -> None:
        self.assertLessEqual(path.stat().st_size, 131072, str(path))
        data = path.read_text(encoding="utf-8").casefold()
        self.assertNotIn("folderopen", data, str(path))
        self.assertNotIn("task.allowautomatictasks", data, str(path))
        self.assertNotIn("fa-solid.lkf", data, str(path))

if __name__ == "__main__":
    unittest.main()
