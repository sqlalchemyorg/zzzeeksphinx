from setuptools import setup
import os
import re


v = open(
    os.path.join(os.path.dirname(__file__), "zzzeeksphinx", "__init__.py")
)
VERSION = (
    re.compile(r""".*__version__ = ["'](.*?)["']""", re.S)
    .match(v.read())
    .group(1)
)
v.close()

readme = os.path.join(os.path.dirname(__file__), "README.rst")


setup(
    name="zzzeeksphinx",
    version=VERSION,
    description="Zzzeek's Sphinx Layout and Utilities.",
    long_description=open(readme).read(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Topic :: Documentation",
    ],
    keywords="Sphinx",
    author="Mike Bayer",
    author_email="mike@zzzcomputing.com",
    url="https://github.com/sqlalchemyorg/zzzeeksphinx",
    license="MIT",
    packages=["zzzeeksphinx"],
    install_requires=["pyscss", "mako", "requests"],
    include_package_data=True,
    zip_safe=False,
    entry_points={
        "sphinx.html_themes": [
            "zsbase = zzzeeksphinx.theme",
            "zzzeeksphinx = zzzeeksphinx.theme",
            "zsmako = zzzeeksphinx.theme",
        ],
        "pygments.lexers": [
            "pycon+sql = zzzeeksphinx.sqlformatter:PyConWithSQLLexer",
            "python+sql = zzzeeksphinx.sqlformatter:PythonWithSQLLexer",
        ],
    },
)
