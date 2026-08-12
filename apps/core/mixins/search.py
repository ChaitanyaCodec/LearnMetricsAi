"""
Search mixin for enterprise CRUD list views.
"""


class SearchMixin:
    """
    Adds search support to list views.
    """

    search_parameter = "search"

    def get_search(self):
        """
        Return the search keyword.
        """

        return self.request.GET.get(
            self.search_parameter,
            "",
        ).strip()

    def get_search_context(self):
        """
        Context used by templates.
        """

        return {
            "search": self.get_search(),
        }