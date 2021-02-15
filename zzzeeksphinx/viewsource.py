import ast
import imp
import os
import re
import warnings

import docutils
from docutils import nodes
from docutils.parsers.rst import Directive
from sphinx.errors import NoUri
from sphinx.locale import _
from sphinx.locale import __
from sphinx.pycode import ModuleAnalyzer
from sphinx.util import status_iterator

from . import util


def view_source(name, rawtext, text, lineno, inliner, options={}, content=[]):

    env = inliner.document.settings.env

    node = _view_source_node(env, text, None)
    return [node], []


def vendored_collect_pages(app):
    # vendored from sphinx viewcode
    env = app.builder.env
    if not hasattr(env, "_viewcode_modules"):
        return
    highlighter = app.builder.highlighter  # type: ignore
    urito = app.builder.get_relative_uri

    modnames = set(env._viewcode_modules)  # type: ignore

    for modname, entry in status_iterator(
        sorted(env._viewcode_modules.items()),  # type: ignore
        __("highlighting module code... "),
        "blue",
        len(env._viewcode_modules),  # type: ignore
        app.verbosity,
        lambda x: x[0],
    ):
        if not entry:
            continue
        code, tags, used, refname = entry
        # construct a page name for the highlighted source
        pagename = "_modules/" + modname.replace(".", "/")
        # highlight the source using the builder's highlighter
        if env.config.highlight_language in ("python3", "default", "none"):
            lexer = env.config.highlight_language
        else:
            lexer = "python"
        highlighted = highlighter.highlight_block(code, lexer, linenos=False)
        # split the code into lines
        lines = highlighted.splitlines()
        # split off wrap markup from the first line of the actual code
        before, after = lines[0].split("<pre>")
        lines[0:1] = [before + "<pre>", after]
        # nothing to do for the last line; it always starts with </pre> anyway
        # now that we have code lines (starting at index 1), insert anchors for
        # the collected tags (HACK: this only works if the tag boundaries are
        # properly nested!)
        maxindex = len(lines) - 1
        for name, docname in used.items():
            type_, start, end = tags[name]
            backlink = urito(pagename, docname) + "#" + refname + "." + name
            lines[start] = (
                '<div class="viewcode-block" id="%s"><a class="viewcode-back" '
                'href="%s">%s</a>' % (name, backlink, _("[docs]"))
                + lines[start]
            )
            lines[min(end, maxindex)] += "</div>"
        # try to find parents (for submodules)
        parents = []
        parent = modname
        while "." in parent:
            parent = parent.rsplit(".", 1)[0]
            if parent in modnames:
                parents.append(
                    {
                        "link": urito(
                            pagename, "_modules/" + parent.replace(".", "/")
                        ),
                        "title": parent,
                    }
                )
        parents.append(
            {
                "link": urito(pagename, "_modules/index"),
                "title": _("Module code"),
            }
        )
        parents.reverse()
        # putting it all together
        context = {
            "parents": parents,
            "title": modname,
            "body": (
                _("<h1>Source code for %s</h1>") % modname + "\n".join(lines)
            ),
        }
        yield (pagename, context, "page.html")

    if not modnames:
        return

    html = ["\n"]
    # the stack logic is needed for using nested lists for submodules
    stack = [""]
    for modname in sorted(modnames):
        if modname.startswith(stack[-1]):
            stack.append(modname + ".")
            html.append("<ul>")
        else:
            stack.pop()
            while not modname.startswith(stack[-1]):
                stack.pop()
                html.append("</ul>")
            stack.append(modname + ".")
        html.append(
            '<li><a href="%s">%s</a></li>\n'
            % (
                urito(
                    "_modules/index", "_modules/" + modname.replace(".", "/")
                ),
                modname,
            )
        )
    html.append("</ul>" * (len(stack) - 1))
    context = {
        "title": _("Overview: module code"),
        "body": (
            _("<h1>All modules for which code is available</h1>")
            + "".join(html)
        ),
    }

    yield ("_modules/index", context, "page.html")


def vendored_env_merge_info(app, env, docnames, other):
    # vendored from sphinx viewcode
    if not hasattr(other, "_viewcode_modules"):
        return
    # create a _viewcode_modules dict on the main environment
    if not hasattr(env, "_viewcode_modules"):
        env._viewcode_modules = {}  # type: ignore
    # now merge in the information from the subprocess
    env._viewcode_modules.update(other._viewcode_modules)  # type: ignore


def _get_sphinx_py_module(env):
    base_name = env.temp_data.get("autodoc:module", None)
    if base_name is not None:
        return base_name
    if util.SPHINX_VERSION >= (1, 3):
        base_name = env.ref_context.get("py:module", None)
        if base_name is not None:
            return base_name
    else:
        base_name = env.temp_data.get("py:module", None)
        if base_name is not None:
            return base_name

    return None


def _get_module_docstring(_file):
    content = _file.read()
    module = ast.parse(content)
    for elem in module.body:
        if isinstance(elem, ast.Expr) and isinstance(elem.value, ast.Str):
            return elem.value.s
    else:
        return None


def _view_source_node(env, text, state):
    # pretend we're using viewcode fully,
    # install the context it looks for
    if not hasattr(env, "_viewcode_modules"):
        env._viewcode_modules = {}

    modname = text
    text = modname.split(".")[-1] + ".py"

    # imitate sphinx .<modname> syntax
    if modname.startswith("."):
        # see if the modname needs to be corrected in terms
        # of current module context

        base_module = _get_sphinx_py_module(env)
        if base_module:
            modname = base_module + modname
        else:
            warnings.warn(
                "Could not get base module for relative module: %s; "
                "not generating node" % modname
            )
            return None

    urito = env.app.builder.get_relative_uri

    # we're showing code examples which may have dependencies
    # which we really don't want to have required so load the
    # module by file, not import (though we are importing)
    # the top level module here...
    pathname = module_docstring = None

    for tok in modname.split("."):
        try:
            file_, pathname, desc = imp.find_module(
                tok, [pathname] if pathname else None
            )
        except ImportError as ie:
            raise ImportError("Error trying to import %s: %s" % (modname, ie))
        else:
            if file_:
                if state:
                    module_docstring = _get_module_docstring(file_)
                file_.close()

    # unlike viewcode which silently traps exceptions,
    # I want this to totally barf if the file can't be loaded.
    # a failed build better than a complete build missing
    # key content
    analyzer = ModuleAnalyzer.for_file(pathname, modname)
    # copied from viewcode
    analyzer.find_tags()
    if not isinstance(analyzer.code, str):
        code = analyzer.code.decode(analyzer.encoding)
    else:
        code = analyzer.code

    pagename = "_modules/" + modname.replace(".", "/")
    try:
        refuri = urito(env.docname, pagename)
    except NoUri:
        # if we're in the latex builder etc., this seems
        # to be what we get
        refuri = None

    if util.SPHINX_VERSION >= (1, 3):
        entry = code, analyzer.tags, {}, refuri
    else:
        entry = code, analyzer.tags, {}
    env._viewcode_modules[modname] = entry

    if refuri:
        refnode = nodes.reference(
            "", "", nodes.Text(text, text), refuri=urito(env.docname, pagename)
        )
    else:
        refnode = nodes.Text(text, text)

    # get the first line of the module docstring
    if module_docstring and state:
        firstline = module_docstring.lstrip().split("\n\n")[0]
        if 30 < len(firstline) < 450:  # opinionated
            description_node = nodes.paragraph("", "")
            # parse the content of the first line of the module
            state.nested_parse(
                docutils.statemachine.StringList([firstline]),
                0,
                description_node,
            )
            stuff_we_want = description_node.children[0].children
            refnode = nodes.paragraph(
                "", "", refnode, nodes.Text(" - ", " - "), *stuff_we_want
            )

    if state:
        return_node = nodes.paragraph("", "", refnode)
    else:
        return_node = refnode

    return return_node


def _parse_content(content):
    d = {}
    d["text"] = []
    idx = 0
    for line in content:
        idx += 1
        m = re.match(r" *\:(.+?)\:(?: +(.+))?", line)
        if m:
            attrname, value = m.group(1, 2)
            d[attrname] = value or ""
        else:
            break
    d["text"] = content[idx:]
    return d


def _comma_list(text):
    return re.split(r"\s*,\s*", text.strip())


class AutoSourceDirective(Directive):
    has_content = True

    def run(self):
        content = _parse_content(self.content)

        env = self.state.document.settings.env
        self.docname = env.docname

        sourcefile = self.state.document.current_source.split(os.pathsep)[0]
        dir_ = os.path.dirname(sourcefile)
        files = [
            f
            for f in os.listdir(dir_)
            if f.endswith(".py") and f != "__init__.py"
        ]

        if "files" in content:
            # ordered listing of files to include
            files = [
                fname
                for fname in _comma_list(content["files"])
                if fname in set(files)
            ]

        node = nodes.paragraph(
            "", "", nodes.Text("Listing of files:", "Listing of files:")
        )

        bullets = nodes.bullet_list()
        for fname in files:
            modname, ext = os.path.splitext(fname)
            # relative lookup
            modname = "." + modname

            link = _view_source_node(env, modname, self.state)
            if link is not None:
                list_node = nodes.list_item("", link)
                bullets += list_node

        node += bullets

        return [node]


def setup(app):

    app.add_role("viewsource", view_source)

    app.add_directive("autosource", AutoSourceDirective)

    app.connect("env-merge-info", vendored_env_merge_info)
    app.connect("html-collect-pages", vendored_collect_pages)
