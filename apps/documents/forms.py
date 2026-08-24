from django import forms

from .models import Document, DocumentVersion


class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = [
            "title",
            "description",
            "subject",
        ]


class DocumentVersionUploadForm(forms.ModelForm):
    class Meta:
        model = DocumentVersion
        fields = [
            "source_file",
        ]