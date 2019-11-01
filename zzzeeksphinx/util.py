import sphinx
import re


SPHINX_VERSION = tuple(
    int(dig) for dig in re.findall("\d+", sphinx.__version__)
)


def striptags(text):
    return re.compile(r"<[^>]*>").sub("", text)


def go(m):
    # .html with no anchor if present, otherwise "#" for top of page
    return m.group(1) or "#"


def strip_toplevel_anchors(text):
    return re.compile(r"(\.html)?#[-\w]+-toplevel").sub(go, text)
