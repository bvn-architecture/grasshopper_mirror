"""Grasshopper Mirror — README wrapper.

Paste into a GhPython node.  Logic lives in lib/mirror_readme.py.
Inputs: headline, tiny_description, tags, authors,
        headline_image_url, summary, origin_story,
        detailed_description, repo_url
Output: a
"""
import sys, os

LIB_PATH = os.path.join(os.pardir, "lib")

_here = os.path.dirname(ghenv.Component.OnPingDocument().FilePath)
sys.path.insert(0, os.path.join(_here, LIB_PATH))

from mirror_readme import generate_readme

a = generate_readme(ghenv.Component.OnPingDocument(),
                    headline, tiny_description, tags, authors,
                    headline_image_url, summary, origin_story,
                    detailed_description, repo_url)
