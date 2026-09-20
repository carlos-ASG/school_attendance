# Design: add-student-photos

## Context

`Student` (src/school/models/student.py) holds only names + email on a UUIDv7 PK; the admin uses unfold's `StudentAdmin` with import/export. There is no `MEDIA_ROOT`/`MEDIA_URL`, no media serving in `config/urls.py`, and no Pillow dependency. Sources will be iPhone photos: HEIC containers, large dimensions, EXIF orientation flags, and embedded GPS — unacceptable to persist for school children. No student detail page exists anywhere yet; display (photo + initials avatar) is an agreed future change, so this change is storage/admin only.

## Goals / Non-Goals

**Goals:**

- Optional per-student photo, managed from the Django admin.
- One stored representation per student: JPEG, fit-within 600×600 (aspect preserved), EXIF-stripped, `<uuid>.jpg`.
- Accept what phones produce: jpeg, heic/heif (via `pillow-heif`), plus png/webp (free with Pillow).
- Validation by attempting to open the image; old file deleted on replacement; media served in dev.

**Non-Goals:**

- No display in teacher panel/API (future student detail page will show photo with initials-avatar fallback).
- No cropping to exact squares, no thumbnails/resizes beyond the single JPEG, no remote storage, no bulk import.

## Decisions

### D1: Convert in the model layer via a custom storage, not in the admin

A small `ConvertedPhotoStorage(FileSystemStorage)` (in `src/school/images.py`) overrides `_save` to run the pipeline on incoming bytes. Every write path (admin, shell, future API) normalizes identically, and the admin needs zero custom logic. Alternatives rejected: processing in `StudentAdmin.save_model` (admin-only — a shell/ORM save would bypass it), `pre_save` signal (same effect, less discoverable than the storage the field already references).

### D2: Pipeline order — open → transpose → strip → flatten → fit → save

`PIL.Image.open` (with `pillow_heif.register_heif_opener()` called at module import) validates by construction: unopenable bytes raise, which the storage re-raises as a `ValidationError`-shaped error surfaced by the admin form. Then `ImageOps.exif_transpose` (bakes orientation into pixels — skips the classic sideways-iPhone bug), re-save without EXIF (strips GPS and all metadata), `convert("RGB")` on a white background (JPEG has no alpha), `thumbnail((600, 600))` (aspect-preserving fit, never upscales), save as JPEG quality ~85. Validation is try-to-open, not extension sniffing — extensions lie; Pillow's decoders don't.

### D3: `<uuid>.jpg` naming, upload_to `students/`, replace deletes the old file

`upload_to='students/'` with the storage generating a fresh `uuid4` filename — stable, collision-free, no user-controlled bytes in paths. `Student.save()` (small override) deletes the prior file when `photo` changed, since Django orphans replaced files. UUIDv7 model PKs exist at instantiation, but a storage-side `uuid4` keeps the name decoupled from PK reuse on re-upload.

### D4: Size cap at the form/field level

A module constant (e.g. 15 MB) checked before decoding — Pillow decompression bombs are otherwise unbounded memory. Implemented as an `ImageField`-level clean in the admin form (`StudentAdmin.form` or field validation), producing a normal Spanish admin error. Alternative rejected: no cap (trusts admin users; a 50 MB HEIC is a real phone default).

### D5: Media config follows Django dev conventions

`MEDIA_ROOT = BASE_DIR / 'media'`, `MEDIA_URL = 'media/'`, `static()` helper appended to `config/urls.py` urlpatterns (DEBUG-only serving), `media/` in `.gitignore`. Production media hosting is explicitly future work.

### D6: Photo invisible to import/export and unchanged UIs

`StudentResource` (import/export) doesn't gain the photo; teacher-panel templates are untouched. `list_display`/changelists gain no thumbnail — the field is only an upload widget on the admin change form.

## Risks / Trade-offs

- [HEIC uploads fail if `pillow-heif` registration is skipped] → registration lives at the top of `images.py`, imported by the storage used by the field; the path can't be entered without it.
- [Orphaned files if photo handling is bypassed via ORM edge paths] → replace-delete lives in `Model.save`, covering all normal writes; raw storage writes out of scope.
- [Conversion cost per upload] → one image, admin-paced uploads; no async needed.
- [Large-upload memory spike before the cap check] → cap is checked on file size before `Image.open` reads pixel data.

## Migration Plan

Additive: one migration adding nullable-blank `photo` (`VARCHAR` path column on both SQLite/Postgres). Rollback: remove field; uploaded files are inert files under `media/students/`.

## Open Questions

- None blocking. Initials-avatar rendering details belong to the future student detail page change.
