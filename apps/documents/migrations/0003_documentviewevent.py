import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("documents", "0002_remove_document_rejection_reason_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="DocumentViewEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("event_type", models.CharField(choices=[("PREVIEW", "Preview"), ("DOWNLOAD", "Download")], max_length=10)),
                ("viewed_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("document", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="view_events", to="documents.document")),
                ("document_version", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="view_events", to="documents.documentversion")),
                ("student", models.ForeignKey(limit_choices_to={"role": "STUDENT"}, on_delete=django.db.models.deletion.CASCADE, related_name="document_view_events", to=settings.AUTH_USER_MODEL)),
            ],
            options={"verbose_name": "Document view event", "verbose_name_plural": "Document view events", "ordering": ["-viewed_at"]},
        ),
        migrations.AddIndex(model_name="documentviewevent", index=models.Index(fields=["document", "event_type", "viewed_at"], name="documents_d_documen_98ad51_idx")),
        migrations.AddIndex(model_name="documentviewevent", index=models.Index(fields=["document", "student"], name="documents_d_documen_3c8a65_idx")),
    ]
