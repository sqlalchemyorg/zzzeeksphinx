=============
zzzeeksphinx
=============

This is zzzeek's own Sphinx layout, used by SQLAlchemy.

This layout is first and foremost pulled in for the SQLAlchemy documentation
builds (and possibly other related projects).

.. note:: The stability of zzzeeksphinx is **not** guaranteed and APIs and
   behaviors can change at any time.    For use in other projects, please fork
   and/or adapt any portion of useful code as needed.

Features include:

* Uses Mako templates instead of Jinja, for more programmatic capabilities
  inside of templates.

* Layout includes an independently scrollable sidebar

* A unique (to Sphinx) "contextual" sidebar contents that shows the
  current page in context with all sibling pages (like that of MySQL's docs).
  This is a form of TOC that Sphinx doesn't typically have a lot of
  capability to do (well it could, with some simple feature adds), but
  IMO this kind of navigation is critical for very large and nested
  documentation sets, so that the navbar stays relatively small yet provides
  context as to where you are in the docs and what else is locally available.

* Modifications to autodoc which illustrate inherited classes, bases,
  method documentation illustrates if a method is only inherited from the
  base or overridden.

* A "dynamic base" feature that will, under ReadTheDocs, pull in optional
  ``.mako`` and ``.py`` files from the website of your choice
  that will serve as an alternate base template and a source of extra
  config setup, respectively, allowing the layout to be integrated into
  the layout of an external site when viewing on the web.

* A "viewsource" extension that can provide highlighted sourcecode to any
  Python file arbitrarily.

* SQLAlchemy-specific stuff, like the [SQL] popups, the dialect info
  directives.

* scss support using pyscss.


Config
======

in conf.py, the extension is::

  extensions = [
      'zzzeeksphinx',
  ]

The theme is::

  html_theme = 'zzzeeksphinx'

Other configs that SQLAlchemy has set up; these two are probably
needed::

  # The short X.Y version.
  version = "1.0"
  # The full version, including alpha/beta/rc tags.
  release = "1.0.0"

  release_date = "Not released"

Additional configs for the "dynamic site thing" look like::

  site_base = os.environ.get("RTD_SITE_BASE", "http://www.sqlalchemy.org")
  site_adapter_template = "docs_adapter.mako"
  site_adapter_py = "docs_adapter.py"

Configs which do some last-minute translation of module names
when running autodoc to display API documentation::

  autodocmods_convert_modname = {
      "sqlalchemy.sql.sqltypes": "sqlalchemy.types",
      "sqlalchemy.sql.type_api": "sqlalchemy.types",
      "sqlalchemy.sql.schema": "sqlalchemy.schema",
      "sqlalchemy.sql.elements": "sqlalchemy.sql.expression",
      "sqlalchemy.sql.selectable": "sqlalchemy.sql.expression",
      "sqlalchemy.sql.dml": "sqlalchemy.sql.expression",
      "sqlalchemy.sql.ddl": "sqlalchemy.schema",
      "sqlalchemy.sql.base": "sqlalchemy.sql.expression"
  }

  autodocmods_convert_modname_w_class = {
      ("sqlalchemy.engine.interfaces", "Connectable"): "sqlalchemy.engine",
      ("sqlalchemy.sql.base", "DialectKWArgs"): "sqlalchemy.sql.base",
  }





