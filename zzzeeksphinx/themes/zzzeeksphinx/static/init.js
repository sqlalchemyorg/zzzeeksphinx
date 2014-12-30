
function initSQLPopups() {
    $('div.popup_sql').hide();
    $('a.sql_link').click(function() {
        $(this).nextAll('div.popup_sql:first').toggle();
        return false;
    });
}

function initFloatyThings() {

    // we use a "fixed" positioning for the sidebar regardless
    // of whether or not we are moving with the page or not because
    // we want it to have an independently-moving scrollbar at all
    // times.
    // this unfortunately means we have to keep it steady across
    // page scrolls, vertically and horizontally, in negative scrolls
    // as well for safari + chrome and also handle resizes.  these browsers
    // all do something a little different with positioning and jquery
    // does not seem to abstract against this use case well.

    var automatedBreakpoint = $("#docs-container").position().top +
        $("#docs-top-navigation-container").height();

    // "top" seems to stay constant...
    var docsBodyOffset = $("#docs-body").offset().top;

    var top = docsBodyOffset;
    var left;

    function resize() {
        // ...while the "left" seems to change based on doc
        // resizes, e.g. if you make the safari window lots bigger
        // than the page
        left = $("#docs-body-container").offset();
        if (left) {
            left = left.left;
        } // otherwise might be undefined
        else {
            left = 0;
        }
        setScroll();
    }

    // this turns on the whole thing, without this
    // we are in graceful degradation assuming no JS
    $("#fixed-sidebar.withsidebar").addClass("preautomated");

    function setScroll() {
        var scrolltop = $(window).scrollTop();
        var scrollleft = $(window).scrollLeft();

        // when page is scrolled down past the top headers,
        // sidebar stays fixed vertically
        if (scrolltop >= automatedBreakpoint) {
            $("#fixed-sidebar.withsidebar").css("top", 5);
        }
        else if (scrolltop < 0) {
            // special trickery to deal with safari vs. chrome
            // acting differently in this case, while avoiding using jquery's
            // weird / slow? offset() setter
            if ($("#fixed-sidebar.withsidebar").offset().top != docsBodyOffset) {
                $("#fixed-sidebar.withsidebar").css(
                    "top", docsBodyOffset - scrolltop);
            }
        }
        else {
            $("#fixed-sidebar.withsidebar").css(
                "top", docsBodyOffset - scrolltop);
        }

        // adjust left scroll.
        // chrome has a "springy" zone in its scrollbar that does
        // not actually move the elements, and this basically means we
        // are breaking the spacing in those zones,  so the navbar "springs"
        // around with this action.   jquery needs to provide a
        // "what is the actual position of the *document* in response to
        // scrolling" feature, not just the raw value of a scrollbar.
        $("#fixed-sidebar.withsidebar").css(
            "left", left - scrollleft);
    }
    $(window).scroll(setScroll);
    $(window).resize(resize);

    resize();
}

function highlightLinks() {
    function bisection(x){
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
    $("div.section").each(function(index) {
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


$(document).ready(function() {
    initSQLPopups();
    if (!$.browser.mobile) {
        initFloatyThings();
        highlightLinks();
    }
});

