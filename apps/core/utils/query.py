"""
Reusable queryset utilities.
"""

from django.core.exceptions import FieldError


def apply_filters(queryset, filters, allowed_filters):
    """
    Apply validated filters to a queryset.
    """

    filters = filters or {}

    query_filters = {}

    for parameter, value in filters.items():

        field = allowed_filters.get(parameter)

        if field is None:
            continue

        query_filters[field] = value

    if not query_filters:
        return queryset

    try:
        return queryset.filter(**query_filters)

    except FieldError:
        raise ValueError(
            "Invalid filter configuration."
        )