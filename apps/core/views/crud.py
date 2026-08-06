
"""
Reusable CRUD base views.

These views provide common behavior for all CRUD modules.
"""

from django.contrib import messages
from django.shortcuts import redirect
from django.views.generic import (
    CreateView,
    UpdateView,
    DeleteView,
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

        type(self).service(**form.cleaned_data)

        messages.success(
            self.request,
            self.success_message,
        )

        return redirect(self.get_success_url())


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

        type(self).service(
            self.get_object(),
            **form.cleaned_data,
        )

        messages.success(
            self.request,
            self.success_message,
        )

        return redirect(self.get_success_url())



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

        type(self).service(self.get_object())

        messages.success(
            self.request,
            self.success_message,
        )

        return redirect(self.get_success_url())