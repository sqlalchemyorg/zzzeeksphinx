from __future__ import absolute_import

import os
from scss import Scss

# these docs aren't super accurate
# http://pyscss.readthedocs.org/en/latest/


def _check_for_builder(app):
    # TODO: make this inclusive of HTML builders
    # instead, or something
    if app.builder.name == "latex" or app.builder.name == "gettext":
        return False
    else:
        return True


def add_stylesheet(app):
    if not _check_for_builder(app):
        return

    to_gen = []

    package_dir = os.path.abspath(os.path.dirname(__file__))
    static_path = os.path.join(
        package_dir, "themes", app.builder.config.html_theme, "static"
    )

    for fname in os.listdir(static_path):
        name, ext = os.path.splitext(fname)
        if ext == ".scss":
            to_gen.append((static_path, name))
        elif ext == ".css":
            app.add_stylesheet(fname)

    # sphinx doesn't really have a "temp" area that will persist
    # down into build-finished (env.temp_data gets emptied).
    # So make our own!
    app._builder_scss = to_gen

    for path, name in to_gen:
        # changed in 1.8
        # https://www.sphinx-doc.org/en/master/extdev/appapi.html#sphinx.application.Sphinx.add_css_file
        app.add_css_file("%s.css" % name)


def generate_stylesheet(app, exception):
    # TODO: make this inclusive of HTML builders
    # instead, or something
    if not _check_for_builder(app):
        return

    to_gen = app._builder_scss

    compiler = Scss(scss_opts={"style": "expanded"})
    if exception:
        return
    for static_path, name in to_gen:

        css = compiler.compile(
            open(os.path.join(static_path, "%s.scss" % name)).read()
        )

        dest = os.path.join(app.builder.outdir, "_static", "%s.css" % name)
        # copyfile(os.path.join(source, "%s.css" % name), dest)

        with open(dest, "w") as out:
            out.write(css)


def setup(app):
    app.connect("builder-inited", add_stylesheet)
    app.connect("build-finished", generate_stylesheet)
