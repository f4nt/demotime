// Dynamically add/remove reviewers
DemoTime.Wysiwyg = Backbone.View.extend({
    el: 'body',

    events: {
        'click .add_emoji': 'add'
    },

    initialize: function(options) {
        this.options = options;

        $('textarea').wysiwyg({
            buttons: {
                insertimage: {
                    image: '\uf030'
                },
                bold: {
                    title: 'Bold (Ctrl+B)',
                    image: '\uf032',
                    hotkey: 'b'
                },
                italic: {
                    title: 'Italic (Ctrl+I)',
                    image: '\uf033',
                    hotkey: 'i'
                },
                underline: {
                    title: 'Underline (Ctrl+U)',
                    image: '\uf0cd',
                    hotkey: 'u'
                },
                strikethrough: {
                    title: 'Strikethrough (Ctrl+S)',
                    image: '\uf0cc',
                    hotkey: 's'
                },
                forecolor: {
                    title: 'Text color',
                    image: '\uf1fc'
                },
                highlight: {
                    title: 'Background color',
                    image: '\uf043'
                },
                orderedList: {
                    title: 'Ordered list',
                    image: '\uf0cb',
                    showselection: false
                },
                unorderedList: {
                    title: 'Unordered list',
                    image: '\uf0ca',
                    showselection: false
                },
                removeformat: {
                    title: 'Remove format',
                    image: '\uf12d'
                }
            },
            submit: {
                title: 'Submit',
                image: '\uf00c'
            },
            selectImage: 'Click or drop image',
            placeholderUrl: 'http://example.com/some.gif',
            maxImageSize: [600,600]
        });

        this.fix_tab_index();

        this.render();
    },

    // focus the wysiwyg when the input prior to hits TAB
    fix_tab_index: function() {
        var wysiwyg_form_group = this.$el.find('.wysiwyg-editor').parents('.form-group'),
            previous_input = wysiwyg_form_group.prev('.form-group').find('input');

        previous_input.keydown(function(event) {
            if (event.keyCode == 9) {
                event.preventDefault();
                wysiwyg_form_group.find('.wysiwyg-editor').focus();
            }
        });
    },

    // Add the custom footer to wysiwygs (emoticons)
    render: function() {
        var self = this;
        setTimeout(function() {
            // Grab the container template
            var html = $('#wysiwyg_footer').html(),
                template = _.template(html);
            template = template();

            self.$el.find('.wysiwyg-container').append(template);
        }, 1000);
    },

    // Emoticon click-to-add event
    add: function(event) {
        var img = $(event.target),
            self = this;

        img.parents('.wysiwyg-container').find('textarea').wysiwyg('shell').insertHTML("<img class='emoji' width='30' height='30' src='" + self.options.dt_url + img.attr('src') + "'>").trigger('keyup');
    }
});
