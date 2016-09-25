from django.shortcuts import get_object_or_404, redirect
from django.forms import formset_factory
from django.views.generic import TemplateView, DetailView, ListView, RedirectView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from demotime import constants, forms, models
from demotime.views import CanViewMixin, CanViewJsonView, JsonView


class ReviewDetail(CanViewMixin, DetailView):
    template_name = 'demotime/review.html'
    model = models.Review

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.project = None
        self.review = None
        self.revision = None
        self.comment = None
        self.comment_form = None
        self.attachment_form = None

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(
            models.Project,
            slug=self.kwargs['proj_slug']
        )
        if self.kwargs.get('rev_num'):
            try:
                self.revision = models.ReviewRevision.objects.get(
                    number=self.kwargs['rev_num'],
                    review__pk=self.kwargs['pk']
                )
            except models.ReviewRevision.DoesNotExist:
                review = get_object_or_404(
                    models.Review,
                    pk=kwargs['pk'],
                )
                return redirect(
                    'review-rev-detail',
                    proj_slug=self.project.slug,
                    pk=review.pk,
                    rev_num=review.revision.number,
                )
        else:
            self.revision = self.get_object().revision

        self.review = self.revision.review
        self.comment = models.Comment(
            commenter=self.request.user
        )
        self.attachment_form = None
        self.comment_form = None
        models.MessageBundle.objects.filter(
            owner=request.user,
            review=self.revision.review
        ).update(read=True)
        return super(ReviewDetail, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ReviewDetail, self).get_context_data(**kwargs)
        try:
            reviewer = models.Reviewer.objects.get(
                review=self.revision.review,
                reviewer=self.request.user
            )
        except models.Reviewer.DoesNotExist:
            reviewer = None
        else:
            context['reviewer_status_form'] = forms.ReviewerStatusForm(
                reviewer, initial={
                    'reviewer': reviewer,
                    'review': reviewer.review
                }
            )

        if self.request.user == self.revision.review.creator:
            context['review_state_form'] = forms.ReviewStateForm(
                self.request.user,
                self.revision.review.pk,
                initial={'review': self.revision.review}
            )

        if self.revision.review.reviewer_set.filter(reviewer=self.request.user).exists():
            context['reviewer'] = self.revision.review.reviewer_set.get(
                reviewer=self.request.user
            )

        models.UserReviewStatus.objects.filter(
            review=self.revision.review,
            user=self.request.user,
        ).update(read=True)
        context['project'] = self.project
        context['revision'] = self.revision
        if self.comment_form:
            context['comment_form'] = self.comment_form
        else:
            context['comment_form'] = forms.CommentForm(instance=self.comment)
        if self.attachment_form:
            context['attachment_form'] = self.attachment_form
        else:
            context['attachment_form'] = forms.AttachmentForm(
                initial={'sort_order': 1}
            )
        return context

    def post(self, request, *args, **kwargs):
        thread = None
        if request.POST.get('thread'):
            if self.revision.commentthread_set.filter(
                    pk=request.POST.get('thread')
            ):
                thread = models.CommentThread.objects.get(pk=request.POST['thread'])

        self.comment_form = forms.CommentForm(
            thread=thread, data=request.POST, instance=self.comment
        )
        self.attachment_form = forms.AttachmentForm(data=request.POST, files=request.FILES)
        data = {}
        if self.comment_form.is_valid():
            data = self.comment_form.cleaned_data
        else:
            return self.get(request, *args, **kwargs)

        if self.attachment_form.is_valid():
            data.update(self.attachment_form.cleaned_data)

        obj = self.get_object()
        data['commenter'] = self.request.user
        data['review'] = obj.revision
        models.Comment.create_comment(**data)
        return redirect(obj.get_absolute_url())


class CreateReviewView(TemplateView):
    template_name = 'demotime/create_review.html'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.project = None
        self.review = None
        self.review_inst = None
        self.comment_form = None
        self.review_form = None
        self.attachment_forms = None

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(
            models.Project,
            slug=kwargs['proj_slug']
        )
        if kwargs.get('pk'):
            self.review_inst = get_object_or_404(models.Review, pk=kwargs['pk'])
            self.project = self.review_inst.project
            self.template_name = 'demotime/edit_review.html'
        else:
            self.review_inst = models.Review(
                creator=self.request.user,
                project=self.project,
            )
        return super(CreateReviewView, self).dispatch(request, *args, **kwargs)

    def post(self, request, pk=None, *args, **kwargs):
        self.review_form = forms.ReviewForm(
            user=self.request.user,
            instance=self.review_inst,
            project=self.project,
            data=request.POST
        )
        # pylint: disable=invalid-name
        AttachmentFormSet = formset_factory(
            forms.AttachmentForm, extra=10, max_num=25
        )
        self.attachment_forms = AttachmentFormSet(
            data=request.POST,
            files=request.FILES
        )
        if self.review_form.is_valid() and self.attachment_forms.is_valid():
            data = self.review_form.cleaned_data
            data['creator'] = request.user
            data['project'] = self.project
            data['attachments'] = []
            state = data['state']
            for form in self.attachment_forms.forms:
                if form.cleaned_data:
                    if not form.cleaned_data['attachment']:
                        continue
                    data['attachments'].append({
                        'attachment': form.cleaned_data['attachment'],
                        'attachment_type': form.cleaned_data['attachment_type'],
                        'description': form.cleaned_data['description'],
                        'sort_order': form.cleaned_data['sort_order'],
                    })

            if pk:
                review = models.Review.update_review(self.review_inst.pk, **data)
            else:
                review = models.Review.create_review(**data)

            return redirect(
                'review-rev-detail',
                proj_slug=review.project.slug,
                pk=review.pk,
                rev_num=review.revision.number
            )
        return self.get(request, *args, **kwargs)

    def get(self, request, pk=None, *args, **kwargs):
        if request.method == 'GET':
            # If we're using this method as the POST error path, let's
            # preserve the existing forms. Also, maybe this is dumb?
            if pk:
                self.review_inst = get_object_or_404(models.Review, pk=pk)
                self.template_name = 'demotime/edit_review.html'
            else:
                self.review_inst = models.Review(creator=self.request.user)
            self.review_form = forms.ReviewForm(
                user=self.request.user,
                instance=self.review_inst,
                project=self.project,
                initial={'description': ''},
            )
            # pylint: disable=invalid-name
            AttachmentFormSet = formset_factory(
                forms.AttachmentForm, extra=10, max_num=25
            )
            initial_data = [
                {'sort_order': x} for x in range(1, AttachmentFormSet.extra + 1)
            ]
            self.attachment_forms = AttachmentFormSet(initial=initial_data)
        return super(CreateReviewView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CreateReviewView, self).get_context_data(**kwargs)
        context.update({
            'project': self.project,
            'review_form': self.review_form,
            'review_inst': self.review_inst,
            'attachment_forms': self.attachment_forms
        })
        return context


class ReviewListView(ListView):

    template_name = 'demotime/demo_list.html'
    paginate_by = 15
    model = models.Review

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ReviewListView, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        qs = super(ReviewListView, self).get_queryset()
        form = forms.ReviewFilterForm(
            self.request.user.projects,
            data=self.request.GET
        )
        if form.is_valid():
            return form.get_reviews(qs)

        return models.Review.objects.none()

    def get_context_data(self, **kwargs):
        context = super(ReviewListView, self).get_context_data(**kwargs)
        initial = self.request.GET.copy()
        initial['state'] = initial.get('state', models.reviews.OPEN)
        context.update({
            'form': forms.ReviewFilterForm(
                self.request.user.projects,
                initial=initial
            )
        })
        return context


class ReviewerStatusView(CanViewJsonView):

    status = 200

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.review = None
        self.project = None
        self.reviewer = None

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        reviewer_pk = kwargs['reviewer_pk']
        self.reviewer = get_object_or_404(
            models.Reviewer, pk=reviewer_pk, reviewer=self.request.user
        )
        self.review = self.reviewer.review
        self.project = self.review.project
        return super(ReviewerStatusView, self).dispatch(*args, **kwargs)

    def post(self, *args, **kwargs):  # pylint: disable=unused-argument
        form = forms.ReviewerStatusForm(self.reviewer, data=self.request.POST)
        if form.is_valid():
            state_changed, new_state = self.reviewer.set_status(
                form.cleaned_data['status']
            )
            return {
                'reviewer_state_changed': state_changed,
                'new_state': new_state,
                'reviewer_status': form.cleaned_data['status'],
                'success': True,
                'errors': {},
            }
        else:
            self.status = 400
            return {
                'reviewer_state_changed': False,
                'new_state': '',
                'reviewer_status': self.reviewer.status,
                'success': False,
                'errors': form.errors,
            }


class ReviewStateView(CanViewJsonView):

    status = 200

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.review = None
        self.project = None

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        review_pk = kwargs['pk']
        self.review = get_object_or_404(models.Review, pk=review_pk)
        self.project = self.review.project
        return super(ReviewStateView, self).dispatch(*args, **kwargs)

    def post(self, *args, **kwargs): # pylint: disable=unused-argument
        form = forms.ReviewStateForm(
            self.request.user, self.review.pk, data=self.request.POST
        )
        if form.is_valid():
            changed = self.review.update_state(form.cleaned_data['state'])
            return {
                'state': self.review.state,
                'state_changed': changed,
                'success': True,
                'errors': {},
            }
        else:
            self.status = 400
            return {
                'state': self.review.state,
                'state_changed': False,
                'success': False,
                'errors': form.errors,
            }


class ReviewJsonView(CanViewJsonView):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.review = None
        self.project = None

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        self.review = get_object_or_404(
            models.Review,
            pk=kwargs.get('pk'),
            project__slug=kwargs.get('proj_slug'),
        )
        self.project = self.review.project
        return super(ReviewJsonView, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):  # pylint: disable=unused-argument
        return self.review.to_json()

    def post(self, request, *args, **kwargs):  # pylint: disable=unused-argument
        if self.review.creator != request.user:
            self.status = 403
            return {
                'errors': ['Only the creator of a Demo can edit it'],
                'review': self.review.to_json()
            }

        form = forms.ReviewQuickEditForm(request.POST)
        json_dict = {'errors': []}
        if form.is_valid():
            data = form.cleaned_data
            update_fields = ['modified']
            for key, value in data.items():
                if value:
                    setattr(self.review, key, value)
                    update_fields.append(key)

            self.review.save(update_fields=update_fields)
        else:
            json_dict['errors'] = form.errors

        json_dict['review'] = self.review.to_json()
        return json_dict


class ReviewSearchJsonView(JsonView):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.projects = None

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        self.projects = self.request.user.projects
        if self.request.POST.get('project_pk'):
            self.projects = self.projects.filter(
                pk=self.request.POST['project_pk']
            )

        elif kwargs.get('proj_slug'):
            self.projects = self.projects.filter(
                slug=kwargs['proj_slug']
            )
        return super(ReviewSearchJsonView, self).dispatch(*args, **kwargs)

    def post(self, *args, **kwargs):  # pylint: disable=unused-argument
        form = forms.ReviewFilterForm(
            self.projects,
            data=self.request.POST
        )
        if form.is_valid():
            reviews = form.get_reviews()
            review_json_dict = {
                'count': reviews.count(),
                'reviews': [],
            }
            for review in reviews:
                review_json_dict['reviews'].append(review.to_json())

            return review_json_dict

        return {'count': 0, 'reviews': []}


class DTRedirectView(RedirectView):

    permanent = True
    query_string = True
    pattern_name = 'review-detail'

    def get_redirect_url(self, *args, **kwargs):
        review = get_object_or_404(
            models.Review,
            pk=kwargs.get('pk')
        )
        kwargs['proj_slug'] = review.project.slug
        return super(DTRedirectView, self).get_redirect_url(*args, **kwargs)

# pylint: disable=invalid-name
review_form_view = CreateReviewView.as_view()
review_detail = ReviewDetail.as_view()
reviewer_status_view = ReviewerStatusView.as_view()
review_state_view = ReviewStateView.as_view()
review_json_view = ReviewJsonView.as_view()
review_search_json_view = ReviewSearchJsonView.as_view()
review_list_view = ReviewListView.as_view()
dt_redirect_view = DTRedirectView.as_view()
