import inspect
import re
import sys
import warnings

from sphinx.util.nodes import make_refnode


def autodoc_skip_member(app, what, name, obj, skip, options):
    if (
        what == "class"
        and skip
        and name
        in ("__init__", "__eq__", "__ne__", "__lt__", "__le__", "__call__")
        and obj.__doc__
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
                bases.append(":class:`%s.%s`" % (adjusted_mod, base.__name__))
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
                        ":%s:`~%s.%s.%s` *%s of* :class:`~%s.%s`"
                        % (
                            "attr" if what == "attribute" else "meth",
                            adjusted_mod,
                            supercls.__name__,
                            attrname,
                            what,
                            adjusted_mod,
                            supercls.__name__,
                        ),
                        "",
                    ]


def missing_reference(app, env, node, contnode):
    if node.attributes["reftarget"] in _inherited_names:
        return node.children[0]
    elif node.attributes["reftype"] == "meth":
        return resolve_missing_method_reference(app, env, node, contnode)

    else:
        return None

_bmopotk = None
def _big_map_of_pydomain_obj_to_key(env):
    global _bmopotk
    if _bmopotk is None:
        _bmopotk = {}
        for key in env.domains["py"].objects:
            obj = _import_object(key)
            if obj is not None and obj.__hash__ is not None:
                _bmopotk[obj] = key
    return _bmopotk

def resolve_missing_method_reference(app, env, node, contnode):
    # NOTE: this does not work, *at all*.   will keep trying.

    tokens = node.attributes["reftarget"].split(".")
    cant_find_tokens = []
    matches = []
    while tokens:
        try_ = ".".join(tokens)
        new_matches = [
            k for k in env.domains["py"].objects if k.endswith(try_)
        ]
        if new_matches:
            matches = new_matches
            break
        else:
            cant_find_tokens.insert(-1, tokens[-1])
            del tokens[-1]

    per_obj_matches = []
    _bmopotk = _big_map_of_pydomain_obj_to_key(env)
    for match in matches:
        obj = _import_object(match)
        if not inspect.isclass(obj):
            import pdb
            pdb.set_trace()
        if inspect.isclass(obj):
            for mro in obj.__mro__:
                obj = mro
                for token in cant_find_tokens:
                    not_found = object()
                    obj = getattr(obj, token, not_found)
                    if obj is not_found:
                        break
                else:
                    if obj in _bmopotk:
                        per_obj_matches.append(_bmopotk[obj])
                        break
    lp = len(per_obj_matches)
    if lp == 0:
        warnings.warn(
            "Couldn't resolve method %s through MRO searching"
            % node.attributes["reftarget"]
        )
    elif lp > 1:
        import pdb
        pdb.set_trace()
        warnings.warn(
            "Found multiple matches for %s through MRO searching"
            % node.attributes["reftarget"]
        )
    else:
        warnings.warn(
            "SUCCESS, matched %s to %s through MRO searching" % (
                node.attributes["reftarget"], per_obj_matches[0]
            )
        )
        objdoc, type_ = env.domains["py"].objects[per_obj_matches[0]]
        return make_refnode(
            app.builder,
            node.attributes["refdoc"],
            objdoc,
            per_obj_matches[0],
            contnode,
            per_obj_matches[0],
        )


def _import_object(dotted_name):
    tokens = dotted_name.split(".")
    non_module_tokens = []
    module = None
    while tokens:
        try_ = ".".join(tokens)
        try:
            __import__(try_)
        except ImportError:
            non_module_tokens.insert(-1, tokens[-1])
            del tokens[-1]
        else:
            module = sys.modules[try_]
            break

    if module is None:
        return None

    obj = module
    not_found = object()
    for tok in non_module_tokens:
        obj = getattr(obj, tok, not_found)
        if obj is not_found:
            return None
    return obj


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
    app.add_config_value("autodocmods_convert_modname", {}, "env")
    app.add_config_value("autodocmods_convert_modname_w_class", {}, "env")

    app.connect("missing-reference", missing_reference)
