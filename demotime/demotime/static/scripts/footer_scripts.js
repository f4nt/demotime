var DemoTime = [];

// AnalyteUI.View.ScrollToLink()
DemoTime.ScrollToLink = Backbone.View.extend({
    el: 'body',

    events: {
        'click a': 'clicked'
    },

    initialize: function() {
        this.$url = window.location.href;

        // On pageload, jump to a link, if it exists
        if (this.$url.indexOf('#') > -1 && this.$url.split('#')[1]) {
            this.jump_to_link(this.$url.split('#')[1], 1000);
        } else {
            // otherwise, return
            return true;
        }
    },

    clicked: function(event) {
        var $l = $(event.target),
            $h = $l.attr('href');

        // check for a valid link
        if (!$h || $h == '#' || $h.indexOf('#') == -1 || $l.data('blockable')) return;

        event.preventDefault();
        var $u = $h;

        // Get url and target
        $u = $h.split('#')[0];
        target = $h.split('#')[1];

        // See if target path matches current path
        if ((!$u) || window.location.pathname == $u) {
            // the target's on this page! set URL in url bar and jump to it
            window.history.pushState('object or string', $l.html(), $h);
            this.jump_to_link(target);
        } else {
            // Otherwise just load the url
            window.location.href = $h;
        }

        return true;
    },

    jump_to_link: function (target, timeout) {
        // Perform the actual jump to a link
        //
        // Set a default timeout before animation of 0
        var timeout = timeout || 0;

        // Sometimes we use name='blah' other times
        // we target an ID. So lets look for names first, then
        // fall back to IDs.
        if ($('[name=' + target + ']').length) {
            target = $('[name=' + target + ']');
        } else {
            target = $('#' + target);
        }

        setTimeout(function () {
            // Animate to the element
            if (target.length) {
                $('html, body').animate({
                    scrollTop: target.offset().top - 35
                }, 500);
            }
            // Sometimes we travel to a 'collapsed' element. if we do,
            // expand it.
            if (target.first().hasClass('collapsed')) {
                target.find('[data-ui-toggle-handle]').trigger('click');
            }
        }, timeout);
    }
});

$('.lightboxed').fancybox();
$('.content input[type="text"]').first().focus();

$('.summary a').click(function(event) {
    event.preventDefault();
    $(this).parents('.summary').next().slideToggle();
});

$('.attachment-add').click(function(event) {
    event.preventDefault();
    $(this).parents('section').next().slideDown();
});

$('.tooltip').tooltipster();

$('button').click(function() {
    if ($(this).data('href')) {
        window.location.href = $(this).data('href');
    }
});

var ScrollToLinks = new DemoTime.ScrollToLink();

$('.review form').submit(function(e) {
    var form = $(this),
        proceed = true;

    $('.attachment-container:visible').each(function() {
        var select = $(this).find('.attachment-type select'),
            file = $(this).find('.attachment-file input');

        if (!select.val() && file.val()) {
            proceed = false;
        }
    });

    if (proceed) {
        form.submit();
    } else {
        e.preventDefault();
        sweetAlert("Sorry...", "Please select an attachment type.", "error");
    }
});
