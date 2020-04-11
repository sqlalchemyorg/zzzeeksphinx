__version__ = "1.1.1"


def setup(app):
    from . import (
        autodoc_mods,
        dialect_info,
        mako,
        sqlformatter,
        viewsource,
        scss,
        render_pydomains
    )

    autodoc_mods.setup(app)
    dialect_info.setup(app)
    mako.setup(app)
    sqlformatter.setup(app)
    viewsource.setup(app)
    scss.setup(app)
    render_pydomains.setup(app)