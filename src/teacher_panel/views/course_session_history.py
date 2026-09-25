from typing import Any

from django.contrib import messages
from django.db.models import QuerySet
from django.http import HttpRequest
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import ListView
from django_htmx.http import retarget

from school.models import AttendanceSession
from school.models import Course
from school.selectors import course_history_sessions
from school.selectors import teacher_courses
from school.selectors import teacher_sessions
from school.services import session_create
from school.services import session_delete
from teacher_panel.forms import SessionForm

from .mixins import TeacherRequiredMixin
from .mixins import session_detail_url

# --- Template views (full pages) ---


class CourseSessionHistoryView(TeacherRequiredMixin, ListView):
    template_name = "teacher_panel/course_session_history.html"
    context_object_name = "sessions"

    def get_course(self) -> Course:
        return get_object_or_404(
            teacher_courses(teacher=self.teacher),
            pk=self.kwargs["pk"],
        )

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        self.course = self.get_course()
        return super().get(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet:
        return course_history_sessions(
            course=self.course,
            value=timezone.now().date(),
        )

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["course"] = self.course
        context["form"] = SessionForm(course=self.course)
        return context

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        self.course = self.get_course()
        form = SessionForm(request.POST, course=self.course)
        if form.is_valid():
            session = session_create(
                course=self.course,
                value=form.cleaned_data["date"],
                created_by=self.teacher,
            )
            messages.success(request, "Sesión creada.")
            if request.htmx:  # type: ignore[attr-defined]
                return HttpResponse(
                    status=200,
                    headers={"HX-Redirect": session_detail_url(session)},
                )
            return HttpResponseRedirect(session_detail_url(session))
        context = {
            "course": self.course,
            "form": form,
            self.context_object_name: self.get_queryset(),
        }
        if request.htmx:  # type: ignore[attr-defined]
            response = render(
                request,
                "teacher_panel/course_session_history.html#session_create_form",
                context,
            )
            return retarget(response, "#session-form")
        return render(request, self.template_name, context)


# --- Partial views (HTMX fragments) ---


class SessionDeleteView(TeacherRequiredMixin, View):
    """Past-session deletes re-render the history list; today deletes redirect (D6)."""

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        session = get_object_or_404(
            teacher_sessions(teacher=self.teacher),
            pk=kwargs["pk"],
        )
        course = session.course
        if session.is_frozen():
            messages.error(request, AttendanceSession.FROZEN_MESSAGE)
            if request.htmx:  # type: ignore[attr-defined]
                return render(
                    request,
                    "teacher_panel/course_session_history.html#session_list",
                    {
                        "course": course,
                        "sessions": course_history_sessions(
                            course=course,
                            value=timezone.now().date(),
                        ),
                    },
                )
            return HttpResponseRedirect(
                reverse("teacher_panel:course_session_history", args=[course.pk]),
            )
        is_today = session.date == timezone.now().date()
        session_delete(session=session)
        messages.success(request, "Sesión eliminada.")
        if request.htmx:  # type: ignore[attr-defined]
            if is_today:
                return HttpResponse(
                    status=200,
                    headers={
                        "HX-Redirect": reverse(
                            "teacher_panel:course_detail",
                            args=[course.pk],
                        ),
                    },
                )
            context = {
                "course": course,
                "sessions": course_history_sessions(
                    course=course,
                    value=timezone.now().date(),
                ),
            }
            return render(
                request,
                "teacher_panel/course_session_history.html#session_list",
                context,
            )
        return HttpResponseRedirect(
            reverse("teacher_panel:course_session_history", args=[course.pk]),
        )
