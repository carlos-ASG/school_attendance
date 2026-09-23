# student-photos Specification

## Purpose

Allow an optional photo for each Student, uploaded and managed exclusively through the Django admin. Uploads are validated by decoding with Pillow (including HEIC/HEIF), normalized to a ≤600×600, EXIF-free JPEG stored under the project media directory, and served only via the development media URL. Photos are never displayed in the teacher panel, admin changelist, or import/export flows.

## Requirements

### Requirement: Optional photo per student managed from the Django admin

Each Student SHALL have an optional photo settable from the Student admin change form. The photo SHALL be stored under `MEDIA_ROOT` and SHALL NOT be displayed anywhere in the teacher panel EXCEPT the course student detail page, nor in the admin changelist or any import/export flow.

#### Scenario: Admin uploads a photo

- **WHEN** an Admin attaches an image file to a Student's change form and saves
- **THEN** the Student has a stored photo and the change form shows the upload widget again on reload

#### Scenario: Photo stays optional

- **WHEN** a Student is created or saved without a photo
- **THEN** saving succeeds and the Student has no photo

#### Scenario: No display outside the admin form and the student detail page

- **WHEN** any teacher-panel page other than the course student detail page (dashboard, course detail, session pages) renders
- **THEN** no student photo is requested or shown

#### Scenario: Photo displayed on the course student detail page

- **WHEN** the course's Teacher opens the student detail page for a student with a stored photo
- **THEN** the photo is displayed on the page

### Requirement: Accepted formats are validated by decoding

The system SHALL accept jpeg, heic, heif, png, and webp uploads. Validation SHALL be performed by attempting to open and decode the image with Pillow (with HEIC support registered), not by trusting the file extension. Files that cannot be decoded SHALL be rejected with a validation error, as SHALL files exceeding the configured maximum upload size.

#### Scenario: iPhone HEIC accepted

- **WHEN** an Admin uploads a `.heic` photo taken on an iPhone
- **THEN** the upload is accepted and normalized

#### Scenario: Undecodable file rejected regardless of extension

- **WHEN** a file named `photo.jpg` contains non-image bytes
- **THEN** the save is rejected with a validation error and no file is stored

#### Scenario: Oversized upload rejected

- **WHEN** an upload exceeds the configured maximum size
- **THEN** the save is rejected with a validation error before image decoding

### Requirement: Stored photos are normalized

Every stored photo SHALL be a JPEG file named `<uuid>.jpg` under `students/`, with EXIF orientation baked into the pixels, all EXIF metadata (including GPS) removed, color flattened to RGB, and dimensions reduced to fit within 600×600 pixels while preserving aspect ratio (never upscaled).

#### Scenario: Normalization of a phone photo

- **WHEN** a 4032×3024 HEIC photo with GPS EXIF and an orientation flag is uploaded
- **THEN** the stored file is a JPEG whose pixels are upright, whose dimensions fit within 600×600 with the original aspect ratio, and which contains no EXIF metadata

#### Scenario: Small photos are not upscaled

- **WHEN** an uploaded photo is already smaller than 600×600 in both dimensions
- **THEN** the stored JPEG keeps the original pixel dimensions

#### Scenario: Replacement removes the previous file

- **WHEN** a Student with a stored photo is saved with a new photo
- **THEN** the new normalized JPEG replaces it and the previous file is deleted from storage, leaving exactly one photo file for that Student

### Requirement: Media storage and development serving

The project SHALL define `MEDIA_ROOT` and `MEDIA_URL`, serve media files in development via the URL configuration, and keep the media directory out of version control.

#### Scenario: Media URL resolves in development

- **WHEN** a Student has a stored photo and `DEBUG` is on
- **THEN** the photo is retrievable at `MEDIA_URL` + stored path from the development server

#### Scenario: Media not committed

- **WHEN** the repository is inspected
- **THEN** the media directory is git-ignored
