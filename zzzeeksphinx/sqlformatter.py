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
from pygments.lexers import PythonConsoleLexer
from pygments.lexers import PythonLexer
from pygments.lexers import SqlLexer
from pygments.token import Token
from sphinx.highlighting import PygmentsBridge


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


class PyConWithSQLLexer(RegexLexer):
    name = "PyCon+SQL"
    aliases = ["pycon+sql"]

    flags = re.IGNORECASE | re.DOTALL

    tokens = {
        "root": [
            (r"{sql}", Token.Sql.Link, "sqlpopup"),
            (r"{opensql}", Token.Sql.Open, "opensqlpopup"),
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
        "opensqlpopup": [(r".*?(?:{stop}\n*|$)", Token.Sql, "#pop")],
    }


class PythonWithSQLLexer(RegexLexer):
    name = "Python+SQL"
    aliases = ["python+sql"]

    flags = re.IGNORECASE | re.DOTALL

    tokens = {
        "root": [
            (r"{sql}", Token.Sql.Link, "sqlpopup"),
            (r"{opensql}", Token.Sql.Open, "opensqlpopup"),
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
        "opensqlpopup": [(r".*?(?:{stop}\n*|$)", Token.Sql, "#pop")],
    }


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


class PopupLatexFormatter(LatexFormatter):
    def _filter_tokens(self, tokensource):
        for ttype, value in apply_filters(tokensource, [StripDocTestFilter()]):
            if ttype in Token.Sql:
                if ttype is not Token.Sql.Link and ttype is not Token.Sql.Open:
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


class DetectAnnotationsFilter(Filter):
    annotated = None

    def filter(self, lexer, stream):
        first, second = None, None
        found_colon = False

        for ttype, value in stream:
            if ttype is Token.Name.Builtin:
                ttype = Token.Name

            first = second
            second = ttype, value

            # print(f"{first} {second}")
            yield ttype, value

            if self.annotated:
                continue
            elif self.annotated is None and ttype is not Token.Text:
                self.annotated = False

            if (first, second) == ARROW_ANNOTATION:
                self.annotated = True
            elif found_colon:
                if (ttype, value) == NEWLINE:
                    found_colon = False
                elif ttype == Token.Name:
                    found_colon = False
                    self.annotated = True
            elif first and ((first[0:1], second) == COLON_ANNOTATION):
                found_colon = True


class DetectAnnotationsFormatterMixin:
    annotated = None

    def __init__(self, app, link, **kw):
        self.app = app
        self.link = link
        super().__init__(**kw)

    def __call__(self, **kw):
        """a hack to allow pygments bridge to 'instantiate' an already
        stateful formatter"""

        return self.__class__(app=self.app, link=self.link, **kw)

    def _format_lines(self, tokensource):
        detect_annotations = DetectAnnotationsFilter()

        for ttype, value in super()._format_lines(
            apply_filters(tokensource, [detect_annotations])
        ):
            yield ttype, value

        self.annotated = detect_annotations.annotated

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
        PygmentsBridge.html_formatter = AnnoPopupSQLFormatter(
            app, config.zzzeeksphinx_annotation_key
        )
    else:
        PygmentsBridge.html_formatter = PopupSQLFormatter

    PygmentsBridge.latex_formatter = PopupLatexFormatter


def setup(app):
    # pass lexer class instead of lexer instance
    app.add_lexer("pycon+sql", PyConWithSQLLexer)
    app.add_lexer("python+sql", PythonWithSQLLexer)

    app.add_config_value("zzzeeksphinx_annotation_key", None, "env")

    app.connect("config-inited", setup_formatters)
