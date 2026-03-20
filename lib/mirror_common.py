"""Shared helpers for Grasshopper Mirror scripts."""

import os
import json


def output_path(gh_doc, suffix):
    """Derive '<basename>_<suffix>' next to the .gh file.

    Returns None if the document hasn't been saved yet.
    """
    fp = gh_doc.FilePath
    if not fp:
        return None
    base = os.path.splitext(os.path.basename(fp))[0]
    return os.path.join(os.path.dirname(fp), f"{base}_{suffix}")


def doc_dir(gh_doc):
    """Return the directory containing the .gh file, or None if unsaved."""
    fp = gh_doc.FilePath
    return os.path.dirname(fp) if fp else None


def write_text(path, content):
    """Write UTF-8 text to disk, ensuring a trailing newline."""
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
        if not content.endswith("\n"):
            f.write("\n")


def write_json(path, data):
    """Write a dict as pretty-printed JSON to disk."""
    content = json.dumps(data, indent=2, ensure_ascii=False)
    write_text(path, content)
