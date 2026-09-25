import json
from datetime import date
from datetime import timedelta
from typing import Any

from django.db.models import Count
from django.db.models import QuerySet
from unfold.components import BaseComponent
from unfold.components import register_component

from .models import AttendanceRecord

STATUS_LABELS: dict[str, str] = dict(AttendanceRecord.Status.choices)
STATUS_ORDER: list[str] = [value for value, _ in AttendanceRecord.Status.choices]
STATUS_COLORS: dict[str, str] = {
    AttendanceRecord.Status.PRESENT: "var(--color-green-500)",
    AttendanceRecord.Status.ABSENT: "var(--color-red-500)",
    AttendanceRecord.Status.LATE: "var(--color-orange-500)",
    AttendanceRecord.Status.EXCUSED: "var(--color-blue-500)",
}


def _records_in_range(
    start: date,
    end: date,
) -> QuerySet[AttendanceRecord]:
    return AttendanceRecord.objects.filter(session__date__range=(start, end))


@register_component
class LineChartComponent(BaseComponent):
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        start = kwargs["start"]
        end = kwargs["end"]
        records = _records_in_range(start, end)

        day_status = (
            records.values("session__date", "status")
            .annotate(count=Count("id"))
            .order_by("session__date", "status")
        )
        counts = {
            (row["session__date"], row["status"]): row["count"] for row in day_status
        }
        days = []
        cursor = start
        while cursor <= end:
            days.append(cursor)
            cursor += timedelta(days=1)

        line_data = {
            "labels": [day.strftime("%d/%m") for day in days],
            "datasets": [
                {
                    "label": STATUS_LABELS[value],
                    "data": [counts.get((day, value), 0) for day in days],
                    "borderColor": STATUS_COLORS[value],
                    **({"maxTicksXLimit": 12} if value == STATUS_ORDER[0] else {}),
                }
                for value in STATUS_ORDER
            ],
        }
        context["data"] = json.dumps(line_data)
        context["height"] = 256
        return context


@register_component
class BarChartComponent(BaseComponent):
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        start = kwargs["start"]
        end = kwargs["end"]
        records = _records_in_range(start, end)

        course_rows = (
            records.values("session__course__subject__name")
            .annotate(count=Count("id"))
            .order_by("-count")
        )
        bar_data = {
            "labels": [
                row["session__course__subject__name"] or "-" for row in course_rows
            ],
            "datasets": [
                {
                    "label": "Registros",
                    "data": [row["count"] for row in course_rows],
                    "backgroundColor": "var(--color-primary-600)",
                    "displayYAxis": True,
                    "maxTicksXLimit": 20,
                },
            ],
        }
        context["data"] = json.dumps(bar_data)
        context["height"] = 256
        return context


@register_component
class PieChartComponent(BaseComponent):
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        start = kwargs["start"]
        end = kwargs["end"]
        records = _records_in_range(start, end)

        status_counts = dict(
            records.values("status")
            .annotate(count=Count("id"))
            .order_by("status")
            .values_list("status", "count"),
        )
        pie_data = {
            "labels": [STATUS_LABELS[value] for value in STATUS_ORDER],
            "datasets": [
                {
                    "data": [status_counts.get(value, 0) for value in STATUS_ORDER],
                    "backgroundColor": [STATUS_COLORS[value] for value in STATUS_ORDER],
                },
            ],
        }
        pie_options = {
            "responsive": True,
            "maintainAspectRatio": False,
            "datasets": {
                "pie": {
                    "borderWidth": 0,
                },
            },
            "plugins": {
                "legend": {
                    "display": True,
                    "position": "right",
                },
            },
        }
        context["data"] = json.dumps(pie_data)
        context["options"] = json.dumps(pie_options)
        context["height"] = 256
        return context
