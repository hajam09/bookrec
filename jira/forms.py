from django import forms
from django.contrib.auth.models import User
from django.template.defaultfilters import slugify

from jira.models import Ticket


class TicketCreationForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ('project', 'issue_type', 'priority', 'reporter', 'assignee', 'summary', 'description', 'points')

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        super().__init__(*args, **kwargs)

        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'

        self.fields['reporter'].queryset = User.objects.filter(is_superuser=True)
        self.fields['reporter'].initial = self.request.user
        self.fields['assignee'].queryset = User.objects.filter(is_superuser=True)
        self.fields['assignee'].required = False

    summary = forms.CharField(
        label='',
        required=True,
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Add issue summary here'
            }
        )
    )

    description = forms.CharField(
        label='',
        required=True,
        widget=forms.Textarea(
            attrs={
                'placeholder': 'Add issue description here',
                'rows': 5,
            }
        )
    )

    points = forms.IntegerField(
        label='',
        required=True,
        widget=forms.NumberInput(
            attrs={
                'placeholder': 'Add issue points here'
            }
        )
    )

    def save(self):
        project = self.cleaned_data.get("project")

        try:
            url = slugify(project) + "-" + str(Ticket.objects.last().pk)
        except Exception as e:
            url = slugify(project) + "-" + "0"

        Ticket.objects.create(
            url=url,
            project=project,
            issue_type=self.cleaned_data.get("issue_type"),
            reporter=self.cleaned_data.get("reporter"),
            assignee=self.cleaned_data.get("assignee"),
            summary=self.cleaned_data.get("summary"),
            description=self.cleaned_data.get("description"),
            points=self.cleaned_data.get("points"),
            priority=self.cleaned_data.get("priority")
        )