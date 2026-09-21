from datetime import date
from typing import Any

from django import forms
from django.utils import timezone

from school.calendar import validate_session_date
from school.models import AttendanceRecord, AttendanceSession, Course


class SessionForm(forms.Form):
    date = forms.DateField(
        widget=forms.DateInput(
            attrs={'type': 'date'}, format='%Y-%m-%d'
        ),
        input_formats=['%Y-%m-%d', '%d/%m/%Y'],
        localize=False,
    )

    def __init__(self, *args: Any, course: Course | None = None, **kwargs: Any) -> None:
        self.course = course
        super().__init__(*args, **kwargs)

    def clean_date(self) -> date:
        date = self.cleaned_data['date']
        today = timezone.now().date()
        if date > today:
            raise forms.ValidationError('La fecha no puede ser posterior a hoy.')
        if date == today:
            raise forms.ValidationError(
                'Para la sesión de hoy, usa la tarjeta "Sesión de hoy".'
            )
        if AttendanceSession.objects.filter(course=self.course, date=date).exists():
            raise forms.ValidationError('Ya existe una sesión para esta fecha.')
        if self.course is not None:
            validate_session_date(self.course, date)
        return date


AttendanceEditFormSet = forms.modelformset_factory(
    AttendanceRecord,
    fields=('status', 'notes'),
    widgets={
        'status': forms.Select(
            choices=AttendanceRecord.Status.choices,
            attrs={
                'class': (
                    'flex h-10 w-full items-center justify-between rounded-md '
                    'border border-input bg-background px-3 py-2 text-sm '
                    'ring-offset-background focus:outline-hidden focus:ring-2 '
                    'focus:ring-ring focus:ring-offset-2 '
                    'disabled:cursor-not-allowed disabled:opacity-50'
                ),
            },
        ),
        'notes': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Nota opcional'}),
    },
    extra=0,
)
