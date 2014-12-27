import re


def autodoc_skip_member(app, what, name, obj, skip, options):
    if what == 'class' and skip and \
        name in ('__init__', '__eq__', '__ne__', '__lt__',
                    '__le__', '__call__') and \
        obj.__doc__:
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
                    app.env.config, base.__module__, base.__name__)
                bases.append(
                    ":class:`%s.%s`" % (
                        adjusted_mod,
                        base.__name__))
                _inherited_names.add(
                    "%s.%s" % (adjusted_mod, base.__name__))

        if bases:
            lines[:0] = [
                "Bases: %s" % (", ".join(bases)),
                ""
            ]

    elif what in ("attribute", "method") and options.get("inherited-members"):
        m = re.match(r'(.*?)\.([\w_]+)$', name)
        if m:
            clsname, attrname = m.group(1, 2)
            if clsname in _track_autodoced:
                cls = _track_autodoced[clsname]
                for supercls in cls.__mro__:
                    if attrname in supercls.__dict__:
                        break
                if supercls is not cls:
                    adjusted_mod = _adjust_rendered_mod_name(
                        app.env.config,
                        supercls.__module__,
                        supercls.__name__
                    )

                    _inherited_names.add(
                        "%s.%s" % (adjusted_mod, supercls.__name__))
                    _inherited_names.add(
                        "%s.%s.%s" %
                        (adjusted_mod, supercls.__name__, attrname))
                    lines[:0] = [
                        ".. container:: inherited_member",
                        "",
                        "    *inherited from the* "
                        ":%s:`~%s.%s.%s` *%s of* :class:`~%s.%s`" % (
                            "attr" if what == "attribute"
                            else "meth",
                            adjusted_mod,
                            supercls.__name__,
                            attrname,
                            what,
                            adjusted_mod,
                            supercls.__name__
                        ),
                        ""
                    ]


def missing_reference(app, env, node, contnode):
    if node.attributes['reftarget'] in _inherited_names:
        return node.children[0]
    else:
        return None


def setup(app):
    app.connect('autodoc-skip-member', autodoc_skip_member)
    app.connect('autodoc-process-docstring', autodoc_process_docstring)
    app.add_config_value("autodocmods_convert_modname", {}, 'env')
    app.add_config_value("autodocmods_convert_modname_w_class", {}, 'env')

    app.connect('missing-reference', missing_reference)
