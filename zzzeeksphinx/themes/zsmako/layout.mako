## coding: utf-8
<%!
    local_script_files = []

    default_css_files = [
        '_static/pygments.css',
    ]
%>

<%doc>
    Structural elements are all prefixed with "docs-"
    to prevent conflicts when the structure is integrated into the
    main site.

    docs-container ->
        docs-header ->
            docs-search
            docs-version-header
        docs-top-navigation
            docs-top-page-control
            docs-navigation-banner
        docs-body-container ->
            docs-sidebar
            docs-body
        docs-bottom-navigation
            docs-copyright
</%doc>

<%inherit file="${context['base']}"/>

<%
withsidebar = bool(toc) and current_page_name != 'index'
%>

<%block name="head_title">
    % if current_page_name not in ('index', 'genindex'):
    ${capture(self.show_title) | util.striptags} &mdash;
    % endif
    ${docstitle|h}
</%block>


<div id="docs-container">

<%block name="headers">
    ${parent.headers()}

    <!-- begin layout.mako headers -->

    % if hasdoc('about'):
        <link rel="author" title="${_('About these documents')}" href="${pathto('about')}" />
    % endif
    <link rel="index" title="${_('Index')}" href="${pathto('genindex')}" />
    <link rel="search" title="${_('Search')}" href="${pathto('search')}" />
    % if hasdoc('copyright'):
        <link rel="copyright" title="${_('Copyright')}" href="${pathto('copyright')}" />
    % endif
    <link rel="top" title="${docstitle|h}" href="${pathto('index')}" />
    % if parents:
        <link rel="up" title="${parents[-1]['title']|util.striptags}" href="${parents[-1]['link']|h}" />
    % endif
    % if nexttopic:
        <link rel="next" title="${nexttopic['title']|util.striptags}" href="${nexttopic['link']|h}" />
    % endif
    % if prevtopic:
        <link rel="prev" title="${prevtopic['title']|util.striptags}" href="${prevtopic['link']|h}" />
    % endif
    <!-- end layout.mako headers -->

</%block>

<div id="docs-header">
    <h1>${docstitle|h}</h1>

    <div id="docs-search">
    Search:
    <form class="search" action="${pathto('search')}" method="get">
      <input type="text" name="q" size="18" /> <input type="submit" value="${_('Search')}" />
      <input type="hidden" name="check_keywords" value="yes" />
      <input type="hidden" name="area" value="default" />
    </form>
    </div>

    <div id="docs-version-header">
        Release: <span class="version-num">${release}</span>

    </div>

</div>

<div id="docs-top-navigation">
    <div id="docs-top-page-control" class="docs-navigation-links">
        <ul>
        % if prevtopic:
            <li>Prev:
            <a href="${prevtopic['link']|h}" title="${_('previous chapter')}">${prevtopic['title']}</a>
            </li>
        % endif
        % if nexttopic:
            <li>Next:
            <a href="${nexttopic['link']|h}" title="${_('next chapter')}">${nexttopic['title']}</a>
            </li>
        % endif

        <li>
            <a href="${pathto('index')}">Table of Contents</a> |
            <a href="${pathto('genindex')}">Index</a>
        </li>
        </ul>
    </div>

    <div id="docs-navigation-banner">
        <a href="${pathto('index')}">${docstitle|h}</a>
        % if parents:
            % for parent in parents:
                » <a href="${parent['link']|h}" title="${parent['title']}">${parent['title']}</a>
            % endfor
        % endif
        % if current_page_name != 'index':
        » ${self.show_title()}
        % endif

        <h2>
            <%block name="show_title">
                ${title}
            </%block>
        </h2>
    </div>

</div>

<div id="docs-body-container">

% if withsidebar:

    <div id="docs-sidebar">
    <div id="sidebar-banner">
        ${self.bannerad()}
    </div>

    <h3><a href="${pathto('index')}">Table of Contents</a></h3>
    <div id="sidebar-toc">${toc}</div>

    % if prevtopic:
    <h4>Previous Topic</h4>
    <p>
    <a href="${prevtopic['link']|h}" title="${_('previous chapter')}">${prevtopic['title']}</a>
    </p>
    % endif
    % if nexttopic:
    <h4>Next Topic</h4>
    <p>
    <a href="${nexttopic['link']|h}" title="${_('next chapter')}">${nexttopic['title']}</a>
    </p>
    % endif

    <h4>Quick Search</h4>
    <p>
    <form class="search" action="${pathto('search')}" method="get">
      <input type="text" name="q" size="18" /> <input type="submit" value="${_('Search')}" />
      <input type="hidden" name="check_keywords" value="yes" />
      <input type="hidden" name="area" value="default" />
    </form>
    </p>

    </div>
% endif

    <div id="docs-body" class="${'withsidebar' if withsidebar else ''}" >
        ${next.body()}
    </div>

</div>

<div id="docs-bottom-navigation" class="docs-navigation-links">
    % if prevtopic:
        Previous:
        <a href="${prevtopic['link']|h}" title="${_('previous chapter')}">${prevtopic['title']}</a>
    % endif
    % if nexttopic:
        Next:
        <a href="${nexttopic['link']|h}" title="${_('next chapter')}">${nexttopic['title']}</a>
    % endif

    <div id="docs-copyright">
    % if hasdoc('copyright'):
        &copy; <a href="${pathto('copyright')}">Copyright</a> ${copyright|h}.
    % else:
        &copy; Copyright ${copyright|h}.
    % endif
    % if show_sphinx:
        Documentation generated using <a href="https://www.sphinx-doc.org">Sphinx</a> ${sphinx_version|h}
        with Mako templates.
    % endif
    </div>
</div>

</div>

<%block name="lower_scripts">

    <script type="text/javascript">
      ## see https://github.com/sphinx-doc/sphinx/commit/8e730ae303ae686705ea12f44ef11da926a87cf5
      document.documentElement.dataset.content_root = '${content_root}';

    </script>

    <!-- begin iterate through sphinx environment script_files -->
    % for scriptfile in script_files + self.attr.local_script_files:
        <script type="text/javascript" src="${pathto(scriptfile, 1)}"></script>
    % endfor
    <!-- end iterate through sphinx environment script_files -->

    <script type="text/javascript" src="${pathto('_static/init.js', 1)}"></script>

</%block>
