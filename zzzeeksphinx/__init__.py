__version__ = '1.0.16'


def setup(app):
    from . import autodoc_mods, dialect_info, mako, \
        sqlformatter, viewsource, scss

    autodoc_mods.setup(app)
    dialect_info.setup(app)
    mako.setup(app)
    sqlformatter.setup(app)
    viewsource.setup(app)
    scss.setup(app)
