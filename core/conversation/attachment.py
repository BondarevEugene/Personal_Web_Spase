from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from .enums import AttachmentType


class Attachment:
    """
    Любое вложение сцены.

    Image
    PDF
    DOCX
    ZIP
    Video
    URL
    """

    def __init__(
        self,
        attachment_type: AttachmentType,
        path: str,
        title: str = "",
        description: str = "",
        downloadable: bool = True,
    ):

        self.id = str(uuid4())

        self.type = attachment_type

        self.path = Path(path)

        self.title = title

        self.description = description

        self.downloadable = downloadable

    @property
    def exists(self):

        return self.path.exists()

    @property
    def filename(self):

        return self.path.name

    @property
    def extension(self):

        return self.path.suffix

    def to_dict(self):

        return {
            "id": self.id,
            "type": self.type.value,
            "path": str(self.path),
            "title": self.title,
            "description": self.description,
            "downloadable": self.downloadable,
        }