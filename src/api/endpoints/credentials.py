from uuid import UUID

from asgiref.sync import sync_to_async
from django.http import HttpRequest, HttpResponse
from ninja import Router
from ninja.errors import HttpError

from credentials import services
from school.models import Student

from ..auth import DesktopApiKeyAuth
from ..schemas import (
    CredentialEventApplied,
    CredentialEventIn,
    DesktopStudentOut,
)

router = Router(auth=DesktopApiKeyAuth())

PHOTO_PATH = '/api/desktop/students/{student_id}/photo'


def student_photo_url(student_id: UUID) -> str:
    return PHOTO_PATH.format(student_id=student_id)


def _student_to_out(student: Student) -> DesktopStudentOut:
    return DesktopStudentOut(
        id=student.id,
        first_name=student.first_name,
        paternal_surname=student.paternal_surname,
        maternal_surname=student.maternal_surname,
        email=student.email,
        groups=[group.name for group in student.student_groups.all()],
        has_photo=bool(student.photo),
        photo_url=student_photo_url(student.id) if student.photo else None,
    )


def _read_photo_bytes(student: Student) -> bytes:
    with student.photo.open('rb') as file:
        return file.read()


@router.get('/students', response=list[DesktopStudentOut])
async def list_students(request: HttpRequest) -> list[DesktopStudentOut]:
    students = Student.objects.prefetch_related('student_groups')
    return [_student_to_out(student) async for student in students]


@router.get('/students/{student_id}/photo')
async def student_photo(request: HttpRequest, student_id: UUID) -> HttpResponse:
    student = await Student.objects.filter(pk=student_id).afirst()
    if student is None or not student.photo:
        raise HttpError(404, 'Foto no encontrada.')
    photo_bytes = await sync_to_async(_read_photo_bytes)(student)
    return HttpResponse(photo_bytes, content_type='image/jpeg')


@router.post('/credential-events', response={200: CredentialEventApplied})
async def credential_events(
    request: HttpRequest, payload: CredentialEventIn
) -> CredentialEventApplied:
    try:
        if payload.operation == 'issued':
            if payload.credential is None or payload.student_id is None:
                raise HttpError(
                    422, 'El evento issued requiere credential y student_id.'
                )
            await sync_to_async(services.credential_issue)(
                student_id=payload.student_id,
                credential=payload.credential.model_dump(),
            )
        elif payload.operation == 'revoked':
            if payload.credential_id is None or payload.revoked_at is None:
                raise HttpError(
                    422, 'El evento revoked requiere credential_id y revoked_at.'
                )
            await sync_to_async(services.credential_revoke)(
                credential_id=payload.credential_id, revoked_at=payload.revoked_at
            )
        else:
            if payload.credential_id is None or payload.expiration_date is None:
                raise HttpError(
                    422,
                    'El evento validity_extended requiere credential_id,'
                    ' expiration_date y max_expiration_date.',
                )
            await sync_to_async(services.credential_extend_validity)(
                credential_id=payload.credential_id,
                expiration_date=payload.expiration_date,
                max_expiration_date=payload.max_expiration_date,
            )
    except services.StudentNotFound:
        raise HttpError(422, 'Estudiante no encontrado.') from None
    except services.CredentialNotFound:
        raise HttpError(404, 'Credencial no encontrada.') from None
    return CredentialEventApplied(status='applied', operation=payload.operation)
