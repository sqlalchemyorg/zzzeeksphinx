from docutils.nodes import Admonition
from docutils.nodes import Element
from docutils.parsers.rst.directives.admonitions import BaseAdmonition
from sphinx.locale import _
from sphinx.locale import admonitionlabels


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


class observations(Admonition, Element):
    pass


class Observations(BaseAdmonition):
    required_arguments = 0
    node_class = observations


def visit_observations(self, node):
    self.visit_admonition(node, "observations")


def depart_observations(self, node):
    self.depart_admonition(node)


observations_visit = (visit_observations, depart_observations)


def setup(app):

    admonitionlabels["deepalchemy"] = _("Deep Alchemy")
    admonitionlabels["observations"] = _("extra notes on the above example")

    app.add_directive("deepalchemy", DeepAlchemy)
    app.add_directive("observations", Observations)

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

    app.add_node(
        observations,
        **{
            key: observations_visit
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
