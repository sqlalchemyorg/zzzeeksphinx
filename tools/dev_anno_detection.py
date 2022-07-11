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

# names like "id" etc
COLON_ANNOTATION_2 = (
    (Token.Name.Builtin,),
    (Token.Punctuation, ":"),
)

NEWLINE = (Token.Text, "\n")


class DetectAnnotationsFilter(Filter):
    annotated = False

    def filter(self, lexer, stream):
        first, second = None, None
        found_colon = False

        for ttype, value in stream:
            first = second
            second = ttype, value

            print(f"{first} {second}")
            yield ttype, value

            if self.annotated:
                continue

            if (first, second) == ARROW_ANNOTATION:
                self.annotated = True
            elif found_colon:
                if (ttype, value) == NEWLINE:
                    found_colon = False
                elif ttype == Token.Name:
                    found_colon = False
                    self.annotated = True
            elif first and (
                (first[0:1], second) == COLON_ANNOTATION
                or (first[0:1], second) == COLON_ANNOTATION_2
            ):
                found_colon = True


class DetectAnnotationsFormatterMixin:
    annotated = False

    def _format_lines(self, tokensource):
        detect_annotations = DetectAnnotationsFilter()

        for ttype, value in super()._format_lines(
            apply_filters(tokensource, [detect_annotations])
        ):
            yield ttype, value

        if detect_annotations.annotated:
            self.annotated = True

    def _wrap_pre(self, inner):
        for level, tag in super()._wrap_pre(inner):
            if level == 0 and tag == "</pre>":
                yield (
                    1,
                    "<div class='code-annotations-key'>annotated example</div>"
                    if self.annotated
                    else "<div class='code-annotations-key'>"
                    "non-annotated example</div>",
                )
            yield level, tag

    def _wrap_code(self, inner):

        for level, tag in super()._wrap_code(inner):
            if level == 0 and tag == "</code>":
                yield (
                    1,
                    "<div class='code-annotations-key'>annotated example</div>"
                    if self.annotated
                    else "<div class='code-annotations-key'>"
                    "non-annotated example</div>",
                )
            yield level, tag


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


class Association(Base):
    __tablename__ = "association"

    left_id = mapped_column(ForeignKey("left.id"), primary_key=True)
    right_id = mapped_column(ForeignKey("right.id"), primary_key=True)
    extra_data = mapped_column(String(50))

    child = relationship("Child", backref="parent_associations")
    parent = relationship("Parent", backref="child_associations")


class Parent(Base):
    __tablename__ = "left"
    id: Mapped[int] = mapped_column(primary_key=True)

    children = relationship("Child", secondary="association")


class Child(Base):
    __tablename__ = "right"
    id: Mapped[int] = mapped_column(primary_key=True)

"""

opt = {}
lex = PythonLexer()

print(highlight(code1, lex, AnnoPopupSQLFormatter()))
