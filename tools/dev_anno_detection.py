from __future__ import absolute_import

import re

import pygments
from pygments import highlight
from pygments.filter import apply_filters
from pygments.filter import Filter
from pygments.formatters import HtmlFormatter
from pygments.lexers import PythonLexer
from pygments.lexers import SqlLexer
from pygments.token import Token


def _strip_trailing_whitespace(iter_):
    buf = list(iter_)
    if buf:
        buf[-1] = (buf[-1][0], buf[-1][1].rstrip())
    for t, v in buf:
        yield t, v


class StripDocTestFilter(Filter):
    def filter(self, lexer, stream):
        for ttype, value in stream:
            if (
                ttype is Token.Comment or ttype.parent is Token.Comment
            ) and re.match(r"#\s*doctest:", value):
                continue
            yield ttype, value


ARROW_ANNOTATION = (
    (Token.Operator, "-"),
    (Token.Operator, ">"),
)
COLON_ANNOTATION = (
    (Token.Name,),
    (Token.Punctuation, ":"),
)


NEWLINE = (Token.Text, "\n")


class DetectAnnotationsFilter(Filter):
    def filter(self, lexer, stream):
        first, second = None, None
        found_colon = False
        should_report = False
        annotated = None
        found_sql = False

        for ttype, value in stream:

            # any encounting of SQL blocks, stop immediately, we would
            # have detected annotations by now if they applied.
            # don't misinterpret SQL tokens
            if ttype is Token.Name and value in (
                "execsql",
                "printsql",
                "opensql",
                "sqlpopup",
            ):
                found_sql = True

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
                should_report = True

        # report only on examples that have class defs
        if annotated is not None and should_report:
            yield Token.Other, f"pep484 annotations detected: {annotated}"


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


class PopupSQLFormatter(HtmlFormatter):
    def _format_lines(self, tokensource):
        sql_lexer = SqlLexer()
        formatter = HtmlFormatter(nowrap=True)
        buf = []
        for ttype, value in apply_filters(tokensource, [StripDocTestFilter()]):
            if ttype in Token.Sql:

                for t, v in HtmlFormatter._format_lines(self, iter(buf)):
                    yield t, v
                buf = []

                if ttype is Token.Sql:
                    yield (
                        1,
                        "<div class='show_sql'>%s</div>"
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


class AnnoPopupSQLFormatter(
    DetectAnnotationsFormatterMixin, PopupSQLFormatter
):
    pass


code1 = """

>>> from sqlalchemy import text

>>> with engine.connect() as conn:
...     result = conn.execute(text("select 'hello world'"))
...     print(result.all())
{execsql}BEGIN (implicit)
select 'hello world'
[...] ()
{stop}[('hello world',)]
{execsql}ROLLBACK{stop}


"""

opt = {}
lex = PythonLexer()

print(highlight(code1, lex, AnnoPopupSQLFormatter()))
