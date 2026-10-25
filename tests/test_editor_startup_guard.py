"""Fail closed on source-managed automatic editor configuration.

Source containment says nothing about possible historical workstation execution.
"""
from __future__ import annotations

import os
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SKIP = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", "node_modules"}
BAD_FONT_SUFFIXES = {".lkf", ".js", ".mjs", ".cjs", ".ps1", ".bat", ".cmd", ".sh", ".py"}

class EditorStartupGuardTests(unittest.TestCase):
    def test_automatic_workspace_configs_are_forbidden_by_path(self) -> None:
        # Reject the entire editor-task/settings surface. Raw-text scans could
        # miss JSON escapes (folder\\u004fpen) that VS Code decodes.
        for directory, subdirs, files in os.walk(ROOT, followlinks=False):
            base = Path(directory)
            subdirs[:] = [name for name in subdirs if name not in SKIP]
            for name in [*subdirs, *files]:
                candidate = base / name
                relative = tuple(p.casefold() for p in candidate.relative_to(ROOT).parts)
                editor_path = ".vscode" in relative
                font_path = relative[:2] == ("public", "fonts")
                if editor_path or font_path or name.casefold().endswith(".code-workspace"):
                    self.assertFalse(candidate.is_symlink(), f"unsafe symlink: {candidate}")
                if editor_path and name.casefold() in {"tasks.json", "settings.json"}:
                    self.fail(f"editor task/settings source forbidden: {candidate}")
                if name.casefold().endswith(".code-workspace"):
                    self.fail(f"workspace execution config forbidden: {candidate}")

    def test_disguised_program_assets_are_forbidden(self) -> None:
        for directory, subdirs, files in os.walk(ROOT, followlinks=False):
            base = Path(directory)
            subdirs[:] = [x for x in subdirs if x not in SKIP]
            parts = tuple(p.casefold() for p in base.relative_to(ROOT).parts)
            if parts[:2] != ("public", "fonts"):
                continue
            for name in files:
                path = base / name
                self.assertNotIn(path.suffix.casefold(), BAD_FONT_SUFFIXES, str(path))
                if path.suffix.casefold() == ".woff2":
                    with path.open("rb") as fp:
                        # Signature sanity only; not proof of complete WOFF2 validity.
                        self.assertEqual(fp.read(4), b"wOF2", f"invalid WOFF2 header: {path}")

if __name__ == "__main__":
    unittest.main()
