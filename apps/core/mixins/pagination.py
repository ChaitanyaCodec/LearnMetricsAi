"""
Pagination mixin for enterprise CRUD list views.
"""


class PaginationMixin:
    """
    Provides common pagination configuration for CRUD list views.
    """

    paginate_by = 10
    page_size_parameter = "page_size"

    max_page_size = 100

    def get_paginate_by(self, queryset):
        """
        Return the number of objects displayed per page.
        """

        page_size = self.request.GET.get(
            self.page_size_parameter
        )

        if not page_size:
            return self.paginate_by

        try:
            page_size = int(page_size)
        except (TypeError, ValueError):
            return self.paginate_by

        if page_size <= 0:
            return self.paginate_by

        return min(
            page_size,
            self.max_page_size,
        )