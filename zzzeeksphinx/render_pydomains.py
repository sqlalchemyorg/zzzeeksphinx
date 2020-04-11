from docutils import nodes
from docutils.transforms import Transform
from sphinx.addnodes import pending_xref
import re

# the searchindex.js system relies upon the object types
# in the PythonDomain to create search entries


class RenderDocLinks(Transform):
    default_priority = 210

    def apply(self):
        py_nodes = self.document.traverse(pending_xref)
        for py_node in py_nodes:
            if not py_node.children or not py_node.children[0].children:
                continue

            reftype = py_node.attributes["reftype"]
            if reftype in ("meth", "attr", "paramref"):
                tokens = py_node.attributes["reftarget"].split(".")
                lt = len(tokens)
                if (
                    reftype == "paramref"
                    and lt >= 3
                    and tokens[-3][0].isupper()
                ):
                    # for paramref look at first char of "method" token
                    # to see if its a method name or if this is a
                    # function.  paramrefs don't store this info right now.
                    need = 3
                else:
                    need = min(lt, 2)
                corrected_name = ".".join(tokens[-need:])
            elif reftype == "func":
                tokens = py_node.attributes["reftarget"].split(".")
                corrected_name = tokens[-1]
                need = 1
            elif reftype == "class" and re.match(
                r"^:class:`\..+`$", py_node.rawsource
            ):
                # for a class node, only rewrite it if the rawsource
                # indicates a "." at the beginning.  otherwise it either
                # has a ~ and it will just be class name anyway, or
                # it's fully module qualified and that should write out fully.
                tokens = py_node.attributes["reftarget"].split(".")
                corrected_name = tokens[-1]
                need = 1
            else:
                continue

            if py_node.attributes["reftype"] in ("meth", "func"):
                corrected_name += "()"

            py_node.children[0].pop(0)
            py_node.children[0].insert(
                0, nodes.Text(corrected_name, corrected_name)
            )


def setup(app):
    app.add_transform(RenderDocLinks)
