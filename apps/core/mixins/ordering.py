"""
Ordering mixin for enterprise CRUD list views.
"""


class OrderingMixin:
    """
    Adds safe ordering support to CRUD list views.
    """

    ordering_parameter = "ordering"

    default_ordering = ("name",)

    allowed_ordering = ()

    ordering_labels = {}

    def get_ordering(self):
        """
        Return validated ordering.
        """

        ordering = self.request.GET.get(
            self.ordering_parameter
        )

        if (
            ordering
            and ordering in self.allowed_ordering
        ):
            return (ordering,)

        return self.default_ordering

    def get_ordering_options(self):
        """
        Return ordering options for templates.
        """

        return [
            (
                value,
                self.ordering_labels.get(
                    value,
                    value,
                ),
            )
            for value in self.allowed_ordering
        ]