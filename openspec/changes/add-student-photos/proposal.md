## Why

Students have no photo, and nothing in the system can accept one. A normalized per-student photo (fixed format, bounded dimensions, metadata stripped) managed from the Django admin prepares the ground for a future student detail page — photos of school children demand GPS/EXIF stripping and uniform small files, not raw iPhone HEICs.

## What Changes

- Add an optional `photo` field to `Student` (`ImageField`, blank), uploaded and managed via the existing unfold `StudentAdmin`.
- New conversion pipeline (`src/school/images.py`): on save, open the upload with Pillow — accepting jpeg/jpg/heic/heif (via `pillow-heif`) and png/webp — transpose EXIF orientation, strip all EXIF metadata (incl. GPS), flatten to RGB, resize to fit within 600×600 preserving aspect ratio, and store as JPEG named `<uuid>.jpg`; replacing a photo deletes the previous file.
- Validation by attempting to open the image (not by extension trust), with a max upload size cap.
- Media infrastructure: `MEDIA_ROOT`/`MEDIA_URL` settings, media serving in dev via `config/urls.py`, `media/` git-ignored.
- Dependencies: `pillow`, `pillow-heif`.

## Capabilities

### New Capabilities

- `student-photos`: photo capture/normalization/storage per student, admin-managed, with format/size/metadata guarantees and no teacher-panel display.

### Modified Capabilities

<!-- None: teacher panel, admin browsing, and import/export behaviors are unchanged; the photo field is excluded from import/export. -->

## Impact

- `src/school/models/student.py`: new `photo` field (+ migration).
- `src/school/admin.py`: `StudentAdmin` gains the photo upload.
- New: `src/school/images.py` (pipeline), tests.
- `src/config/settings.py`, `src/config/urls.py`: media config/serving; `.gitignore`: `media/`.
- `pyproject.toml`: `pillow`, `pillow-heif`.
- **No display anywhere yet**: photos appear nowhere in the teacher panel; the future student detail page (agreed direction: photo with initials-avatar fallback) is a separate change.

## Non-goals

- No teacher-panel or API display of photos (student detail page deferred; initials avatar ships with that change).
- No image generation/thumbnails beyond the single 600×600 JPEG; no exact-square cropping.
- No bulk photo import; no student self-service; no remote object storage (local `MEDIA_ROOT` only).
- Photo excluded from import/export flows (`StudentResource` unchanged).
