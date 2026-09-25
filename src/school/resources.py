from typing import Any
from uuid import UUID

from django.core.exceptions import ValidationError
from django.db.models import QuerySet
from import_export import resources
from import_export import widgets
from import_export.fields import Field

from .models import Student
from .models import StudentGroup


class NullableIdWidget(widgets.Widget):
    """Converts blank ids to None so rows without id create new records."""

    def clean(
        self,
        value: Any,
        row: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> UUID | None:
        if value is None or str(value).strip() == "":
            return None
        return UUID(str(value))


class GroupNameWidget(widgets.ManyToManyWidget):
    """Maps comma-separated group names to StudentGroup records.

    Raises a validation error when a name does not match an existing group,
    so missing groups are reported in the import preview instead of being
    silently skipped or created.
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(model=StudentGroup, field="name", separator=",")

    def clean(
        self,
        value: Any,
        row: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> QuerySet[StudentGroup]:
        if not value:
            return self.model.objects.none()
        names = [
            name.strip() for name in str(value).split(self.separator) if name.strip()
        ]
        found_names = set(
            StudentGroup.objects.filter(name__in=names).values_list("name", flat=True)
        )
        missing = [name for name in names if name not in found_names]
        if missing:
            raise ValidationError(f"Grupos inexistentes: {', '.join(missing)}")
        return StudentGroup.objects.filter(name__in=names)


class StudentResource(resources.ModelResource):
    id = Field(column_name="id", attribute="id", widget=NullableIdWidget())
    first_name = Field(column_name="Nombre", attribute="first_name")
    paternal_surname = Field(
        column_name="Apellido paterno", attribute="paternal_surname"
    )
    maternal_surname = Field(
        column_name="Apellido materno", attribute="maternal_surname"
    )
    email = Field(column_name="Correo electrónico", attribute="email")
    student_groups = Field(
        column_name="Grupos",
        attribute="student_groups",
        widget=GroupNameWidget(),
    )

    class Meta:
        model = Student
        import_id_fields = ("id",)
        clean_model_instances = True
        skip_unchanged = True
        report_skipped = True
