from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import FileResponse, JsonResponse,Http404
from django.views import View
from django.core.paginator import Paginator
from django.views.generic import TemplateView
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render
from apps.accounts.mixins import AdminRequiredMixin
from apps.teachers.models import TeachingAssignment
from apps.accounts.models import User
from apps.academics.models import Subject
from .selectors import (
    get_admin_review_queue,
    get_authorized_document,
    get_authorized_documents,
)

from .forms import DocumentForm
from .models import (
                     
    Document,
    DocumentVersion,
)
from .permissions import (
    can_manage_document,
    is_documents_admin,
    
)
from .processing import process_document_version
from .selectors import (
    get_authorized_document,
    get_authorized_documents,
)
from .services import (
    DocumentServiceError,
    approve_document_version,
    create_document_with_initial_version,
    reject_document_version,
    retire_document,
    submit_latest_version_for_review,
    upload_new_document_version,
)


def error_response(message, status=400):
    return JsonResponse(
        {"detail": message},
        status=status,
    )


def serialize_version(version):
    return {
        "id": version.id,
        "version_number": version.version_number,
        "original_filename": version.original_filename,
        "file_size": version.file_size,
        "processing_status": version.processing_status,
        "review_status": version.review_status,
        "page_count": version.page_count,
        "chunk_count": version.chunk_count,
        "processing_error": version.processing_error,
        "uploaded_at": version.created_at.isoformat(),
        "reviewed_at": (
            version.reviewed_at.isoformat()
            if version.reviewed_at
            else None
        ),
    }


def serialize_document(document):
    subject = document.subject
    semester = subject.semester
    course = semester.course
    department = course.department
    institution = department.institution

    return {
        "id": document.id,
        "title": document.title,
        "description": document.description,
        "status": document.status,
        "is_active": document.is_active,
        "created_at": document.created_at.isoformat(),
        "subject": {
            "id": subject.id,
            "code": subject.code,
            "name": subject.name,
            "semester": semester.name,
            "semester_number": semester.semester_number,
            "course": course.name,
            "department": department.name,
            "institution": institution.name,
        },
        "published_version_id": document.published_version_id,
    }


def run_processing(version):
    try:
        process_document_version(version.id)
        version.refresh_from_db()
        return version, True
    except Exception:
        version.refresh_from_db()
        return version, False

class DocumentListView(
    LoginRequiredMixin,
    TemplateView,
):
    template_name = "documents/document/list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        search = self.request.GET.get(
            "search",
            "",
        ).strip()

        filters = {
            "subject": self.request.GET.get("subject"),
            "status": self.request.GET.get("status"),
        }

        # Get the documents that the current user is authorized
        # to access, without search/status/subject filters.
        authorized_documents = get_authorized_documents(
            user=self.request.user,
        )

        # Build filter choices from the user's authorized scope,
        # not from the already-filtered result set.
        subject_ids = (
            authorized_documents
            .values_list("subject_id", flat=True)
            .distinct()
        )

        subjects = Subject.objects.filter(
            pk__in=subject_ids
        ).order_by("name")

        # Apply the actual search and filters to the document list.
        documents = get_authorized_documents(
            user=self.request.user,
            search=search,
            filters=filters,
        )

        paginator = Paginator(documents, 10)

        page_obj = paginator.get_page(
            self.request.GET.get("page")
        )

        context.update(
            {
                "documents": page_obj.object_list,
                "page_obj": page_obj,
                "subjects": subjects,
                "search": search,
                "selected_subject": filters["subject"],
                "selected_status": filters["status"],
                "status_choices": Document.Status.choices,
            }
        )

        return context

class DocumentListAPIView(LoginRequiredMixin, View):
    def get(self, request):
        documents = get_authorized_documents(
            user=request.user,
            search=request.GET.get("search", ""),
            filters={
                "subject": request.GET.get("subject"),
                "status": request.GET.get("status"),
            },
        )

        return JsonResponse(
            {
                "results": [
                    serialize_document(document)
                    for document in documents
                ]
            }
        )

    def post(self, request):
        form = DocumentForm(request.POST)
        source_file = request.FILES.get("source_file")

        if not form.is_valid():
            return JsonResponse(
                {"errors": form.errors.get_json_data()},
                status=400,
            )

        if not source_file:
            return error_response(
                "A source file is required."
            )

        try:
            version = create_document_with_initial_version(
                user=request.user,
                source_file=source_file,
                **form.cleaned_data,
            )
        except DocumentServiceError as exc:
            return error_response(str(exc))

        version, processed = run_processing(version)

        document = get_authorized_document(
            user=request.user,
            document_id=version.document_id,
        )

        return JsonResponse(
            {
                "document": serialize_document(document),
                "version": serialize_version(version),
                "processing_succeeded": processed,
            },
            status=201,
        )


class DocumentDetailAPIView(LoginRequiredMixin, View):
    def get(self, request, document_id):
        document = get_authorized_document(
            user=request.user,
            document_id=document_id,
        )

        if document is None:
            return error_response(
                "Document not found.",
                status=404,
            )

        if (
            is_documents_admin(request.user)
            or can_manage_document(request.user, document)
        ):
            versions = document.versions.order_by(
                "-version_number"
            )
        elif document.published_version_id:
            versions = [document.published_version]
        else:
            versions = []

        return JsonResponse(
            {
                "document": serialize_document(document),
                "versions": [
                    serialize_version(version)
                    for version in versions
                ],
            }
        )


class DocumentVersionUploadAPIView(
    LoginRequiredMixin,
    View,
):
    def post(self, request, document_id):
        source_file = request.FILES.get("source_file")

        if not source_file:
            return error_response(
                "A source file is required."
            )

        try:
            version = upload_new_document_version(
                user=request.user,
                document_id=document_id,
                source_file=source_file,
            )
        except DocumentServiceError as exc:
            return error_response(str(exc))

        version, processed = run_processing(version)

        return JsonResponse(
            {
                "version": serialize_version(version),
                "processing_succeeded": processed,
            },
            status=201,
        )


class DocumentSubmitReviewAPIView(
    LoginRequiredMixin,
    View,
):
    def post(self, request, document_id):
        try:
            version = submit_latest_version_for_review(
                user=request.user,
                document_id=document_id,
            )
        except DocumentServiceError as exc:
            return error_response(str(exc))

        return JsonResponse(
            {"version": serialize_version(version)}
        )


class DocumentVersionApproveAPIView(
    LoginRequiredMixin,
    View,
):
    def post(self, request, version_id):
        try:
            version = approve_document_version(
                user=request.user,
                document_version_id=version_id,
            )
        except DocumentVersion.DoesNotExist:
            return error_response(
                "Document version not found.",
                status=404,
            )
        except DocumentServiceError as exc:
            return error_response(str(exc))

        return JsonResponse(
            {"version": serialize_version(version)}
        )


class DocumentVersionRejectAPIView(
    LoginRequiredMixin,
    View,
):
    def post(self, request, version_id):
        try:
            version = reject_document_version(
                user=request.user,
                document_version_id=version_id,
                reason=request.POST.get("reason", ""),
            )
        except DocumentVersion.DoesNotExist:
            return error_response(
                "Document version not found.",
                status=404,
            )
        except DocumentServiceError as exc:
            return error_response(str(exc))

        return JsonResponse(
            {"version": serialize_version(version)}
        )


class DocumentRetireAPIView(LoginRequiredMixin, View):
    def post(self, request, document_id):
        try:
            document = retire_document(
                user=request.user,
                document_id=document_id,
                reason=request.POST.get("reason", ""),
            )
        except DocumentServiceError as exc:
            return error_response(str(exc))

        return JsonResponse(
            {"document": serialize_document(document)}
        )


class DocumentVersionRetryAPIView(
    LoginRequiredMixin,
    View,
):
    def post(self, request, version_id):
        if not is_documents_admin(request.user):
            return error_response(
                "Only administrators can retry processing.",
                status=403,
            )

        try:
            version = DocumentVersion.objects.get(pk=version_id)
        except DocumentVersion.DoesNotExist:
            return error_response(
                "Document version not found.",
                status=404,
            )

        if (
            version.processing_status
            != DocumentVersion.ProcessingStatus.FAILED
        ):
            return error_response(
                "Only failed versions can be retried."
            )

        version, processed = run_processing(version)

        return JsonResponse(
            {
                "version": serialize_version(version),
                "processing_succeeded": processed,
            }
        )


class DocumentVersionDownloadAPIView(
    LoginRequiredMixin,
    View,
):
    def get(self, request, document_id, version_id):
        document = get_authorized_document(
            user=request.user,
            document_id=document_id,
        )

        if document is None:
            return error_response(
                "Document not found.",
                status=404,
            )

        version = document.versions.filter(
            pk=version_id
        ).first()

        if version is None:
            return error_response(
                "Document version not found.",
                status=404,
            )

        may_download_any_version = (
            is_documents_admin(request.user)
            or can_manage_document(request.user, document)
        )

        if (
            not may_download_any_version
            and version.id != document.published_version_id
        ):
            return error_response(
                "Document version not found.",
                status=404,
            )

        return FileResponse(
            version.source_file.open("rb"),
            as_attachment=True,
            filename=version.original_filename,
        )




class DocumentUploadView(LoginRequiredMixin, View):
    template_name = "documents/document/upload.html"

    def get_subject_queryset(self):
        if self.request.user.role == User.Roles.ADMIN:
            return Subject.objects.filter(
                is_active=True,
                semester__is_active=True,
                semester__course__is_active=True,
            ).order_by("name")

        if self.request.user.role == User.Roles.TEACHER:
            return Subject.objects.filter(
                teaching_assignments__teacher__user=(
                    self.request.user
                ),
                teaching_assignments__is_active=True,
                is_active=True,
                semester__is_active=True,
                semester__course__is_active=True,
            ).distinct().order_by("name")

        return Subject.objects.none()

    def get_form(self, *args, **kwargs):
        form = DocumentForm(*args, **kwargs)
        form.fields["subject"].queryset = (
            self.get_subject_queryset()
        )
        return form

    def dispatch(self, request, *args, **kwargs):
        if request.user.role not in [
            User.Roles.ADMIN,
            User.Roles.TEACHER,
        ]:
            raise PermissionDenied(
                "You are not allowed to upload documents."
            )

        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return render(
            request,
            self.template_name,
            {"form": self.get_form()},
        )

    def post(self, request, *args, **kwargs):
        form = self.get_form(request.POST)
        source_file = request.FILES.get("source_file")

        if not source_file:
            form.add_error(
                None,
                "Please select a document file.",
            )

        if form.is_valid():
            try:
                version = create_document_with_initial_version(
                    user=request.user,
                    source_file=source_file,
                    **form.cleaned_data,
                )
            except DocumentServiceError as exc:
                form.add_error(None, str(exc))
            else:
                version, processed = run_processing(version)

                if processed:
                    messages.success(
                        request,
                        "Document uploaded and processed successfully. "
                        "Submit it for review when ready.",
                    )
                else:
                    messages.warning(
                        request,
                        "Document uploaded, but processing failed. "
                        "An administrator can retry it.",
                    )

                return redirect(
                    "documents:detail",
                    document_id=version.document_id,
                )

        return render(
            request,
            self.template_name,
            {"form": form},
        )

class DocumentDetailView(
    LoginRequiredMixin,
    TemplateView,
):
    # template_name = "documents/document/detail.html"
    template_name = "documents/detail.html"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        document = get_authorized_document(
            user=self.request.user,
            document_id=self.kwargs["document_id"],
        )

        if document is None:
            raise Http404("Document not found.")

        may_manage = (
            is_documents_admin(self.request.user)
            or can_manage_document(
                self.request.user,
                document,
            )
        )

        if may_manage:
            versions = document.versions.order_by(
                "-version_number"
            )
        elif document.published_version_id:
            versions = [document.published_version]
        else:
            versions = []

        context.update(
            {
                "document": document,
                "versions": versions,
                "may_manage": may_manage,
                "latest_version": (
                    versions[0] if versions else None
                ),
            }
        )

        return context


class DocumentVersionUploadView(
    LoginRequiredMixin,
    View,
):
    def post(self, request, document_id):
        source_file = request.FILES.get("source_file")

        if not source_file:
            messages.error(
                request,
                "Please select a file to upload.",
            )
            return redirect(
                "documents:detail",
                document_id=document_id,
            )

        try:
            version = upload_new_document_version(
                user=request.user,
                document_id=document_id,
                source_file=source_file,
            )
        except DocumentServiceError as exc:
            messages.error(request, str(exc))
        else:
            version, processed = run_processing(version)

            if processed:
                messages.success(
                    request,
                    f"Version {version.version_number} was uploaded "
                    "and processed successfully.",
                )
            else:
                messages.warning(
                    request,
                    "The new version was uploaded, but processing failed.",
                )

        return redirect(
            "documents:detail",
            document_id=document_id,
        )


class DocumentSubmitReviewView(
    LoginRequiredMixin,
    View,
):
    def post(self, request, document_id):
        try:
            version = submit_latest_version_for_review(
                user=request.user,
                document_id=document_id,
            )
        except DocumentServiceError as exc:
            messages.error(request, str(exc))
        else:
            messages.success(
                request,
                f"Version {version.version_number} was submitted "
                "for review.",
            )

        return redirect(
            "documents:detail",
            document_id=document_id,
        )


class DocumentReviewQueueView(
    AdminRequiredMixin,
    TemplateView,
):
    template_name = "documents/review/queue.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["versions"] = get_admin_review_queue()
        return context


class DocumentVersionApproveView(
    AdminRequiredMixin,
    View,
):
    def post(self, request, version_id):
        try:
            version = approve_document_version(
                user=request.user,
                document_version_id=version_id,
            )
        except (
            DocumentVersion.DoesNotExist,
            DocumentServiceError,
        ) as exc:
            messages.error(request, str(exc))
        else:
            messages.success(
                request,
                f"Version {version.version_number} was approved.",
            )

        return redirect("documents:review-queue")


class DocumentVersionRejectView(
    AdminRequiredMixin,
    View,
):
    def post(self, request, version_id):
        try:
            version = reject_document_version(
                user=request.user,
                document_version_id=version_id,
                reason=request.POST.get("reason", ""),
            )
        except (
            DocumentVersion.DoesNotExist,
            DocumentServiceError,
        ) as exc:
            messages.error(request, str(exc))
        else:
            messages.success(
                request,
                f"Version {version.version_number} was rejected.",
            )

        return redirect("documents:review-queue")


class DocumentVersionRetryView(
    AdminRequiredMixin,
    View,
):
    def post(self, request, version_id):
        try:
            version = DocumentVersion.objects.get(pk=version_id)
        except DocumentVersion.DoesNotExist:
            messages.error(
                request,
                "Document version not found.",
            )
            return redirect("documents:review-queue")

        if (
            version.processing_status
            != DocumentVersion.ProcessingStatus.FAILED
        ):
            messages.error(
                request,
                "Only failed versions can be retried.",
            )
            return redirect("documents:detail", version.document_id)

        version, processed = run_processing(version)

        if processed:
            messages.success(
                request,
                "Document processing completed successfully.",
            )
        else:
            messages.error(
                request,
                "Document processing failed again.",
            )

        return redirect("documents:detail", version.document_id)


class DocumentRetireView(
    AdminRequiredMixin,
    View,
):
    def post(self, request, document_id):
        try:
            document = retire_document(
                user=request.user,
                document_id=document_id,
                reason=request.POST.get("reason", ""),
            )
        except DocumentServiceError as exc:
            messages.error(request, str(exc))
        else:
            messages.success(
                request,
                f"'{document.title}' was retired.",
            )

        return redirect("documents:detail", document_id=document_id)