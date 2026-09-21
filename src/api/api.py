from ninja import NinjaAPI

from .auth import TeacherSessionAuth
from .endpoints.attendance import router as attendance_router
from .endpoints.credentials import router as credentials_router

api = NinjaAPI(
    title='Asistencia Escolar API',
    urls_namespace='api',
    auth=TeacherSessionAuth(),
)

api.add_router('', attendance_router)
api.add_router('/desktop', credentials_router)
