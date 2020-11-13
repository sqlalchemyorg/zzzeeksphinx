import re

from docutils import nodes
from sphinx.addnodes import pending_xref
from sphinx.util import logging

LOG = logging.getLogger(__name__)


def replace_synonyms(app, doctree):

    py_nodes = doctree.traverse(pending_xref)

    replace_prefixes = app.env.config.zzzeeksphinx_module_prefixes

    for py_node in py_nodes:
        if not py_node.children or not py_node.children[0].children:
            continue

        reftype = py_node.attributes["reftype"]
        reftarget = py_node.attributes["reftarget"]

        needs_correction = False

        ref_tokens = reftarget.split(".")
        if ref_tokens[0] in replace_prefixes:
            ref_tokens[0] = replace_prefixes[ref_tokens[0]]

            needs_correction = True
            py_node.attributes["reftarget"] = ".".join(ref_tokens)

        if reftype in ("meth", "attr", "paramref"):
            lt = len(ref_tokens)
            if (
                reftype == "paramref"
                and lt >= 3
                and ref_tokens[-3][0].isupper()
            ):
                # for paramref look at first char of "method" token
                # to see if its a method name or if this is a
                # function.  paramrefs don't store this info right now.
                need = 3
            else:
                need = min(lt, 2)
            corrected_name = ".".join(ref_tokens[-need:])
        elif reftype in ("func", "obj", "data", "mod"):
            if needs_correction or re.match(
                r"^:(?:func|obj|data|mod):`[\.~].+`$", py_node.rawsource
            ):
                corrected_name = ref_tokens[-1]
            else:
                # print(
                #    "no longer correcting: %s %s %s"
                #    % (py_node.rawsource, py_node.source, py_node.line)
                # )
                continue
        elif reftype == "class" and (
            needs_correction or re.match(r"^:class:`\..+`$", py_node.rawsource)
        ):
            corrected_name = ref_tokens[-1]
        else:
            if needs_correction:
                LOG.warn(
                    "source %r at %s needs synonym correction but is not "
                    "handled by zzzeeksphinx",
                    py_node.rawsource,
                    py_node.source,
                )
            continue

        if reftype in ("meth", "func"):
            corrected_name += "()"

        py_node.children[0].pop(0)
        py_node.children[0].insert(
            0, nodes.Text(corrected_name, corrected_name)
        )


def setup(app):
    app.connect("doctree-read", replace_synonyms)
    app.add_config_value("zzzeeksphinx_module_prefixes", {}, "env")
