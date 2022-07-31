
function initSQLPopups() {
    /* initializes the [SQL] popup buttons that are in the 1.x tutorials.
       Currently this toggle is disabled and the SQL display is fixed at
       visible.
    */
    $('div.popup_sql').hide();
    $('a.sql_link').click(function () {
        $(this).nextAll('div.popup_sql:first').toggle();
        return false;
    });
}

function collapseDocStrings() {
    var collapse_classes = false;
    var collapse_functions_etc = false;

    var all_not_classes =
        "dl.py.method," +
        "dl.py.classmethod," +
        "dl.py.attribute";

    if (collapse_functions_etc) {
        all_not_classes += ", "
        "dl.py.function," +
            "dl.py.exception," +
            "dl.py.data";
    }


    var hash = null;
    var maintain_symbol = "";
    if (location.hash) {
        // omit # symbol at position 0
        hash = location.hash.substring(1,);

        params_token = hash.indexOf(".params.")
        if (params_token != -1) {
            maintain_symbol = hash.substring(0, params_token)
        }
    }


    if (collapse_classes) {
        $("dl.py.class > dd").children(":not(dl)").hide();
    }

    $(all_not_classes).children("dd").children().hide();


    $("dl.py > dd > p:first-of-type").show()

    var moretext = "more..."
    var lesstext = "less"
    var autodoc_collapse = "<a class='autodoc-collapse'>" + moretext + "</a>"

    if (collapse_classes) {
        $("dl.py.class").
            children("dt").
            append(autodoc_collapse);

    }
    $(all_not_classes).children("dt").append(autodoc_collapse);

    function showmore(target) {
        $(target).
            parent("dt").
            next("dd").
            children(":not(p:first-of-type , .autodoc-collapse , dl.py)").
            toggle();
        var text = $(target).text();
        var grew = text == moretext;
        $(target).text(grew ? lesstext : moretext);
        return grew;
    }

    if (maintain_symbol) {
        showmore($("dt[id='" + maintain_symbol + "'], dt[id='" + maintain_symbol + ".__init__']").children(".autodoc-collapse"))
    }


    $('a.autodoc-collapse').
        prev("a.headerlink").
        click(
            function () { showmore($(this).next(".autodoc-collapse")) }
        );
    $('a.autodoc-collapse').click(function () {
        // empty div in layout.mako set to None in css for
        // narrow media.  the jquery scrolling doesn't seem to work
        // in android so just shut it off
        var is_mobile = $("#mobile-element").css("display") == "none";

        if (showmore(this) && !is_mobile) {
            var hash = $(this).parent("dt").attr("id");
            var aTag = $("*[id='" + hash + "']");
            if (aTag) {
                $(window).scrollTop(aTag.offset().top);
            }
        }

    });

    // navigate to current hash as we have resized things
    if (hash) {
        var aTag = $("*[id='" + hash + "']");
        if (aTag) {
            $(window).scrollTop(aTag.offset().top);
        }
    }

}



_debug = false;

function initFloatyThings() {
    /* switches the left navbar between css fixed and css flowing */

    if (_debug) {
        console.log("initfloatingthing");
    }
    if (!$("#fixed-sidebar.withsidebar")) {
        if (_debug) {
            console.log("no side bar, returning")
        }
        return;
    }

    if (_debug) {
        console.log("sidebar, doing things");
    }

    var docsBodyOffset;
    var padding;
    var automatedBreakpoint;

    /*

        Before the introduction of responsive design which adds vertical
        elements when the window shrinks past a threshold, the
        variables here could be fixed.   however, we now have to recalculate
        them when the window resizes since the rendered height of the
        top of the page can change.

        It's likely that the whole thing can just be in one function that
        runs for the resize and scroll events together, and that would be fine.
        It's unknown if jquery calls like css_element.height() are expensive
        or not on different browsers.  it all certainly seems to be
        faster than instantaneous on any browser here.


     */
    function setScrollWithRecalc() {
        docsBodyOffset = $("#docs-body").offset().top;

        padding = docsBodyOffset -
            ($("#docs-top-navigation-container").offset().top +
                $("#docs-top-navigation-container").height());

        automatedBreakpoint = $("#docs-container").position().top +
            $("#docs-top-navigation-container").height();

        if (_debug) {
            console.log("new breakpoint " + automatedBreakpoint);
        }
        setScroll();
    }

    function setScroll() {
        var scrolltop = $(window).scrollTop();
        var fix = scrolltop >= automatedBreakpoint;

        if (_debug) {
            console.log(
                "scrolltop: " + scrolltop + " breakpoint: " + automatedBreakpoint
            );
        }

        if (fix) {
            $("#fixed-sidebar.withsidebar").css("top", padding);
            $("#fixed-sidebar.withsidebar").css("position", "fixed");
            $("#fixed-sidebar.withsidebar").css("height", '');
            if (_debug) {
                console.log("setting fixed sidebar, padding: " + padding);
            }
        }
        else {
            $("#fixed-sidebar.withsidebar").css("top", 0);
            $("#fixed-sidebar.withsidebar").css(
                "height", $(window).height() - docsBodyOffset + scrolltop);
            $("#fixed-sidebar.withsidebar").css("position", "absolute");
            if (_debug) {
                console.log("setting flowing sidebar");
            }
        }
    }

    $(window).scroll(setScroll);
    $(window).resize(setScrollWithRecalc);
    setScrollWithRecalc();
}

function highlightLinks() {
    /* Highlights the active section in the left navbar */

    function bisection(x) {
        var low = 0;
        var high = divCollection.length;

        var mid;

        while (low < high) {
            mid = (low + high) >> 1;

            if (x < divCollection[mid]['active']) {
                high = mid;
            } else {
                low = mid + 1;
            }
        }

        return low;
    }

    var divCollection = [];
    var currentIdx = -1;
    var docHeight = $(document).height();
    $("div.section,section").each(function (index) {
        var active = $(this).offset().top - 20;
        divCollection.push({
            'id': this.id,
            'active': active,
        });
    });

    function setLink() {
        var windowPos = $(window).scrollTop();
        var windowHeight = $(window).height();

        var idx;
        if (windowPos + windowHeight == docHeight) {
            idx = divCollection.length;
        }
        else {
            idx = bisection(windowPos);
        }

        if (idx != currentIdx) {
            var effectiveIdx = Math.max(0, idx - 1);
            currentIdx = idx;

            var ref;
            if (effectiveIdx == 0) {
                ref = '';
            }
            else {
                ref = divCollection[effectiveIdx]['id'];
            }
            $("#docs-sidebar li.current").removeClass('current');
            $("#docs-sidebar li a.reference[href='#" + ref + "']").parents("li").first().addClass('current');
        }
    }

    $(window).scroll(setLink);
    setLink();
}


$(document).ready(function () {
    collapseDocStrings();
    initFloatyThings();
    highlightLinks();
});

