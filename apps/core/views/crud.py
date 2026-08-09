from django.contrib import messages
from django.shortcuts import redirect
from django.core.exceptions import ImproperlyConfigured
from apps.core.mixins.search import SearchMixin
from apps.core.mixins.ordering import OrderingMixin
from apps.core.mixins.context import ContextMixin
from apps.core.mixins.pagination import PaginationMixin
from apps.core.mixins.filters import FilterMixin
from django.views.generic import (
    ListView,
    CreateView,
    UpdateView,
    DeleteView,
)


class BaseListView(
    SearchMixin,
    OrderingMixin,
    ContextMixin,
    FilterMixin,
    PaginationMixin,
    ListView,
):
    """
    Base class for enterprise list views.

    Provides common functionality shared by all
    CRUD list pages.
    """
    

    selector = None

    default_ordering = "name"

    

    page_title = ""

    selector_kwargs = {}
    def get_queryset(self):
        if self.selector is None:
            raise ImproperlyConfigured(
                "selector must be defined."
            )

        queryset = type(self).selector(
            search=self.get_search(),
            filters=self.get_filters(),
        )

        return queryset.order_by(
            *self.get_ordering()
        )


class BaseCreateView(CreateView):
    """
    Base class for create operations using a service function.
    """

    service = None

    success_message = "Created successfully."

    def form_valid(self, form):
        if self.service is None:
            raise NotImplementedError(
                "service must be defined."
            )

        self.object = type(self).service(
            **form.cleaned_data
        )

        messages.success(
            self.request,
            self.success_message,
        )

        return redirect(self.success_url)


class BaseUpdateView(UpdateView):
    """
    Base class for update operations using a service function.
    """

    service = None

    success_message = "Updated successfully."

    def form_valid(self, form):
        if self.service is None:
            raise NotImplementedError(
                "service must be defined."
            )

        self.object = type(self).service(
            self.get_object(),
            **form.cleaned_data,
        )

        messages.success(
            self.request,
            self.success_message,
        )

        return redirect(self.success_url)


class BaseDeleteView(DeleteView):
    """
    Base class for delete operations using a service function.
    """

    service = None

    success_message = "Deleted successfully."

    def form_valid(self, form):
        if self.service is None:
            raise NotImplementedError(
                "service must be defined."
            )

        type(self).service(
            self.get_object()
        )

        messages.success(
            self.request,
            self.success_message,
        )

        return redirect(self.success_url)