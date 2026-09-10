from django import forms

from .models import AttendanceRecord, AttendanceSession


class SessionCreateForm(forms.Form):
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))

    def __init__(self, *args, classroom=None, **kwargs):
        self.classroom = classroom
        super().__init__(*args, **kwargs)

    def clean_date(self):
        date = self.cleaned_data['date']
        if AttendanceSession.objects.filter(classroom=self.classroom, date=date).exists():
            raise forms.ValidationError('A session already exists for this date.')
        return date


AttendanceFormSet = forms.modelformset_factory(
    AttendanceRecord,
    fields=('status',),
    extra=0,
)
