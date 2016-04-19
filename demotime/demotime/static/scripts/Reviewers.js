var ReviewerModel = Backbone.Model.extend();
// Dynamically add/remove reviewers
DemoTime.Reviewers = Backbone.View.extend({
    el: 'body',

    events: {
        'keyup .find_person': 'typing',
        'click .add_person_click': 'add',
        'click .person_deleter': 'delete',
        'click .cancel': 'cancel'
    },

    initialize: function(options) {
        this.options = options;
    },

    cancel: function() {
        this.$el.find('.find_person').val('');
    },

    typing: function(event) {
        var $input = $(event.target),
            self = this;

        if (event.keyCode == 27) {
            $input.val('');
        }

        if ($input.val().length > 2 && String.fromCharCode(event.keyCode).match(/[a-zA-Z]/i)) {
            var req = $.ajax({
                url: self.options.url,
                method: 'POST',
                data: {
                    action: $input.data('action'),
                    review_pk: self.options.review_pk,
                    name: $input.val()
                }
            });

            req.success(function(data) {
                self.people = new ReviewerModel(data);

                if (self.people.get('users').length) {
                    // Grab the container template (reviewers vs. followers)
                    if ($input.data('action') == 'find_reviewer') {
                        var html = $('#new_reviewers').html(),
                            template = _.template(html);
                    } else {
                        var html = $('#new_followers').html(),
                            template = _.template(html);
                    }

                    template = template({ person: self.people.get('users') });

                    swal ({
                        title: "Found matches",
                        text: template,
                        type: "success",
                        showConfirmButton: false,
                        showCancelButton: true,
                        html: true
                    });
                } else {
                    sweetAlert("Sorry...", "No matches found.", "error");
                    $input.val('');
                }
            });
        }
    },

    add: function(event) {
        var link = $(event.target),
            pk = link.data('reviewer'),
            self = this;

        event.preventDefault();

        var req = $.ajax({
            url: self.options.url,
            method: 'POST',
            data: {
                action: link.data('action'),
                review_pk: self.options.review_pk,
                user_pk: pk
            }
        });

        req.always(function() {
            swal.close();
        });
        req.success(function(data) {
            self.person= new ReviewerModel(data);

            // Grab the container template
            if (data.reviewer_name) {
                var html = $('#added_reviewer').html(),
                    template = _.template(html);

                template = template({ person: self.person });

                self.$el.find('.reviewer_ul').append(template);
            } else {
                var html = $('#added_follower').html(),
                    template = _.template(html);

                template = template({ person: self.person });

                self.$el.find('.follower_ul').append(template);
            }

            self.$el.find('.find_person_li input').val('');

        });
        req.error(function(err) {
            swal ({
                title: 'Whoops',
                type: 'error',
                text: 'Your request was denied: ' + err,
                html: true
            });
        });
    },

    delete: function(event) {
        event.preventDefault();
        var $el = $(event.target),
            $li = $el.parents('li'),
            pk = $el.data('person'),
            self = this;

        var req = $.ajax({
            url: self.options.url,
            method: 'POST',
            data: {
                action: $el.data('action'),
                review_pk: self.options.review_pk,
                user_pk: pk
            }
        });

        req.success(function() {
            $li.slideUp();
        });

        req.error(function(err) {
            swal ({
                title: 'Whoops',
                type: 'error',
                text: 'Your request was denied: ' + err,
                html: true
            });
        });
    }
});
