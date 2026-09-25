import io
import posixpath
from typing import Any
from typing import ClassVar
from uuid import uuid4

import pillow_heif
from django import forms
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.base import File
from django.core.files.storage import FileSystemStorage
from PIL import Image
from PIL import ImageOps

pillow_heif.register_heif_opener()

MAX_PHOTO_SIZE_BYTES = 15 * 1024 * 1024
MAX_PHOTO_DIMENSIONS = (600, 600)
JPEG_QUALITY = 85

PHOTO_TOO_LARGE_ERROR = (
    "La fotografía supera el tamaño máximo de "
    f"{MAX_PHOTO_SIZE_BYTES // (1024 * 1024)} MB."
)
PHOTO_INVALID_ERROR = "El archivo no es una imagen válida o está dañada."


class StudentPhotoField(forms.ImageField):
    """Form field that caps upload size before decoding, with Spanish errors."""

    default_error_messages: ClassVar[dict[str, str]] = {  # type: ignore[assignment]
        "invalid_image": PHOTO_INVALID_ERROR,
        "photo_too_large": PHOTO_TOO_LARGE_ERROR,
    }

    def to_python(self, data: Any) -> File | None:
        if data is not None and getattr(data, "size", 0) > MAX_PHOTO_SIZE_BYTES:
            raise ValidationError(
                self.error_messages["photo_too_large"], code="photo_too_large"
            )
        return super().to_python(data)


class ConvertedPhotoStorage(FileSystemStorage):
    """Normalizes every saved photo into an EXIF-free bounded JPEG."""

    def _save(self, name: str, content: Any) -> str:
        size = getattr(content, "size", None)
        if size is not None and size > MAX_PHOTO_SIZE_BYTES:
            raise ValidationError(PHOTO_TOO_LARGE_ERROR, code="photo_too_large")
        directory = posixpath.dirname(name)
        target = f"{directory}/{uuid4()}.jpg" if directory else f"{uuid4()}.jpg"
        return super()._save(target, _normalized_jpeg(content))  # type: ignore[misc]


def _normalized_jpeg(source: Any) -> ContentFile:
    try:
        image: Image.Image = Image.open(io.BytesIO(source.read()))
        image = ImageOps.exif_transpose(image)
        image.info.pop("exif", None)
        image = _flatten_to_rgb(image)
        image.thumbnail(MAX_PHOTO_DIMENSIONS)
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=JPEG_QUALITY)
    except ValidationError:
        raise
    except Exception as exc:
        raise ValidationError(PHOTO_INVALID_ERROR, code="invalid_image") from exc
    return ContentFile(buffer.getvalue())


def _flatten_to_rgb(image: Image.Image) -> Image.Image:
    if image.mode == "RGB":
        return image
    if image.mode in ("RGBA", "LA") or (
        image.mode == "P" and "transparency" in image.info
    ):
        rgba = image.convert("RGBA")
        background = Image.new("RGB", rgba.size, (255, 255, 255))
        background.paste(rgba, mask=rgba.getchannel("A"))
        return background
    return image.convert("RGB")
