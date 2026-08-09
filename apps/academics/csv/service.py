



class InstitutionCSVImportView(View):
    """
    Upload and validate Institution CSV files.

    Preview only.
    No database records are created during upload.
    """

    template_name = (
        "academics/csv/institution_import.html"
    )

    def get(self, request, *args, **kwargs):

        form = InstitutionCSVImportForm()

        return render(
            request,
            self.template_name,
            {
                "form": form,
            },
        )

    def post(self, request, *args, **kwargs):

        # ==================================================
        # CONFIRM IMPORT
        # ==================================================

        if request.POST.get("action") == "confirm_import":

            rows = request.session.get(
                "institution_csv_rows"
            )

            if not rows:

                messages.error(
                    request,
                    "No validated CSV data was found. "
                    "Please upload the CSV again.",
                )

                return redirect(
                    "academics:institution-import"
                )

            try:

                with transaction.atomic():

                    for row in rows:

                        Institution.objects.create(
                            name=row["name"],
                            short_name=row["short_name"],
                            email=row["email"],
                            phone_number=row["phone_number"],
                            website=row["website"],
                            address=row["address"],
                            is_active=(
                                row["is_active"] == "1"
                            ),
                        )

            except IntegrityError:

                messages.error(
                    request,
                    (
                        "Import failed because a database "
                        "constraint was violated. "
                        "No institutions were imported."
                    ),
                )

                return redirect(
                    "academics:institution-import"
                )

            except Exception:

                messages.error(
                    request,
                    (
                        "An unexpected error occurred "
                        "during import. "
                        "No institutions were imported."
                    ),
                )

                return redirect(
                    "academics:institution-import"
                )

            request.session.pop(
                "institution_csv_rows",
                None,
            )

            messages.success(
                request,
                f"{len(rows)} institutions "
                "imported successfully.",
            )

            return redirect(
                "academics:institution-list"
            )

        # ==================================================
        # CSV UPLOAD + VALIDATION
        # ==================================================

        form = InstitutionCSVImportForm(
            request.POST,
            request.FILES,
        )

        if not form.is_valid():

            return render(
                request,
                self.template_name,
                {
                    "form": form,
                },
            )

        uploaded_file = form.cleaned_data[
            "csv_file"
        ]

        try:

            rows = read_institution_csv(
                uploaded_file
            )

            validate_institution_rows(
                rows
            )

        except ValueError as exc:

            form.add_error(
                "csv_file",
                str(exc),
            )

            return render(
                request,
                self.template_name,
                {
                    "form": form,
                },
            )

        request.session[
            "institution_csv_rows"
        ] = rows

        return render(
            request,
            self.template_name,
            {
                "form": form,
                "preview_rows": rows,
                "preview_count": len(rows),
            },
        )