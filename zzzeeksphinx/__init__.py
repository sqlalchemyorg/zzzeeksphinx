__version__ = "1.3.3"


def setup(app):
    from . import (
        autodoc_mods,
        dialect_info,
        mako,
        sqlformatter,
        viewsource,
        scss,
        render_pydomains,
        extras,
    )

    autodoc_mods.setup(app)
    dialect_info.setup(app)
    mako.setup(app)
    sqlformatter.setup(app)
    viewsource.setup(app)
    scss.setup(app)
    render_pydomains.setup(app)
    extras.setup(app)

    return {
        "version": __version__,
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
