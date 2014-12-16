class TOCMixin(object):
    def get_current_subtoc(self, current_page_name, current_page_title):
        """Return a TOC for sub-files and sub-elements of the current file.

        This is to provide a "contextual" navbar that shows the current page
        in context of all of its siblings, not just the immediate "previous"
        and "next".

        This allows a very long page with many sections to be broken
        into smaller pages while not losing the navigation of the overall
        section, with the added bonus that only the page-level bullets for
        the current subsection are expanded, thus making for a much shorter,
        "drill-down" style navigation.

        """

        raw_tree = self.app.env.get_toctree_for(
            current_page_name, self.app.builder, True, maxdepth=0)
        local_tree = self.app.env.get_toc_for(
            current_page_name, self.app.builder)

        def _locate_nodes(nodes, level, outer=True):
            # this is a lazy way of getting at all the info in a
            # series of docutils nodes, with an absolute mimimal
            # reliance on the actual structure of the nodes.
            # we just look for refuris and the fact that a node
            # is dependent on another somehow, that's it, then we
            # flatten it out into a clean "tree" later.
            # An official Sphinx feature/extension
            # here would probably make much more use of direct
            # knowledge of the structure
            for elem in nodes:

                if hasattr(elem, 'attributes'):
                    refuri = elem.attributes.get('refuri', None)
                else:
                    refuri = None

                name = None
                if refuri is not None:
                    name = elem.children[0].rawsource
                    remainders = elem.children[1:]
                    # a little bit of extra filtering of when/where
                    # we want internal nodes vs. page-level nodes,
                    # this is usually not needed except in a certain
                    # edge case
                    if (
                        not outer and refuri.startswith("#")
                    ) or (
                        outer and "#" not in refuri
                    ):
                        yield level, refuri, name
                else:
                    remainders = elem.children

                # try to embed the item-level get_toc_for() inside
                # the file-level get_toctree_for(), otherwise if we
                # just get the full get_toctree_for(), it's enormous.
                if outer and name == current_page_title:
                    for ent in _locate_nodes([local_tree], level + 1, False):
                        yield ent
                else:
                    for ent in _locate_nodes(
                        remainders, level + 1, outer):
                        yield ent

        def _organize_nodes(nodes):
            stack = []
            levels = []
            for level, refuri, name in nodes:
                if not levels or levels[-1] < level:
                    levels.append(level)
                    new_collection = []
                    if stack:
                        stack[-1].append(new_collection)
                    stack.append(new_collection)
                elif level < levels[-1]:
                    while levels and level < levels[-1]:
                        levels.pop(-1)
                        if level > levels[-1]:
                            levels.append(level)
                        else:
                            stack.pop(-1)

                stack[-1].append((refuri, name))
            return stack

        def _render_nodes(stack, searchfor, level=0, nested_element=False):
            # this is me being lazy about dealing with docutils renderers,
            # and just programmatically rendering out.  A real Sphinx
            # extension / feature would obviously need to use the idiomatic
            # docutils renderers.
            if stack:
                indent = " " * level
                printing = nested_element or searchfor in stack
                if printing:
                    yield (" " * level) + "<ul>"
                while stack:
                    elem = stack.pop(0)
                    as_links = searchfor != elem
                    if isinstance(elem, tuple):
                        if not stack or isinstance(stack[0], tuple):
                            if printing:
                                if as_links:
                                    yield "%s<li><a href='%s'>%s</a></li>" % (
                                        (indent,) + elem)
                                else:
                                    yield "%s<li><strong>%s</strong></li>" % (
                                        indent, elem[1])
                        elif isinstance(stack[0], list):
                            if printing:
                                if as_links:
                                    yield "%s<li><a href='%s'>%s</a>" % (
                                        (indent,) + elem)
                                else:
                                    yield "%s<li><strong>%s</strong>" % (
                                        indent, elem[1])
                            for sub in _render_nodes(
                                    stack[0], searchfor,
                                    level=level + 1,
                                    nested_element=nested_element or
                                    searchfor == elem):
                                yield sub
                            if printing:
                                yield (" " * level) + "</li>"
                    elif isinstance(elem, list):
                        for sub in _render_nodes(
                                elem, searchfor,
                                level=level + 1,
                                nested_element=nested_element):
                            yield sub
                if printing:
                    yield (" " * level) + "</ul>"

        return "\n".join(
            _render_nodes(
                _organize_nodes(_locate_nodes([raw_tree], 0)),
                ('', current_page_title)
            )
        )
