import re

from docutils import nodes
from sphinx import addnodes


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


def fix_up_autodoc_headers(app, doctree):

    for idx, node in enumerate(doctree.traverse(addnodes.desc)):
        objtype = node.attributes.get("objtype")
        if objtype in ("method", "attribute"):
            sig = node.children[0]

            modname = sig.attributes["module"]
            clsname = sig.attributes["class"]
            qualified = "%s.%s." % (modname, clsname)

            sig.insert(
                0,
                nodes.reference(
                    "",
                    "",
                    nodes.literal(qualified, qualified),
                    refid="%s.%s" % (modname, clsname),
                ),
            )

            sig.insert(
                0,
                addnodes.desc_annotation(
                    objtype, nodes.Text(objtype + " ", objtype + " ")
                ),
            )

        elif objtype == "function":
            sig = node.children[0]
            sig.insert(
                0,
                addnodes.desc_annotation(
                    objtype, nodes.Text(objtype + " ", objtype + " ")
                ),
            )


def autodoc_process_docstring(app, what, name, obj, options, lines):
    if what == "class":
        _track_autodoced[name] = obj

        # need to translate module names for bases, others
        # as we document lots of symbols in namespace modules
        # outside of their source
        bases = []
        for base in obj.__bases__:
            if base is not object:
                adjusted_mod = _adjust_rendered_mod_name(
                    app.env.config, base.__module__, base.__name__
                )
                bases.append(_superclass_classstring(adjusted_mod, base))
                _inherited_names.add("%s.%s" % (adjusted_mod, base.__name__))

        if bases:
            lines[:0] = ["Bases: %s" % (", ".join(bases)), ""]

    elif what in ("attribute", "method"):
        m = re.match(r"(.*?)\.([\w_]+)$", name)
        if m:
            clsname, attrname = m.group(1, 2)
            if clsname in _track_autodoced:
                cls = _track_autodoced[clsname]
                for supercls in cls.__mro__:
                    if attrname in supercls.__dict__:
                        break
                if supercls is not cls:
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


def missing_reference(app, env, node, contnode):
    if node.attributes["reftarget"] in _inherited_names:
        return node.children[0]
    else:
        return None


def work_around_issue_6785():
    """See https://github.com/sphinx-doc/sphinx/issues/6785
    """

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
    app.connect("doctree-read", fix_up_autodoc_headers)
    app.add_config_value("autodocmods_convert_modname", {}, "env")
    app.add_config_value("autodocmods_convert_modname_w_class", {}, "env")

    app.connect("missing-reference", missing_reference)
