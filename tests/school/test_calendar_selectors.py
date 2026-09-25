"""Tests for school.selectors.calendar."""

from datetime import UTC
from datetime import date
from datetime import datetime

import pytest

from school.models import NonSchoolDay
from school.models import SchoolCycle
from school.selectors.calendar import get_current_school_cycle
from school.selectors.calendar import get_non_school_day

pytestmark = pytest.mark.django_db

MONDAY = date(2026, 1, 5)
FRIDAY = date(2026, 1, 9)


def create_cycle(name, start, end):
    return SchoolCycle.objects.create(
        name=name,
        cycle_type=SchoolCycle.CycleType.SEMESTRAL,
        start_date=start,
        end_date=end,
    )


def create_non_school_day(cycle, name, start, end=None):
    return NonSchoolDay.objects.create(
        cycle=cycle,
        name=name,
        day_type=NonSchoolDay.DayType.ASUETO,
        start_date=start,
        end_date=end,
    )


def test_get_current_school_cycle_returns_cycle_containing_value(school_cycle):
    assert get_current_school_cycle(value=MONDAY) == school_cycle


@pytest.mark.parametrize("value", [date(2026, 1, 5), date(2026, 6, 30)])
def test_get_current_school_cycle_includes_cycle_boundaries(school_cycle, value):
    assert get_current_school_cycle(value=value) == school_cycle


def test_get_current_school_cycle_returns_none_when_date_uncovered(school_cycle):
    assert get_current_school_cycle(value=date(2026, 7, 6)) is None


def test_get_current_school_cycle_returns_none_without_cycles():
    assert get_current_school_cycle(value=MONDAY) is None


def test_get_current_school_cycle_defaults_to_today(monkeypatch, school_cycle):
    monkeypatch.setattr(
        "django.utils.timezone.now",
        lambda: datetime(2026, 1, 5, 12, 0, tzinfo=UTC),
    )

    assert get_current_school_cycle() == school_cycle


def test_get_current_school_cycle_picks_lowest_pk_among_overlapping_cycles():
    create_cycle("Ciclo A", date(2026, 1, 5), date(2026, 6, 30))
    create_cycle("Ciclo B", date(2026, 2, 1), date(2026, 5, 31))

    expected = SchoolCycle.objects.order_by("pk").first()

    assert get_current_school_cycle(value=date(2026, 3, 15)) == expected


def test_get_non_school_day_returns_single_date_day(school_cycle):
    day = create_non_school_day(school_cycle, "Día del maestro", MONDAY)

    assert get_non_school_day(cycle=school_cycle, value=MONDAY) == day


def test_get_non_school_day_returns_range_day_covering_value(school_cycle):
    day = create_non_school_day(
        school_cycle,
        "Semana de asueto",
        MONDAY,
        end=FRIDAY,
    )

    assert get_non_school_day(cycle=school_cycle, value=MONDAY) == day
    assert get_non_school_day(cycle=school_cycle, value=FRIDAY) == day


def test_get_non_school_day_ignores_other_cycle_days(school_cycle):
    other_cycle = create_cycle("Ciclo B", date(2026, 7, 1), date(2026, 12, 15))
    create_non_school_day(other_cycle, "Día del maestro", MONDAY)

    assert get_non_school_day(cycle=school_cycle, value=MONDAY) is None


def test_get_non_school_day_returns_none_when_date_not_covered(school_cycle):
    create_non_school_day(school_cycle, "Día del maestro", MONDAY)

    assert get_non_school_day(cycle=school_cycle, value=FRIDAY) is None


def test_get_non_school_day_returns_none_for_missing_cycle():
    assert get_non_school_day(cycle=None, value=MONDAY) is None
