from __future__ import absolute_import

from sphinx.application import TemplateBridge
from sphinx.jinja2glue import BuiltinTemplateLoader
from mako.lookup import TemplateLookup
from .toc import TOCMixin
import os

rtd = os.environ.get('READTHEDOCS', None) == 'True'

class MakoBridge(TOCMixin, TemplateBridge):
    def init(self, builder, *args, **kw):
        self.jinja2_fallback = BuiltinTemplateLoader()
        self.jinja2_fallback.init(builder, *args, **kw)

        builder.config.html_context['release_date'] = \
            builder.config['release_date']
        builder.config.html_context['site_base'] = builder.config['site_base']

        self.app = builder.app

        package_dir = os.path.abspath(os.path.dirname(__file__))
        template_path = os.path.join(
            package_dir, 'themes', builder.config.html_theme)

        self.lookup = TemplateLookup(
            strict_undefined=True,
            directories=builder.config.templates_path + [
                template_path
            ],
            #format_exceptions=True,
            imports=[
                "from zzzeeksphinx import util"
            ]
        )

        if rtd and builder.config['site_base']:
            import urllib2
            if builder.config['site_adapter_template']:
                # remote site layout / startup files
                template_name = builder.config['site_adapter_template']

                template = urllib2.urlopen(
                    builder.config['site_base'] + "/" + template_name).read()
                self.lookup.put_string(template_name, template)

            py_name = builder.config['site_adapter_py']
            if py_name:
                setup_ctx = urllib2.urlopen(
                    builder.config['site_base'] + "/" + py_name).read()
                lcls = {}
                exec(setup_ctx, lcls)
                self.setup_ctx = lcls['setup_context']

    def setup_ctx(self, context):
        pass

    def render(self, template, context):
        template = template.replace(".html", ".mako")
        context['prevtopic'] = context.pop('prev', None)
        context['nexttopic'] = context.pop('next', None)
        context['app'] = self.app
        # local docs layout
        context['rtd'] = False
        context['toolbar'] = False
        context['base'] = "static_base.mako"
        context['parent_toc'] = self.get_current_subtoc
        context['bridge'] = self
        context.setdefault('toc', None)
        context.setdefault('pdf_url', None)
        context.setdefault('metatags', None)
        context.setdefault("canonical_url", None)
        context.setdefault("single_version", None)
        context.setdefault("rtd_language", "en")
        # override context attributes
        self.setup_ctx(context)
        context.setdefault('_', lambda x: x)
        return self.lookup.get_template(template).render_unicode(**context)

    def render_string(self, template, context):
        # this is used for  .js, .css etc. and we don't have
        # local copies of that stuff here so use the jinja render.
        return self.jinja2_fallback.render_string(template, context)


def setup(app):
    app.config['template_bridge'] = "zzzeeksphinx.mako.MakoBridge"
    app.add_config_value('release_date', "", 'env')
    app.add_config_value('site_base', "", 'env')
    app.add_config_value('site_adapter_template', "", 'env')
    app.add_config_value('site_adapter_py', "", 'env')
    app.add_config_value('build_number', "", 'env')

