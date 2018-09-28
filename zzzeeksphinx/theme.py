from os import path
package_dir = path.abspath(path.dirname(__file__))
template_path = path.join(package_dir, 'themes', 'zzzeeksphinx')


def setup(app):
    app.add_html_theme('zzzeeksphinx', template_path)
