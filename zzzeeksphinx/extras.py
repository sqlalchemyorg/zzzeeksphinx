from docutils.nodes import Admonition
from docutils.nodes import Element
from docutils.parsers.rst.directives.admonitions import BaseAdmonition
from sphinx.locale import admonitionlabels, _


class deepalchemy(Admonition, Element):
    pass


class DeepAlchemy(BaseAdmonition):

    required_arguments = 0
    node_class = deepalchemy


def visit_deepalchemy(self, node):
    self.visit_admonition(node, "deepalchemy")


def depart_deepalchemy(self, node):
    self.depart_admonition(node)


deepalchemy_visit = (visit_deepalchemy, depart_deepalchemy)


def setup(app):

    admonitionlabels["deepalchemy"] = _('Deep Alchemy')

    app.add_directive("deepalchemy", DeepAlchemy)
    app.add_node(
        deepalchemy,
        **{
            key: deepalchemy_visit
            for key in [
                "html",
                "html5",
                "latex",
                "text",
                "xml",
                "texinfo",
                "manpage",
            ]
        }
    )
