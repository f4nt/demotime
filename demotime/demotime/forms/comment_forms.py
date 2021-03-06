from django import forms

from demotime import models


class CommentForm(forms.ModelForm):

    thread = forms.ModelChoiceField(
        queryset=models.CommentThread.objects.none(),
        widget=forms.widgets.HiddenInput(),
        required=False
    )
    is_issue = forms.BooleanField(required=False)

    def __init__(self, thread=None, has_attachments=False, *args, **kwargs):
        super(CommentForm, self).__init__(*args, **kwargs)
        if thread:
            self.fields['thread'].queryset = models.CommentThread.objects.filter(
                pk=thread.pk
            )
            self.fields['thread'].required = True

        if not has_attachments:
            self.fields['comment'].required = True

        for key, _ in self.fields.items():
            self.fields[key].widget.attrs['class'] = 'form-control'

    class Meta:
        model = models.Comment
        fields = (
            'comment',
        )


class CommentAttachmentForm(forms.Form):

    attachment = forms.FileField(
        required=False,
        widget=forms.widgets.FileInput(
            attrs={'class': 'form-control'}
        )
    )
    description = forms.CharField(
        required=False,
        widget=forms.widgets.TextInput(attrs={'class': 'form-control'}),
        max_length=2048
    )


class DemoAttachmentForm(CommentAttachmentForm):

    sort_order = forms.IntegerField(
        required=False,
        widget=forms.HiddenInput,
    )

    def clean_sort_order(self):
        data = self.cleaned_data
        if data.get('attachment') and not data.get('sort_order'):
            raise forms.ValidationError('Attachments require a sort_order')

        return data['sort_order']
