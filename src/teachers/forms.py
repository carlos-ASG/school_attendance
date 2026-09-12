from django import forms

from school.models import AttendanceRecord, AttendanceSession


class SessionForm(forms.Form):
    date = forms.DateField(
        widget=forms.DateInput(
            attrs={'type': 'date'}, format='%Y-%m-%d'
        ),
        input_formats=['%Y-%m-%d', '%d/%m/%Y'],
        localize=False,
    )

    def __init__(self, *args, course=None, exclude_pk=None, **kwargs):
        self.course = course
        self.exclude_pk = exclude_pk
        super().__init__(*args, **kwargs)

    def clean_date(self):
        date = self.cleaned_data['date']
        sessions = AttendanceSession.objects.filter(course=self.course, date=date)
        if self.exclude_pk is not None:
            sessions = sessions.exclude(pk=self.exclude_pk)
        if sessions.exists():
            raise forms.ValidationError('A session already exists for this date.')
        return date


AttendanceFormSet = forms.modelformset_factory(
    AttendanceRecord,
    fields=('notes',),
    widgets={
        'notes': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Nota opcional'}),
    },
    extra=0,
)
