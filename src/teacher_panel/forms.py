import datetime
from typing import Any

from django import forms
from django.utils import timezone

from school.models import AttendanceRecord
from school.models import AttendanceSession
from school.models import Course
from school.services import validate_session_date


class SessionForm(forms.Form):
    date = forms.DateField(
        widget=forms.DateInput(
            attrs={"type": "date"},
            format="%Y-%m-%d",
        ),
        input_formats=["%Y-%m-%d", "%d/%m/%Y"],
        localize=False,
    )

    def __init__(self, *args: Any, course: Course | None = None, **kwargs: Any) -> None:
        self.course = course
        super().__init__(*args, **kwargs)

    def clean_date(self) -> datetime.date:
        date_value: datetime.date = self.cleaned_data["date"]
        today = timezone.now().date()
        if date_value > today:
            raise forms.ValidationError("La fecha no puede ser posterior a hoy.")
        if date_value == today:
            raise forms.ValidationError(
                'Para la sesión de hoy, usa la tarjeta "Sesión de hoy".',
            )
        if AttendanceSession.objects.filter(
            course=self.course, date=date_value
        ).exists():
            raise forms.ValidationError("Ya existe una sesión para esta fecha.")
        if self.course is not None:
            validate_session_date(course=self.course, value=date_value)
        return date_value


class AttendanceSummaryFilterForm(forms.Form):
    """Optional date range bounds for the course attendance summary page."""

    date_from = forms.DateField(
        required=False,
        label="Desde",
        widget=forms.DateInput(
            attrs={"type": "date"},
            format="%Y-%m-%d",
        ),
        input_formats=["%Y-%m-%d", "%d/%m/%Y"],
        localize=False,
    )
    date_to = forms.DateField(
        required=False,
        label="Hasta",
        widget=forms.DateInput(
            attrs={"type": "date"},
            format="%Y-%m-%d",
        ),
        input_formats=["%Y-%m-%d", "%d/%m/%Y"],
        localize=False,
    )

    def clean(self) -> dict[str, Any]:
        cleaned = super().clean()
        date_from = cleaned.get("date_from")
        date_to = cleaned.get("date_to")
        if date_from and date_to and date_from > date_to:
            raise forms.ValidationError(
                "La fecha inicial no puede ser posterior a la fecha final.",
            )
        return cleaned


AttendanceEditFormSet = forms.modelformset_factory(
    AttendanceRecord,
    fields=("status", "notes"),
    widgets={
        "status": forms.Select(
            choices=AttendanceRecord.Status.choices,
            attrs={
                "class": (
                    "flex h-10 w-full items-center justify-between rounded-md "
                    "border border-input bg-background px-3 py-2 text-sm "
                    "ring-offset-background focus:outline-hidden focus:ring-2 "
                    "focus:ring-ring focus:ring-offset-2 "
                    "disabled:cursor-not-allowed disabled:opacity-50"
                ),
            },
        ),
        "notes": forms.Textarea(attrs={"rows": 2, "placeholder": "Nota opcional"}),
    },
    extra=0,
)
