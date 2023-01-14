from __future__ import absolute_import

import re

import pygments
from pygments.filter import apply_filters
from pygments.filter import Filter
from pygments.formatters import HtmlFormatter
from pygments.formatters import LatexFormatter
from pygments.lexer import bygroups
from pygments.lexer import RegexLexer
from pygments.lexer import using
from pygments.lexer import words
from pygments.lexers import PythonConsoleLexer
from pygments.lexers import PythonLexer
from pygments.lexers import SqlLexer
from pygments.token import Keyword
from pygments.token import Token
from sphinx import highlighting
from sphinx.highlighting import PygmentsBridge


def _strip_trailing_whitespace(iter_):
    buf = list(iter_)
    if buf:
        buf[-1] = (buf[-1][0], buf[-1][1].rstrip())
    for t, v in buf:
        yield t, v


class RealWorldSQLLexer(SqlLexer):
    tokens = {k: l[:] for (k, l) in SqlLexer.tokens.items()}

    tokens["root"].insert(0, (words(("RETURNING",), suffix=r"\b"), Keyword))


class StripDocTestFilter(Filter):
    def filter(self, lexer, stream):
        for ttype, value in stream:
            if (
                ttype is Token.Comment or ttype.parent is Token.Comment
            ) and re.match(r"#\s*doctest:", value):
                continue
            yield ttype, value


class DetectAnnotationsFilter(Filter):
    def filter(self, lexer, stream):
        first, second = None, None
        found_colon = False
        should_report = False
        annotated = None
        found_sql = False

        for ttype, value in stream:

            # any encounting of SQL blocks, stop immediately.  This is
            # likely not a class def example and we don't want the
            # "anno/non-anno" label to appear under SQL boxes at all
            if ttype is Token.Name and value in (
                "execsql",
                "printsql",
                "opensql",
                "sqlpopup",
            ):
                found_sql = True
                should_report = False

            if found_sql:
                yield ttype, value
                continue

            if ttype is Token.Name.Builtin:
                ttype = Token.Name

            if ttype is Token.Keyword and value == "class":
                should_report = True

            first = second
            second = ttype, value

            yield ttype, value

            if annotated:
                continue
            elif annotated is None and ttype is not Token.Text:
                annotated = False

            if (first, second) == ARROW_ANNOTATION:
                annotated = True
            elif found_colon:
                if (ttype, value) == NEWLINE:
                    found_colon = False
                elif ttype == Token.Name:
                    found_colon = False
                    annotated = True
            elif first and ((first[0:1], second) == COLON_ANNOTATION):
                found_colon = True
                # should_report = True

        # report only on examples that have class defs
        if annotated is not None and should_report:
            yield Token.Other, f"pep484 annotations detected: {annotated}"


class PyConWithSQLLexer(RegexLexer):
    name = "PyCon+SQL"
    aliases = ["pycon+sql"]

    flags = re.IGNORECASE | re.DOTALL

    tokens = {
        "root": [
            (r"{sql}", Token.Sql.Link, "sqlpopup"),
            (r"{execsql}", Token.Sql.Exec, "execsql"),
            (r"{opensql}", Token.Sql.Exec, "opensql"),  # alias of execsql
            (r"{printsql}", Token.Sql.Print, "printsql"),
            (r".*?\n", using(PythonConsoleLexer)),
        ],
        "sqlpopup": [
            (
                r"(.*?\n)((?:PRAGMA|BEGIN|WITH|SE\.\.\.|SELECT|INSERT|"
                "DELETE|ROLLBACK|"
                "COMMIT|ALTER|UPDATE|CREATE|DROP|PRAGMA"
                "|DESCRIBE).*?(?:{stop}\n?|$))",
                bygroups(using(PythonConsoleLexer), Token.Sql.Popup),
                "#pop",
            )
        ],
        "execsql": [(r".*?(?:{stop}\n*|$)", Token.Sql.ExecState, "#pop")],
        "opensql": [(r".*?(?:{stop}\n*|$)", Token.Sql.ExecState, "#pop")],
        "printsql": [(r".*?(?:{stop}\n*|$)", Token.Sql.PrintState, "#pop")],
    }


class PythonWithSQLLexer(RegexLexer):
    name = "Python+SQL"
    aliases = ["python+sql"]

    flags = re.IGNORECASE | re.DOTALL

    tokens = {
        "root": [
            (r"{sql}", Token.Sql.Link, "sqlpopup"),
            (r"{execsql}", Token.Sql.Exec, "execsql"),
            (r"{opensql}", Token.Sql.Exec, "opensql"),  # alias of execsql
            (r"{printsql}", Token.Sql.Print, "printsql"),
            (r".*?\n", using(PythonLexer)),
        ],
        "sqlpopup": [
            (
                r"(.*?\n)((?:PRAGMA|BEGIN|SELECT|INSERT|DELETE|ROLLBACK"
                "|COMMIT|ALTER|UPDATE|CREATE|DROP"
                "|PRAGMA|DESCRIBE).*?(?:{stop}\n?|$))",
                bygroups(using(PythonLexer), Token.Sql.Popup),
                "#pop",
            )
        ],
        "execsql": [(r".*?(?:{stop}\n*|$)", Token.Sql.ExecState, "#pop")],
        "opensql": [(r".*?(?:{stop}\n*|$)", Token.Sql.ExecState, "#pop")],
        "printsql": [(r".*?(?:{stop}\n*|$)", Token.Sql.PrintState, "#pop")],
    }


class PopupSQLFormatter(HtmlFormatter):
    def _format_lines(self, tokensource):
        sql_lexer = RealWorldSQLLexer()

        formatter = HtmlFormatter(nowrap=True)
        buf = []
        for ttype, value in apply_filters(tokensource, [StripDocTestFilter()]):
            if ttype in Token.Sql:

                for t, v in HtmlFormatter._format_lines(self, iter(buf)):
                    yield t, v
                buf = []

                if ttype in (Token.Sql.ExecState, Token.Sql.PrintState):
                    class_ = (
                        "show_sql"
                        if ttype is Token.Sql.ExecState
                        else "show_sql_print"
                    )
                    yield (
                        1,
                        f"<div class='{class_}'>%s</div>"
                        % pygments.highlight(
                            re.sub(r"(?:{stop}|\n+)\s*$", "", value),
                            sql_lexer,
                            formatter,
                        ),
                    )
                elif ttype is Token.Sql.Link:
                    yield 1, "<a href='#' class='sql_link'>sql</a>"
                elif ttype is Token.Sql.Popup:
                    yield (
                        1,
                        "<div class='popup_sql'>%s</div>"
                        % pygments.highlight(
                            re.sub(r"(?:{stop}|\n+)$", "", value),
                            sql_lexer,
                            formatter,
                        ),
                    )
            else:
                buf.append((ttype, value))

        for t, v in _strip_trailing_whitespace(
            HtmlFormatter._format_lines(self, iter(buf))
        ):
            yield t, v


class PopupLatexFormatter(LatexFormatter):
    def _filter_tokens(self, tokensource):
        for ttype, value in apply_filters(tokensource, [StripDocTestFilter()]):
            if ttype in Token.Sql:
                if ttype not in (
                    Token.Sql.Link,
                    Token.Sql.Exec,
                    Token.Sql.Print,
                ):
                    yield Token.Literal, re.sub(r"{stop}", "", value)
                else:
                    continue
            else:
                yield ttype, value

    def format(self, tokensource, outfile):
        LatexFormatter.format(self, self._filter_tokens(tokensource), outfile)


ARROW_ANNOTATION = (
    (Token.Operator, "-"),
    (Token.Operator, ">"),
)
COLON_ANNOTATION = (
    (Token.Name,),
    (Token.Punctuation, ":"),
)

NEWLINE = (Token.Text, "\n")


class DetectAnnotationsFormatterMixin:
    annotated = None

    def _format_lines(self, tokensource):

        self.annotated = None

        def go(tokensource):
            for ttype, value in tokensource:
                if ttype is Token.Other and value.startswith(
                    "pep484 annotations detected:"
                ):
                    self.annotated = (
                        value == "pep484 annotations detected: True"
                    )
                    continue

                yield ttype, value

        for level, tag in super()._format_lines(go(tokensource)):
            yield level, tag

    def _wrap_pre(self, inner):
        for level, tag in super()._wrap_pre(inner):
            yield level, tag

            if level == 0 and self.annotated is not None and tag == "</pre>":
                yield (
                    1,
                    '<div class="code-annotations-key"></div>'
                    if self.annotated
                    else '<div class="code-non-annotations-key"></div>',
                )

    def _wrap_code(self, inner):

        for level, tag in super()._wrap_code(inner):
            yield level, tag

            if level == 0 and self.annotated is not None and tag == "</code>":
                yield (
                    1,
                    '<div class="code-annotations-key"></div>'
                    if self.annotated
                    else '<div class="code-annotations-key"></div>',
                )


class AnnoPopupSQLFormatter(
    DetectAnnotationsFormatterMixin, PopupSQLFormatter
):
    pass


def setup_formatters(app, config):
    if config.zzzeeksphinx_annotation_key:
        PygmentsBridge.html_formatter = AnnoPopupSQLFormatter
        filters = [DetectAnnotationsFilter()]
    else:
        PygmentsBridge.html_formatter = PopupSQLFormatter
        filters = []

    highlighting.lexers["sql"] = RealWorldSQLLexer()

    highlighting.lexers["python"] = highlighting.lexers[
        "python3"
    ] = PythonLexer(filters=filters)
    highlighting.lexers["pycon"] = highlighting.lexers[
        "pycon3"
    ] = PythonConsoleLexer(filters=filters)
    highlighting.lexers["python+sql"] = PythonWithSQLLexer(filters=filters)
    highlighting.lexers["pycon+sql"] = PyConWithSQLLexer(filters=filters)

    PygmentsBridge.latex_formatter = PopupLatexFormatter


def setup(app):

    # pass lexer class instead of lexer instance
    app.add_lexer("pycon+sql", PyConWithSQLLexer)
    app.add_lexer("python+sql", PythonWithSQLLexer)

    app.add_config_value("zzzeeksphinx_annotation_key", None, "env")

    app.connect("config-inited", setup_formatters)
