"""Consistency checks for the version number, which is stored in several places."""

import re
from pathlib import Path

import pytest

import ebooklib
from ebooklib import consts, epub

ROOT = Path(__file__).resolve().parent.parent


def _read(relative_path: str) -> str:
    """Return the text of a file in the repository, skipping the test when it is not available (e.g. sdist)."""
    path = ROOT / relative_path
    if not path.is_file():
        pytest.skip(f"{relative_path} is not available")
    return path.read_text(encoding="utf-8")


def test_version_constants_agree():
    """The version tuple is exported from ebooklib, ebooklib.consts and ebooklib.epub."""
    assert ebooklib.VERSION == consts.VERSION == epub.VERSION
    assert len(ebooklib.VERSION) == 3
    assert all(isinstance(part, int) for part in ebooklib.VERSION)


def test_generator_metadata_uses_version():
    """The package document names the generator with the library version."""
    book = epub.EpubBook()

    generator = book.get_metadata("OPF", "generator")

    assert generator == [("", {"name": "generator", "content": "Ebook-lib " + ".".join(map(str, ebooklib.VERSION))})]


def test_pyproject_version_matches_code():
    """pyproject.toml carries the same version as the code (major.minor, optional patch)."""
    match = re.search(r'^version = "(\d+)\.(\d+)(?:\.(\d+))?"', _read("pyproject.toml"), re.MULTILINE)
    assert match is not None
    declared = (int(match.group(1)), int(match.group(2)), int(match.group(3) or 0))
    assert declared == ebooklib.VERSION


def test_sphinx_version_matches_code():
    """The documentation shows the released version, not a development one."""
    conf = _read("docs/conf.py")
    short = re.search(r"^version = '([^']+)'", conf, re.MULTILINE)
    full = re.search(r"^release = '([^']+)'", conf, re.MULTILINE)
    assert short is not None and full is not None
    assert short.group(1) == "{}.{}".format(*ebooklib.VERSION[:2])
    assert full.group(1) in {short.group(1), ".".join(map(str, ebooklib.VERSION))}


def test_changelog_documents_current_version():
    """CHANGES.txt has a section for the current version, not marked as unreleased."""
    changes = _read("CHANGES.txt")
    major_minor = "{}.{}".format(*ebooklib.VERSION[:2])
    heading = re.search(rf"^Version {re.escape(major_minor)}(?:\.\d+)? \(([^)]*)\)$", changes, re.MULTILINE)
    assert heading is not None
    assert heading.group(1) != "unreleased"
