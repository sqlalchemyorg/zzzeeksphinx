<!DOCTYPE html>

<%def name="bannerad()"></%def>

<html xmlns="http://www.w3.org/1999/xhtml">
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
        ${metatags and metatags or ''}
        <title>
            <%block name="head_title">
            </%block>
        </title>

        <%block name="css">
            <!-- begin iterate through site-imported + sphinx environment css_files -->
            % for cssfile in self.attr.default_css_files + css_files:
                <link rel="stylesheet" href="${pathto(cssfile, 1)}" type="text/css" />
            % endfor
            <!-- end iterate through site-imported + sphinx environment css_files -->
        </%block>

        <%block name="headers"/>
    </head>
    <body>
        ${next.body()}
        <%block name="footer"/>
        <%block name="lower_scripts"/>
    </body>
</html>


