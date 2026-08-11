"""Repository metadata and lightweight context discovery."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List


@dataclass(frozen=True)
class RepositoryMetadata:
    root: str
    projects: Dict[str, List[str]]
    rules_file: str | None = None


MARKERS = {
    "python": ("pyproject.toml", "requirements.txt", "setup.py"),
    "java": ("pom.xml", "build.gradle", "build.gradle.kts"),
    "node": ("package.json",),
    "go": ("go.mod",),
    "rust": ("Cargo.toml",),
}


def discover_repository(root: str | Path = ".") -> RepositoryMetadata:
    """Detect common project types and local CodeSmith rules."""
    path = Path(root).resolve()
    projects = {
        language: [marker for marker in markers if (path / marker).is_file()]
        for language, markers in MARKERS.items()
    }
    projects = {language: markers for language, markers in projects.items() if markers}
    rules = path / ".codesmith" / "rules.md"
    return RepositoryMetadata(str(path), projects, str(rules) if rules.is_file() else None)


def load_rules(root: str | Path = ".") -> str:
    """Read local CodeSmith rules, returning an empty string when absent."""
    path = Path(root).resolve() / ".codesmith" / "rules.md"
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")
