from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from apps.core.mixins import FormConfigContextMixin

from .forms import ClientForm
from .models import Client


class ClientOwnerMixin:
    def get_queryset(self):
        return Client.objects.filter(user=self.request.user)


class ClientListView(LoginRequiredMixin, ClientOwnerMixin, ListView):
    model = Client
    template_name = "clients/client_list.html"
    context_object_name = "clients"


class ClientDetailView(LoginRequiredMixin, ClientOwnerMixin, DetailView):
    model = Client
    template_name = "clients/client_detail.html"
    context_object_name = "client"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["vehicles"] = self.object.vehicles.all()
        return context


class ClientCreateView(LoginRequiredMixin, FormConfigContextMixin, CreateView):
    model = Client
    form_class = ClientForm
    template_name = "clients/client_form.html"

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, "Client added.")
        return super().form_valid(form)


class ClientUpdateView(LoginRequiredMixin, ClientOwnerMixin, FormConfigContextMixin, UpdateView):
    model = Client
    form_class = ClientForm
    template_name = "clients/client_form.html"

    def form_valid(self, form):
        messages.success(self.request, "Client updated.")
        return super().form_valid(form)


class ClientDeleteView(LoginRequiredMixin, ClientOwnerMixin, DeleteView):
    model = Client
    template_name = "clients/client_confirm_delete.html"
    success_url = reverse_lazy("clients:list")

    def form_valid(self, form):
        messages.success(self.request, "Client deleted.")
        return super().form_valid(form)


@login_required
def client_quick_add_api(request):
    """Quick-create a Client from the vehicle form modal. POST only."""
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)
    first_name = request.POST.get("first_name", "").strip()
    last_name = request.POST.get("last_name", "").strip()
    company = request.POST.get("company", "").strip()
    email = request.POST.get("email", "").strip()
    phone = request.POST.get("phone", "").strip()
    notes = request.POST.get("notes", "").strip()
    if not first_name and not company:
        return JsonResponse(
            {"errors": {"first_name": ["First name or company name is required."]}},
            status=400,
        )
    client = Client.objects.create(
        user=request.user,
        first_name=first_name,
        last_name=last_name,
        company=company,
        email=email,
        phone=phone,
        notes=notes,
    )
    return JsonResponse({"pk": client.pk, "label": str(client)})
