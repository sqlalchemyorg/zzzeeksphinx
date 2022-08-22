## coding: utf-8

<%!
    import datetime

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
        docs-top-navigation-container ->
            docs-header ->
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
    if builder == 'epub':
        next.body()
        return
%>


<%
withsidebar = bool(toc) and (
    theme_index_sidebar is True or current_page_name != 'index'
)
%>

<%block name="head_title">
    % if theme_index_sidebar or current_page_name != 'index':
    ${capture(self.show_title) | util.striptags} &mdash;
    % endif
    ${docstitle|h}
</%block>

<%def name="show_title()">
    ${title}
</%def>


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


<div id="docs-top-navigation-container" class="body-background">
<div id="docs-header">
    <div id="docs-version-header">
        Release: <span class="version-num">${release}</span>

        % if is_beta_version:
            <span id="sidebar-beta">beta release</span>
        % elif is_prerelease_version:
            <span id="sidebar-prerelease">${"in development" if not release_date else "pre release"}</span>
        % elif is_legacy_version:
            <span id="sidebar-legacy">legacy version</span>
        % elif is_current_version:
            <span id="sidebar-current">current release</span>
        % endif

        % if release_date:
        | Release Date: ${release_date}
        % else:
        | Release Date: <b>not released yet</b>
        % endif

    </div>

    <h1><a href="${pathto('index')}">${docstitle|h}</a></h1>

</div>
</div>

<div id="docs-body-container">

    <div id="fixed-sidebar" class="${'withsidebar' if withsidebar else ''}">

    % if not withsidebar:
        <div id="index-nav">
            <form class="search" action="${pathto('search')}" method="get">
              <label>
                 Search terms:
              <input type="text" placeholder="search..." name="q" size="12" />
              </label>
              <input type="submit" value="${_('Search')}" />
              <input type="hidden" name="check_keywords" value="yes" />
              <input type="hidden" name="area" value="default" />
            </form>

            <p>
            <a href="${pathto('contents')}">Contents</a> |
            <a href="${pathto('genindex')}">Index</a>
            % if zip_url:
            | <a href="${zip_url}">Download this Documentation</a>
            % endif
            </p>

        </div>
    % endif

    % if withsidebar:

        <div id="docs-sidebar-popout">
            <h3><a href="${pathto('index')}">${docstitle|h}</a></h3>
            % if is_beta_version:
                <p id="sidebar-beta">beta release</p>
            % elif is_prerelease_version:
                <p id="sidebar-prerelease">${"in development" if not release_date else "pre release"}</p>
            % elif is_legacy_version:
                <p id="sidebar-legacy">legacy version</p>
            % elif is_current_version:
                <p id="sidebar-current">current release</p>
            % endif
            <p id="sidebar-topnav">
                <a href="${pathto('index')}">Home</a>
                % if zip_url:
                | <a href="${zip_url}">Download this Documentation</a>
                % endif
            </p>

            <div id="sidebar-search">
                <form class="search" action="${pathto('search')}" method="get">
                  <label>
                  Search terms:
                  <input type="text" placeholder="search..." name="q" size="12" />
                  </label>
                  <input type="hidden" name="check_keywords" value="yes" />
                  <input type="hidden" name="area" value="default" />
                </form>
            </div>

        </div>

        <div id="docs-sidebar">

        <div id="sidebar-banner">
            ${parent.bannerad()}
        </div>

        <div id="docs-sidebar-inner">

        <%
            breadcrumb = parents[:]
            if not breadcrumb or breadcrumb[0]['link'] != pathto('index'):
                breadcrumb = [{'link': pathto('index'), 'title': docstitle}] + breadcrumb

            if len(breadcrumb) > 1:
                breadcrumb = breadcrumb[1:]
            h3_toc_item = breadcrumb[0]
            if len(breadcrumb) > 1:
                outermost_link_item = breadcrumb[1]['link']
            elif not parents:
                outermost_link_item = None
            else:
                outermost_link_item = ''

        %>
        <h3>
            <a href="${h3_toc_item['link']|h}" title="${h3_toc_item['title']}">${h3_toc_item['title']}</a>
        </h3>

        ${parent_toc(
            current_page_name,
            outermost_link_item)}

        % if rtd:
        <h4>Project Versions</h4>
        <ul class="version-listing">
            <li><a href="${pathto('index')}">${release}</a></li>
        </ul>
        % endif

        </div>

        </div>
    % endif

    </div>

    <div id="narrow-index-nav">
        <form class="search" action="${pathto('search')}" method="get">
            <label>
                Search terms:
            <input type="text" placeholder="search..." name="q" size="12" />
            </label>
            <input type="submit" value="${_('Search')}" />
            <input type="hidden" name="check_keywords" value="yes" />
            <input type="hidden" name="area" value="default" />
        </form>

        <p>
        <a href="${pathto('index')}">Home</a>
        % if zip_url:
        | <a href="${zip_url}">Download this Documentation</a>
        % endif
        </p>

    </div>

    % if withsidebar:

        <div id="docs-narrow-top-navigation">
            <ul>
            % if prevtopic:
                <li><b>Previous:</b>
                <a href="${prevtopic['link']|h}" title="${_('previous chapter')}">${prevtopic['title']}</a></li>
            % endif
            % if nexttopic:
                <li><b>Next:</b>
                <a href="${nexttopic['link']|h}" title="${_('next chapter')}">${nexttopic['title']}</a></li>
            % endif

            <li><b>Up:</b> <a href="${pathto('index')}">Home</a></li>
            % if parents:
                % for _parent in parents:
                    <ul><li><a href="${_parent['link']|h}" title="${_parent['title']}">${_parent['title']}</a></li>
                % endfor
            % endif
            % for _parent in parents:
                </ul>
            % endfor



            <li><b>On this page:</b></li>
            ${local_toc(current_page_name, apply_exact_top_anchor=True)}

            </ul>

        </div>

    % endif


    <div id="docs-body" role="main" class="${'withsidebar' if withsidebar else ''} ${current_page_name.replace("/", "-")}" >
        ${next.body()}
    </div>

</div>

<div id="docs-bottom-navigation" class="docs-navigation-links${', withsidebar' if withsidebar else ''}">
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


    <p><b>flambé!</b> the dragon and <b><i>The Alchemist</i></b> image designs created and generously donated by <a href="https://github.com/vmalloc">Rotem Yaari</a>.</p>

    % if show_sphinx:
        Created using <a href="http://sphinx.pocoo.org/">Sphinx</a> ${sphinx_version|h}.
    % endif

    Documentation last generated: ${datetime.datetime.now().strftime("%c")}

    </div>
</div>

</div>

<%block name="lower_scripts">

    <script type="text/javascript">
      var DOCUMENTATION_OPTIONS = {
          URL_ROOT:    '${pathto("", 1)}',
          VERSION:     '${release|h}',
          COLLAPSE_MODINDEX: false,
          FILE_SUFFIX: '${file_suffix}'
      };
    </script>

    <script type="text/javascript" id="documentation_options" data-url_root="${ pathto('', 1) }" src="${ pathto('_static/documentation_options.js', 1) }"></script>

    <!-- begin iterate through sphinx environment script_files -->
    % for scriptfile in script_files + self.attr.local_script_files:
        <script type="text/javascript" src="${pathto(scriptfile, 1)}"></script>
    % endfor
    <!-- end iterate through sphinx environment script_files -->

    <script type="text/javascript" src="${pathto('_static/init.js', 1)}"></script>

</%block>
