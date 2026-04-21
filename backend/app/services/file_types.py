from pathlib import Path

from app.models.enums import SourceFileType

TEXT_EXTENSIONS = {".txt", ".md", ".markdown", ".html", ".htm", ".json", ".csv", ".py", ".js", ".ts", ".docx"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tiff"}
AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v"}
PDF_EXTENSIONS = {".pdf"}


def infer_source_file_type(path: Path) -> SourceFileType:
    extension = path.suffix.lower()
    if extension in AUDIO_EXTENSIONS:
        return SourceFileType.AUDIO
    if extension in VIDEO_EXTENSIONS:
        return SourceFileType.VIDEO
    if extension in IMAGE_EXTENSIONS:
        return SourceFileType.IMAGE
    if extension in PDF_EXTENSIONS:
        return SourceFileType.PDF
    if extension == ".md":
        return SourceFileType.MARKDOWN
    if extension in TEXT_EXTENSIONS:
        return SourceFileType.TEXT
    return SourceFileType.OTHER
