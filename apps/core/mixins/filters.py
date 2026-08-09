"""
Reusable filtering mixin for CRUD list views.
"""


class FilterMixin:
    """
    Provides common filter handling and filter choices.
    """

    filter_parameters = ()

    filter_choices = {}

    def get_filters(self):
        """
        Read supported filter parameters from the request.
        """

        filters = {}

        for parameter in self.filter_parameters:

            value = self.request.GET.get(parameter)

            if value not in (None, ""):
                filters[parameter] = value

        return filters

    def get_filter_choices(self):
        """
        Return choices required by filter controls.
        """

        return self.filter_choices