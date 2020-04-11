import re
from docutils import nodes
from docutils.transforms import Transform
import os
from sphinx.util.osutil import copyfile
from sphinx.util.console import bold
from sphinx.domains.python import PyXRefRole
from sphinx.domains.python import PythonDomain
from distutils.version import LooseVersion
from sphinx import __version__
from sphinx.addnodes import pending_xref

# the searchindex.js system relies upon the object types
# in the PythonDomain to create search entries
from sphinx.domains import ObjType
from sphinx.util import logging


class RenderDocLinks(Transform):
    # apply references targets and optional references
    # to nodes that contain our target text.
    default_priority = 210

    def apply(self):
        classes = {"py-func", "py-attr", "py-meth", "py-class"}

        reg = re.compile(r"^(:meth:|:attr:)`~?(.+)`$")

        def find_code_node(node):
            return isinstance(node, nodes.literal) and classes.intersection(
                node.attributes.get("classes", ())
            )

        py_nodes = self.document.traverse(pending_xref)
        for py_node in py_nodes:
            if py_node.attributes['reftype'] in ('meth', 'attr', 'paramref'):
                if py_node.attributes['reftype'] == 'paramref':
                    need = 3
                else:
                    need = 2
                tokens = py_node.attributes['reftarget'].split(".")
                corrected_name = ".".join(tokens[-need:])
                if py_node.attributes["reftype"] == "meth":
                    corrected_name += "()"
                if str(py_node.children[0].children[0]) != corrected_name:
                    py_node.children[0].pop(0)
                    py_node.children[0].insert(
                        0, nodes.Text(corrected_name, corrected_name)
                    )


def setup(app):
    app.add_transform(RenderDocLinks)
