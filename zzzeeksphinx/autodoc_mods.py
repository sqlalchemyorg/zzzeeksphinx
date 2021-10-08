import inspect
import re

from docutils import nodes
from sphinx import addnodes
from sphinx.util import logging

LOG = logging.getLogger(__name__)


def autodoc_skip_member(app, what, name, obj, skip, options):
    if (
        what == "class"
        and skip
        and name
        in ("__init__", "__eq__", "__ne__", "__lt__", "__le__", "__call__")
        and obj.__doc__
        and getattr(obj, "__objclass__", None)
        not in (type, object, list, tuple, dict)
    ):
        return False
    else:
        return skip


def _adjust_rendered_mod_name(config, modname, objname):
    if (modname, objname) in config.autodocmods_convert_modname_w_class:
        return config.autodocmods_convert_modname_w_class[(modname, objname)]
    elif modname in config.autodocmods_convert_modname:
        return config.autodocmods_convert_modname[modname]
    else:
        return modname


# im sure this is in the app somewhere, but I don't really
# know where, so we're doing it here.
_track_autodoced = {}
_inherited_names = set()


def _superclass_classstring(
    adjusted_mod, base, tilde=False, pytype="class", attrname=None
):

    dont_link = (
        base.__module__ == "builtins"
        or base.__name__.startswith("_")
        or (attrname and attrname.startswith("_"))
    )
    attrname = ".%s" % attrname if attrname else ""
    if dont_link:
        return "``%s.%s%s``" % (adjusted_mod, base.__name__, attrname)
    else:
        return ":%s:`%s%s.%s%s`" % (
            pytype,
            "~" if tilde else "",
            adjusted_mod,
            base.__name__,
            attrname,
        )


def _quick_inspect_sig(
    args,
    varargs=None,
    varkw=None,
    defaults=None,
    kwonlyargs=(),
    kwonlydefaults={},
    annotations={},
    formatarg=str,
    formatvarargs=lambda name: "*" + name,
    formatvarkw=lambda name: "**" + name,
):
    specs = []
    if defaults:
        firstdefault = len(args) - len(defaults)

    close_bracket = False
    for i, arg in enumerate(args):
        if i > 3:
            specs[-1] += ", ..."
            break

        spec = formatarg(arg)
        if defaults and i >= firstdefault and not close_bracket:
            if specs:
                specs[-1] = specs[-1] + "["
            else:
                spec = "[" + spec
            close_bracket = True
        specs.append(spec)

    if close_bracket:
        specs[-1] = specs[-1] + "]"
        close_bracket = False

    if varargs is not None:
        specs.append(formatvarargs(formatarg(varargs)))
    else:
        if kwonlyargs:
            specs.append("*")

    if kwonlyargs:
        for kwonlyarg in kwonlyargs:
            spec = formatarg(kwonlyarg)
            if (
                kwonlydefaults
                and kwonlyarg in kwonlydefaults
                and not close_bracket
            ):
                close_bracket = True
                spec = "[" + spec
            specs.append(spec)

        if close_bracket:
            specs[-1] = specs[-1] + "]"
            close_bracket = False

    if varkw is not None:
        specs.append(formatvarkw(formatarg(varkw)))

    result = "(" + ", ".join(specs) + ")"
    return result


def write_autosummaries(app, doctree):
    for idx, node in enumerate(doctree.traverse(nodes.section)):

        immediate_autodoc_nodes = [
            n
            for n in node.traverse(addnodes.desc)
            if n.parent is node
            and n.attributes.get("objtype", None)
            in ("attribute", "data", "class", "function")
        ]
        if not immediate_autodoc_nodes:
            continue
        where = node.index(immediate_autodoc_nodes[0])

        immediate_autodoc_nodes = sorted(
            immediate_autodoc_nodes,
            key=lambda node: node[0].attributes["fullname"].lower(),
        )

        table = nodes.table("", classes=["longtable"])
        group = nodes.tgroup("", cols=2)

        table.append(group)
        group.append(nodes.colspec("", colwidth=10))
        group.append(nodes.colspec("", colwidth=90))

        header = nodes.thead("")
        header.append(
            nodes.row(
                "",
                nodes.entry("", nodes.Text("Object Name", "Object Name")),
                nodes.entry("", nodes.Text("Description", "Description")),
            )
        )
        group.append(header)

        body = nodes.tbody("")
        group.append(body)

        for ad_node in immediate_autodoc_nodes:

            # what = ad_node.attributes["objtype"]
            sig = ad_node.children[0]
            refid = sig.attributes.get("ids", [None])[0]
            if not refid:
                continue

            row = nodes.row("")

            obj = _track_autodoced.get(refid, None)

            if inspect.isfunction(obj):
                param_str = _quick_inspect_sig(*inspect.getfullargspec(obj))
            else:
                param_str = ""

            name_node = list(sig.traverse(addnodes.desc_name))
            if name_node:
                name_node = name_node[0]
            else:
                continue

            name_node = name_node.deepcopy()

            # nodes.literal(
            #    "", *[c.copy() for c in name_node.children]
            # )

            p = nodes.paragraph(
                "",
                "",
                # nodes.Text(what + " ", what + " "),
                nodes.reference(
                    "",
                    "",
                    name_node,
                    refid=refid,
                    classes=["reference", "internal"],
                ),
                nodes.Text(param_str, param_str),
            )

            row.append(nodes.entry("", p, classes=["nowrap"]))
            try:
                para = ad_node[1][0]
                if isinstance(para, nodes.paragraph):
                    text = para.deepcopy()
                else:
                    text = nodes.Text("", "")
            except IndexError:
                text = nodes.Text("", "")

            row.append(nodes.entry("", text))
            body.append(row)

        if where > 0:
            node.insert(where, table)


def fix_up_autodoc_headers(app, doctree):

    for idx, node in enumerate(doctree.traverse(addnodes.desc)):
        objtype = node.attributes.get("objtype")
        if objtype in ("method", "attribute"):
            sig = node.children[0]

            modname = sig.attributes["module"]
            clsname = sig.attributes["class"]
            qualified = "%s.%s." % (modname, clsname)

            start_index = 0
            if sig[0].rawsource == "async ":
                start_index = 1

            sig.insert(
                start_index,
                nodes.reference(
                    "",
                    "",
                    nodes.literal(qualified, qualified),
                    refid="%s.%s" % (modname, clsname),
                ),
            )

            sig.insert(
                start_index,
                addnodes.desc_annotation(
                    objtype, nodes.Text(objtype + " ", objtype + " ")
                ),
            )

        elif objtype == "function":
            sig = node.children[0]

            start_index = 0
            if sig[0].rawsource == "async ":
                start_index = 1

            sig.insert(
                start_index,
                addnodes.desc_annotation(
                    objtype, nodes.Text(objtype + " ", objtype + " ")
                ),
            )


def autodoc_process_signature(
    app, what, name, obj, options, signature, return_annotation
):
    # a fixer for return annotations that seem to be fully module-qualified
    # if the return class is outside of any brackets.
    if what in ("function", "method", "attribute") and return_annotation:
        m = re.match(r"^(.*?)\.([\w_]+)$", return_annotation)
        if m:
            modname, objname = m.group(1, 2)
            config = app.env.config
            if modname in config.autodocmods_convert_modname:
                modname = config.autodocmods_convert_modname[modname]

                new_return_annotation = "%s.%s" % (modname, objname)
                return_annotation = new_return_annotation
        return (signature, return_annotation)


def autodoc_process_docstring(app, what, name, obj, options, lines):
    # skipping superclass classlevel docs for now, as these
    # get in the way of using autosummary.

    if what == "class":
        _track_autodoced[name] = obj

        # need to translate module names for bases, others
        # as we document lots of symbols in namespace modules
        # outside of their source
        bases = []
        try:
            obj_bases = obj.__bases__
        except AttributeError:
            LOG.warn(
                "Object %s is not a class, "
                "cannot be corrected by zzzeeksphinx",
                obj,
            )
            return

        for base in obj_bases:
            if base is not object:
                adjusted_mod = _adjust_rendered_mod_name(
                    app.env.config, base.__module__, base.__name__
                )
                bases.append(_superclass_classstring(adjusted_mod, base))
                _inherited_names.add("%s.%s" % (adjusted_mod, base.__name__))

        if bases:
            modname, objname = re.match(r"(.*)\.(.*?)$", name).group(1, 2)

            adjusted_mod = _adjust_rendered_mod_name(
                app.env.config, modname, objname
            )
            clsdoc = _superclass_classstring(adjusted_mod, obj)

            lines.extend(
                [
                    "",
                    ".. container:: class_bases",
                    "    " "",
                    "    **Class signature**",
                    "",
                    "    class %s (%s)" % (clsdoc, ", ".join(bases)),
                    "",
                ]
            )

    elif what in ("attribute", "method"):
        m = re.match(r"(.*?)\.([\w_]+)$", name)
        if m:
            clsname, attrname = m.group(1, 2)
            if clsname in _track_autodoced:
                cls = _track_autodoced[clsname]
                found = False
                for supercls in cls.__mro__:
                    if attrname in supercls.__dict__:
                        found = True
                        break
                if found and supercls is not cls:
                    adjusted_mod = _adjust_rendered_mod_name(
                        app.env.config, supercls.__module__, supercls.__name__
                    )

                    _inherited_names.add(
                        "%s.%s" % (adjusted_mod, supercls.__name__)
                    )
                    _inherited_names.add(
                        "%s.%s.%s"
                        % (adjusted_mod, supercls.__name__, attrname)
                    )
                    lines[:0] = [
                        ".. container:: inherited_member",
                        "",
                        "    *inherited from the* "
                        "%s *%s of* %s"
                        % (
                            _superclass_classstring(
                                adjusted_mod,
                                supercls,
                                attrname=attrname,
                                pytype="attr"
                                if what == "attribute"
                                else "meth",
                                tilde=True,
                            ),
                            what,
                            _superclass_classstring(
                                adjusted_mod, supercls, tilde=True
                            ),
                        ),
                        "",
                    ]
    elif what == "function":
        _track_autodoced[name] = obj


def missing_reference(app, env, node, contnode):
    if node.attributes["reftarget"] in _inherited_names:
        return node.children[0]
    else:
        return None


def work_around_issue_6785():
    """See https://github.com/sphinx-doc/sphinx/issues/6785"""

    from sphinx.ext import autodoc

    # check some assumptions, more as a way of testing if this code changes
    # on the sphinx side
    assert (
        autodoc.PropertyDocumenter.priority
        > autodoc.AttributeDocumenter.priority
    )
    autodoc.PropertyDocumenter.priority = -100


def setup(app):
    work_around_issue_6785()

    app.connect("autodoc-skip-member", autodoc_skip_member)
    app.connect("autodoc-process-docstring", autodoc_process_docstring)
    app.connect("autodoc-process-signature", autodoc_process_signature)
    app.connect("doctree-read", fix_up_autodoc_headers)
    app.connect("doctree-read", write_autosummaries)
    app.add_config_value("autodocmods_convert_modname", {}, "env")
    app.add_config_value("autodocmods_convert_modname_w_class", {}, "env")

    app.connect("missing-reference", missing_reference)
