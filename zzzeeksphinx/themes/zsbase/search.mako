<%inherit file="layout.mako"/>

<%!
    local_script_files = ['_static/searchtools.js', '_static/language_data.js']
%>
<%block name="show_title">
    ${_('Search')}
</%block>

<div id="search-results"></div>

<%block name="footer">
    ${parent.footer()}
</%block>

<%block name="lower_scripts">
	${parent.lower_scripts()}
	<script type="text/javascript" src="searchindex.js" defer></script>
</%block>