## 1. Dependencies and model

- [x] 1.1 Add `pillow` and `pillow-heif` via `uv add`. Given the lockfile update, when importing Pillow with `register_heif_opener()` called, then HEIC test fixtures open successfully.
- [ ] 1.2 Add `photo = models.ImageField('Fotografía', blank=True, upload_to='students/', storage=ConvertedPhotoStorage())` to `Student`, with the migration. Given an existing SQLite database, when `migrate` runs, then the column is added with no data loss.

## 2. Conversion pipeline

- [x] 2.1 Create `src/school/images.py`: `ConvertedPhotoStorage(FileSystemStorage)` whose `_save` decodes with Pillow (HEIC registered), applies `exif_transpose`, drops all EXIF, flattens RGBA onto white RGB, `thumbnail((600, 600))` (no upscale), saves as quality-85 JPEG named `f'{uuid4()}.jpg'` under `students/`. Given a 4032×3024 GPS-tagged HEIC, when saving through the field, then the stored file is an upright EXIF-free JPEG ≤ 600×600 preserving aspect ratio.
- [x] 2.2 Size cap: reject uploads over the configured maximum (constant in `images.py`) with a Spanish validation error before decoding. Given a 20 MB file, when uploading via the admin, then the form shows the error and nothing is stored.
- [x] 2.3 Decode-failure rejection: undecodable bytes are rejected with a Spanish validation error regardless of extension. Given `photo.jpg` containing text bytes, when uploading, then the form shows the error and nothing is stored.
- [x] 2.4 Replace cleanup: override `Student.save` to delete the previous photo file when `photo` changed. Given a student with a photo, when a new photo is uploaded, then exactly one file remains under `media/students/`.

## 3. Admin and media wiring

- [x] 3.1 Expose `photo` on `StudentAdmin`'s change form (fieldsets with the upload widget); no changelist thumbnail, no import/export changes. Given the admin, when editing a student, then the photo uploads and normalizes via 2.1–2.3.
- [x] 3.2 Media config: `MEDIA_ROOT = BASE_DIR / 'media'`, `MEDIA_URL = 'media/'` in settings; `static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)` appended to `config/urls.py`; `media/` added to `.gitignore`. Given a stored photo and `DEBUG` on, when requesting `MEDIA_URL` + path, then the JPEG is served.

## 4. Verification

- [x] 4.1 Unit tests for the pipeline: HEIC/jpeg/png/webp fixtures normalize to upright EXIF-free JPEGs ≤ 600×600; small images are not upscaled; undecodable and oversized uploads are rejected; replacement deletes the old file.
- [x] 4.2 Admin tests: upload via the change form stores one normalized file; saving without a photo succeeds; teacher-panel pages (dashboard, course detail, session detail) contain no photo references.
- [x] 4.3 Run `uv run manage.py check`, `migrate`, and the full test suite on SQLite.
- [ ] 4.4 Manual smoke with a real iPhone HEIC (and a rotated jpeg): upload in the admin, verify the stored file is a ~600px upright JPEG with no EXIF, and reload the form to confirm the widget resets.
