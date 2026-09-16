# Example: Full CRUD on a Django model

Complete pattern for model-backed endpoints: input schema (`*In`), output
schema (`*Out`), list route returning a queryset, PATCH with
`exclude_unset=True`.

```python
from datetime import date
from typing import List

from django.shortcuts import get_object_or_404
from ninja import NinjaAPI, Schema

from school.models import Student

api = NinjaAPI()


class StudentIn(Schema):
    first_name: str
    last_name: str
    birthdate: date = None


class StudentOut(Schema):
    id: int
    first_name: str
    last_name: str
    birthdate: date = None


@api.post("/students")
def create_student(request, payload: StudentIn):
    student = Student.objects.create(**payload.dict())
    return {"id": student.id}


@api.get("/students/{student_id}", response=StudentOut)
def get_student(request, student_id: int):
    return get_object_or_404(Student, id=student_id)


@api.get("/students", response=List[StudentOut])
def list_students(request):
    return Student.objects.all()          # queryset converted automatically


@api.put("/students/{student_id}")
def update_student(request, student_id: int, payload: StudentIn):
    student = get_object_or_404(Student, id=student_id)
    for attr, value in payload.dict().items():
        setattr(student, attr, value)
    student.save()
    return {"success": True}


@api.patch("/students/{student_id}")
def partial_update(request, student_id: int, payload: StudentIn):
    student = get_object_or_404(Student, id=student_id)
    for attr, value in payload.dict(exclude_unset=True).items():
        setattr(student, attr, value)
    student.save()
    return {"success": True}


@api.delete("/students/{student_id}")
def delete_student(request, student_id: int):
    student = get_object_or_404(Student, id=student_id)
    student.delete()
    return {"success": True}
```

Wire in `src/config/urls.py`:

```python
path("api/", api.urls)
```

Notes:

- Strict input: add `model_config = ConfigDict(extra="forbid")` to `StudentIn`
  if unknown fields must error instead of being ignored.
- PATCH alternative: `payload: PatchDict[StudentIn]` makes all fields optional
  automatically (see `../references/schemas.md`).
- FileField addition (e.g. `cv`): add `cv: File[UploadedFile]` to the create
  operation and `student.cv.save(cv.name, cv)` — see
  `../references/input-params.md`.
