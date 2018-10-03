<%inherit file="layout.mako"/>

<%!
    local_script_files = ['_static/searchtools.js']
%>
<%block name="show_title">
    ${_('Page not found')}
</%block>

<h1>Page Not Found!</h1>

<p>Can't find the page you're looking for.</p>



<%block name="footer">
    ${parent.footer()}
</%block>

