from django.conf import settings
from django.core.files.storage import FileSystemStorage


class PrivateDocumentStorage(FileSystemStorage):
    def __init__(self):
        super().__init__(
            location=settings.PRIVATE_DOCUMENTS_ROOT,
        )

    def url(self, name):
        raise ValueError(
            "Private document files must be accessed through "
            "an authorized download view."
        )


private_document_storage = PrivateDocumentStorage()