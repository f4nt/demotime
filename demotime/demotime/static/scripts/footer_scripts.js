// Initialize lightboxes
$('.lightboxed').fancybox();

// Set focus on pageload
$('.content input[type="text"]').first().focus();

// Slide toggle summary boxes
$('.summary a').click(function(event) {
    event.preventDefault();
    $(this).parents('.summary').next().slideToggle();
});

// Dynamically add additional attachments
$('.attachment-add').click(function(event) {
    event.preventDefault();
    $(this).parents('section').next().slideDown();
});

// Linkify URLs
$('blockquote p, .review-overview li, .review-overview p').linkify({
    target: "_blank"
});

// Initialize tooltips
$('.tooltip').tooltipster();

// Initialized button clicks
$('button').click(function() {
    if ($(this).data('href')) {
        window.location.href = $(this).data('href');
    }
});

// Smooth scroll to links
var ScrollToLink = new DemoTime.ScrollToLink();

// Handle review form submits (some light validation on attachments)
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

    if (!proceed) {
        e.preventDefault();
        sweetAlert("Sorry...", "Please select an attachment type.", "error");
    } else {
        swal ({
            title: "Updating review",
            text: "Just a sec...",
            type: "success",
            showConfirmButton: false
        });
    }
});

// Attach 'markdown supported' links after wysiwyg boxes
setTimeout(function() {
    $('.markItUpEditor').after('<div class="mdhelper"><a href="/markdown" target="_blank" class="mdhelper">Markdown supported</a></div>');
}, 1);

$('textarea').keypress(function() {
    window.addEventListener("beforeunload", function (e) {
        var confirmationMessage = "You have unsaved work. Are you sure you want to close Demotime?";

        (e || window.event).returnValue = confirmationMessage; //Gecko + IE
        return confirmationMessage;                            //Webkit, Safari, Chrome
    });
});
