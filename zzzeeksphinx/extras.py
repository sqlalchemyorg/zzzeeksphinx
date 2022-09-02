from docutils import nodes
from docutils.nodes import Admonition
from docutils.nodes import Element
from docutils.nodes import topic
from docutils.parsers.rst.directives.admonitions import BaseAdmonition
from docutils.parsers.rst.directives.body import Topic
from sphinx.locale import _
from sphinx.locale import admonitionlabels


class footer_topic(topic):
    pass


class deepalchemy(Admonition, Element):
    pass


class DeepAlchemy(BaseAdmonition):

    required_arguments = 0
    node_class = deepalchemy


class legacy(Admonition, Element):
    pass


class Legacy(BaseAdmonition):

    required_arguments = 0
    node_class = legacy


class FooterTopic(Topic):

    node_class = footer_topic


def visit_footer_topic(self, node):
    self.visit_topic(node)


def depart_footer_topic(self, node):
    self.depart_topic(node)


def visit_deepalchemy(self, node):
    self.visit_admonition(node, "deepalchemy")


def visit_legacy(self, node):
    self.visit_admonition(node, "legacy")


def depart_admonition(self, node):
    self.depart_admonition(node)


deepalchemy_visit = (visit_deepalchemy, depart_admonition)

legacy_visit = (visit_legacy, depart_admonition)

footer_topic_visit = (visit_footer_topic, depart_footer_topic)


def move_footer(app, doctree):

    if doctree.traverse(footer_topic):
        dec = nodes.decoration()
        doctree.append(dec)
        for f1 in doctree.traverse(footer_topic):
            dec.append(f1.deepcopy())
            f1.parent.remove(f1)


visit_keys = [
    "html",
    "html5",
    "latex",
    "text",
    "xml",
    "texinfo",
    "manpage",
]


def setup(app):

    app.add_directive("footer_topic", FooterTopic)

    admonitionlabels["deepalchemy"] = _("Deep Alchemy")
    app.add_directive("deepalchemy", DeepAlchemy)
    app.add_node(deepalchemy, **{key: deepalchemy_visit for key in visit_keys})

    admonitionlabels["legacy"] = _("Legacy Feature")
    app.add_directive("legacy", Legacy)
    app.add_node(legacy, **{key: legacy_visit for key in visit_keys})

    app.add_node(
        footer_topic, **{key: footer_topic_visit for key in ["html", "html5"]}
    )

    app.connect("doctree-read", move_footer)
