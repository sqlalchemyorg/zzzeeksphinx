from os import path
package_dir = path.abspath(path.dirname(__file__))
template_path = path.join(package_dir, 'themes')


def get_path():
    return template_path
