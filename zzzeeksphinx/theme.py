from os import path

package_dir = path.abspath(path.dirname(__file__))


def setup(app):
    app.add_html_theme("zsbase", path.join(package_dir, "themes", "zsbase"))
    app.add_html_theme(
        "zzzeeksphinx", path.join(package_dir, "themes", "zzzeeksphinx")
    )
    app.add_html_theme("zsmako", path.join(package_dir, "themes", "zsmako"))

    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }