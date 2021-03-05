import re

from docutils import nodes
from docutils.parsers.rst import directives
from docutils.parsers.rst.directives.tables import align
from docutils.parsers.rst.directives.tables import ListTable
from docutils.statemachine import StringList
from sphinx.util.docutils import SphinxDirective

# see https://www.sphinx-doc.org/en/master/development/tutorials/todo.html


class DialectDirective(SphinxDirective):
    has_content = True

    _dialects = {}

    def _parse_content(self):
        d = {}
        d["default"] = self.content[0]
        d["text"] = []
        idx = 0
        for line in self.content[1:]:
            idx += 1
            m = re.match(r"\:(.+?)\: +(.+)", line)
            if m:
                attrname, value = m.group(1, 2)
                d[attrname] = value
            else:
                break
        d["text"] = self.content[idx + 1 :]
        return d

    def _dbapi_node(self):

        dialect_name, dbapi_name = self.dialect_name.split("+")

        try:
            dialect_directive = self._dialects[dialect_name]
        except KeyError:
            raise Exception(
                "No .. dialect:: %s "
                "directive has been established" % dialect_name
            )

        output = []

        content = self._parse_content()

        parent_section_ref = self.state.parent.children[0]["ids"][0]
        self._append_dbapi_bullet(
            dialect_name, dbapi_name, content["name"], parent_section_ref
        )

        p = nodes.paragraph(
            "",
            "",
            nodes.Text(
                "Support for the %s database via the %s driver."
                % (dialect_directive.database_name, content["name"]),
                "Support for the %s database via the %s driver."
                % (dialect_directive.database_name, content["name"]),
            ),
        )

        self.state.nested_parse(content["text"], 0, p)
        output.append(p)

        if "url" in content or "driverurl" in content:
            sec = nodes.section(
                "",
                nodes.title("DBAPI", "DBAPI"),
                ids=["dialect-%s-%s-url" % (dialect_name, dbapi_name)],
            )
            if "url" in content:
                text = (
                    "Documentation and download information "
                    "(if applicable) "
                    "for %s is available at:\n" % content["name"]
                )
                uri = content["url"]
                sec.append(
                    nodes.paragraph(
                        "",
                        "",
                        nodes.Text(text, text),
                        nodes.reference(
                            "", "", nodes.Text(uri, uri), refuri=uri
                        ),
                    )
                )
            if "driverurl" in content:
                text = "Drivers for this database are available at:\n"
                sec.append(
                    nodes.paragraph(
                        "",
                        "",
                        nodes.Text(text, text),
                        nodes.reference(
                            "",
                            "",
                            nodes.Text(
                                content["driverurl"], content["driverurl"]
                            ),
                            refuri=content["driverurl"],
                        ),
                    )
                )
            output.append(sec)

        if "connectstring" in content:
            sec = nodes.section(
                "",
                nodes.title("Connecting", "Connecting"),
                nodes.paragraph(
                    "",
                    "",
                    nodes.Text("Connect String:", "Connect String:"),
                    nodes.literal_block(
                        content["connectstring"], content["connectstring"]
                    ),
                ),
                ids=["dialect-%s-%s-connect" % (dialect_name, dbapi_name)],
            )
            output.append(sec)

        return output

    def _build_supported_version_table(self, content):
        if not any(
            k in content
            for k in ("full_support", "normal_support", "best_effort")
        ):
            return []
        text = ["* - Support type", "  - Versions"]
        if "full_support" in content:
            text.append("* - :term:`Fully tested in CI`")
            text.append("  - %s" % content["full_support"])
        if "normal_support" in content:
            text.append("* - :term:`Normal support`")
            text.append("  - %s" % content["normal_support"])
        if "best_effort" in content:
            text.append("* - :term:`Best effort`")
            text.append("  - %s" % content["best_effort"])

        list_table = ListTable(
            name="list-table",
            arguments=["**Supported %s versions**" % content["name"]],
            options={"header-rows": 1},
            content=StringList(text),
            lineno=self.lineno,
            content_offset=self.content_offset,
            block_text="",
            state=self.state,
            state_machine=self.state_machine,
        )
        return list_table.run()

    def _dialect_node(self):
        self._dialects[self.dialect_name] = self

        content = self._parse_content()
        self.database_name = content["name"]

        self.bullets = nodes.bullet_list()
        text = (
            "The following dialect/DBAPI options are available.  "
            "Please refer to individual DBAPI sections "
            "for connect information."
        )

        try:
            table = self._build_supported_version_table(content)
        except Exception:
            table = []

        if table:
            table = [nodes.paragraph("", "", *table)]
            # add the dialect to the recap table only if the dialect
            # has information to show there
            if not hasattr(self.env, "dialect_data"):
                self.env.dialect_data = []
            content["sphinx_docname"] = self.env.docname
            self.env.dialect_data.append(content)

        sec = nodes.section(
            "",
            nodes.paragraph(
                "",
                "",
                nodes.Text(
                    "Support for the %s database." % content["name"],
                    "Support for the %s database." % content["name"],
                ),
            ),
            nodes.paragraph(
                "",
                "",
                nodes.Text(
                    "The following table summarizes current support "
                    "levels for database release versions.",
                    "The following table summarizes current support "
                    "levels for database release versions.",
                ),
            ),
            *table,
            nodes.title("DBAPI Support", "DBAPI Support"),
            nodes.paragraph("", "", nodes.Text(text, text), self.bullets),
            ids=["dialect-%s" % self.dialect_name],
        )

        return [sec]

    def _append_dbapi_bullet(self, dialect_name, dbapi_name, name, idname):
        dialect_directive = self._dialects[dialect_name]
        try:
            relative_uri = self.env.app.builder.get_relative_uri(
                dialect_directive.docname, self.docname
            )
        except:
            relative_uri = ""
        list_node = nodes.list_item(
            "",
            nodes.paragraph(
                "",
                "",
                nodes.reference(
                    "",
                    "",
                    nodes.Text(name, name),
                    refdocname=self.docname,
                    refuri=relative_uri + "#" + idname,
                ),
            ),
        )
        dialect_directive.bullets.append(list_node)

    def run(self):
        self.docname = self.env.docname

        self.dialect_name = dialect_name = self.content[0]

        has_dbapi = "+" in dialect_name
        if has_dbapi:
            return self._dbapi_node()
        else:
            return self._dialect_node()


class dialecttable(nodes.General, nodes.Element):
    pass


class DialectTableDirective(SphinxDirective):
    has_content = True
    # from ListTable
    final_argument_whitespace = True
    optional_arguments = 1
    option_spec = {
        "header-rows": directives.nonnegative_int,
        "class": directives.class_option,
        "name": directives.unchanged,
        "align": align,
        "width": directives.length_or_percentage_or_unitless,
        "widths": directives.value_or(
            ("auto", "grid"), directives.positive_int_list
        ),
    }

    def run(self):
        node = dialecttable("")

        # generate a placeholder table since in process_dialect_table
        # there seem to be no access to state and state_machine

        text = [
            "* - Database",
            "  - :term:`Fully tested in CI`",
            "  - :term:`Normal support`",
            "  - :term:`Best effort`",
            # Mock row. Will be replaced in process_dialect_table
            "* - **placeholder**",
            "  - placeholder",
            "  - placeholder",
            "  - placeholder",
        ]

        self.options["header-rows"] = 1
        list_table = ListTable(
            name="list-table",
            arguments=self.arguments,
            options=self.options,
            content=StringList(text),
            lineno=self.lineno,
            content_offset=self.content_offset,
            block_text="",
            state=self.state,
            state_machine=self.state_machine,
        )

        node.extend(list_table.run())

        return [node]


def purge_dialects(app, env, docname):
    if not hasattr(env, "dialect_data"):
        return
    # not sure what this does
    env.dialect_data = [
        dialect
        for dialect in env.dialect_data
        if dialect["sphinx_docname"] != docname
    ]


def merge_dialects(app, env, docnames, other):
    if not hasattr(env, "dialect_data"):
        env.dialect_data = []

    if hasattr(other, "dialect_data"):
        env.dialect_data.extend(other.dialect_data)


def process_dialect_table(app, doctree, fromdocname):
    # Replace all dialecttable nodes with a table with the collected data
    env = app.builder.env
    if not hasattr(env, "dialect_data"):
        env.dialect_data = []

    seen = set()
    dialect_data = []
    for d in env.dialect_data:
        if d["name"] not in seen:
            seen.add(d["name"])
            dialect_data.append(d)

    dialect_data.sort(key=lambda d: d["name"])

    for node in doctree.traverse(dialecttable):
        if not dialect_data:
            node.replace_self([])
            return

        tbody = list(node.traverse(nodes.tbody))
        assert len(tbody) == 1
        tbody = tbody[0]

        assert len(tbody) == 1
        templateRow = tbody[0]
        tbody.remove(templateRow)

        for dialect_info in dialect_data:
            row = templateRow.deepcopy()
            text_to_replace = list(row.traverse(nodes.Text))
            assert len(text_to_replace) == 4
            columns = [
                # TODO: it would be great for this first element to
                # be hyperlinked
                dialect_info["name"],
                dialect_info.get("full_support", "-"),
                dialect_info.get("normal_support", "-"),
                dialect_info.get("best_effort", "-"),
            ]
            for text_node, col_text in zip(text_to_replace, columns):
                text_node.parent.remove(text_node)

                text_node.parent.append(nodes.Text(col_text, col_text))

            tbody.append(row)
        node.replace_self([node.children[0]])


def setup(app):
    app.add_node(dialecttable)
    app.add_directive("dialect", DialectDirective)
    app.add_directive("dialect-table", DialectTableDirective)
    app.connect("doctree-resolved", process_dialect_table)
    app.connect("env-purge-doc", purge_dialects)
    app.connect("env-merge-info", merge_dialects)
