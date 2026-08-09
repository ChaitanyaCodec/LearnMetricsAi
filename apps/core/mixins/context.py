"""
Context mixin for enterprise CRUD list views.
"""


class ContextMixin:
    """
    Adds common context to CRUD pages.
    """

    page_title = ""

    page_subtitle = ""

    def get_context_data(self, **kwargs):

        context = super().get_context_data(
            **kwargs
        )

        context.update(
            {
                "page_title": self.page_title,
                "page_subtitle": self.page_subtitle,
                "search": self.get_search(),
                "ordering": self.request.GET.get(
                    self.ordering_parameter,
                    "",
                ),
                "ordering_options": (
                    self.get_ordering_options()
                ),
                "filters": self.get_filters(),
                "filter_choices": (
                    self.get_filter_choices()
                ),
            }
        )

        return context