import io
import os
from xml.sax.saxutils import escape

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)
from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from apps.core.mixins import FormConfigContextMixin, ModuleEnabledMixin, VehicleOwnerMixin
from apps.formconfig.utils import get_label_overrides
from apps.garages.utils import get_active_garage

from .forms import ServiceRecordForm, ServiceRecordItemFormSet
from .models import ServiceRecord, ServiceRecordItem

PDF_FONT_NAME = "Helvetica"
PDF_FONT_BOLD_NAME = "Helvetica-Bold"
_PDF_FONT_REGISTERED = False


def ensure_pdf_font():
    global _PDF_FONT_REGISTERED, PDF_FONT_NAME, PDF_FONT_BOLD_NAME
    if _PDF_FONT_REGISTERED:
        return
    candidates = [
        ("/System/Library/Fonts/Supplemental/Arial Unicode.ttf", "ArialUnicodeMS"),
        ("/System/Library/Fonts/Supplemental/Arial.ttf", "Arial"),
        ("/Library/Fonts/Arial Unicode.ttf", "ArialUnicodeMS"),
        ("/Library/Fonts/Arial.ttf", "Arial"),
    ]
    for path, base_name in candidates:
        if not os.path.exists(path):
            continue
        try:
            regular_name = f"{base_name}-Regular"
            bold_name = f"{base_name}-Bold"
            pdfmetrics.registerFont(TTFont(regular_name, path))
            pdfmetrics.registerFont(TTFont(bold_name, path))
            PDF_FONT_NAME = regular_name
            PDF_FONT_BOLD_NAME = bold_name
            _PDF_FONT_REGISTERED = True
            return
        except Exception:
            continue
    _PDF_FONT_REGISTERED = True

SERVICE_FIELD_DEFAULT_LABELS = {
    "date": "Dátum",
    "mileage": "Kilométeróra állás",
    "cost": "Teljes költség",
    "notes": "Megjegyzés",
    "item_service_type": "Szerviztípus",
    "item_replacement_part": "Cserélt alkatrész",
    "item_part_price": "Alkatrész ára",
    "item_consumable": "Fogyóanyag",
    "item_work_hours": "Munkaóra",
    "item_note": "Sor megjegyzés",
}


class VehicleContextMixin(ModuleEnabledMixin, VehicleOwnerMixin):
    module_key = "services"

    def get_queryset(self):
        return ServiceRecord.objects.filter(vehicle=self.get_vehicle()).prefetch_related("items")


class ServiceRecordListView(LoginRequiredMixin, VehicleContextMixin, ListView):
    model = ServiceRecord
    template_name = "services/service_list.html"
    context_object_name = "records"

    def get_queryset(self):
        qs = super().get_queryset()
        query = (self.request.GET.get("q") or "").strip()
        if query:
            base_filter = (
                Q(notes__icontains=query)
                | Q(items__service_type__icontains=query)
                | Q(items__replacement_part__icontains=query)
                | Q(items__consumable__icontains=query)
                | Q(items__note__icontains=query)
            )
            if query.isdigit():
                base_filter |= Q(mileage=int(query))
            qs = qs.filter(base_filter).distinct()
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_query"] = (self.request.GET.get("q") or "").strip()
        return context


class GlobalServiceHistoryView(LoginRequiredMixin, ModuleEnabledMixin, ListView):
    module_key = "services"
    model = ServiceRecord
    template_name = "services/service_history_all.html"
    context_object_name = "records"

    def get_queryset(self):
        garage = get_active_garage(self.request)
        qs = ServiceRecord.objects.select_related("vehicle").prefetch_related("items")
        if garage:
            qs = qs.filter(vehicle__garage=garage)
        else:
            qs = qs.filter(vehicle__owner=self.request.user)
        return qs.order_by("date", "created_at")


class ServiceRecordDetailView(LoginRequiredMixin, VehicleContextMixin, DetailView):
    model = ServiceRecord
    template_name = "services/service_detail.html"
    context_object_name = "record"


class ServiceRecordPDFView(LoginRequiredMixin, VehicleContextMixin, DetailView):
    model = ServiceRecord

    def get(self, request, *args, **kwargs):
        record = self.get_object()
        vehicle = self.get_vehicle()
        garage = getattr(vehicle, "garage", None) or get_active_garage(request)
        garage_label = getattr(garage, "name", "") or (str(garage) if garage else "—")
        ensure_pdf_font()

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=18 * mm,
            leftMargin=18 * mm,
            topMargin=16 * mm,
            bottomMargin=16 * mm,
            title=f"Szervizbejegyzés {record.pk}",
        )
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name="Muted", parent=styles["Normal"], textColor=colors.HexColor("#6B7280")))
        styles.add(
            ParagraphStyle(
                name="SectionHeading",
                parent=styles["Heading2"],
                fontName=PDF_FONT_BOLD_NAME,
                fontSize=12,
                spaceAfter=6,
            )
        )
        styles.add(
            ParagraphStyle(
                name="InvoiceTotal",
                parent=styles["Normal"],
                alignment=TA_RIGHT,
                fontName=PDF_FONT_BOLD_NAME,
                fontSize=12,
                textColor=colors.HexColor("#111827"),
            )
        )
        styles.add(
            ParagraphStyle(
                name="TableCell",
                parent=styles["Normal"],
                fontName=PDF_FONT_NAME,
                fontSize=8.4,
                leading=10,
                textColor=colors.HexColor("#111827"),
                splitLongWords=True,
                wordWrap="CJK",
            )
        )
        styles.add(
            ParagraphStyle(
                name="TableHeaderCell",
                parent=styles["TableCell"],
                fontName=PDF_FONT_BOLD_NAME,
                textColor=colors.white,
            )
        )
        story = []

        def cell(value):
            text = str(value).strip() if value is not None else ""
            if not text:
                text = "—"
            # Escape XML-sensitive chars because reportlab Paragraph parses markup.
            return Paragraph(escape(text), styles["TableCell"])

        def header_cell(value):
            return Paragraph(escape(str(value)), styles["TableHeaderCell"])

        story.append(Paragraph("SZERVIZBEJEGYZÉS", styles["Title"]))
        story.append(Paragraph(f"Bejegyzés #{record.pk}", styles["Muted"]))
        story.append(Spacer(1, 10))

        details_rows = [
            ["Garázs", garage_label],
            ["Jármű", str(vehicle)],
            ["Dátum", f"{record.date:%d %b %Y}"],
            ["Kilométer állás", str(record.mileage) if record.mileage is not None else "—"],
        ]
        details_table = Table(details_rows, colWidths=[42 * mm, 130 * mm])
        details_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F9FAFB")),
                    ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#D1D5DB")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
                    ("FONTNAME", (0, 0), (0, -1), PDF_FONT_BOLD_NAME),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#111827")),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        story.append(details_table)
        story.append(Spacer(1, 12))

        story.append(Paragraph("Szerviz sorok", styles["SectionHeading"]))
        rows = [
            [
                header_cell("Szerviztípus"),
                header_cell("Cserélt alkatrész"),
                header_cell("Alkatrész ára"),
                header_cell("Fogyóanyag"),
                header_cell("Munkaóra"),
                header_cell("Megjegyzés"),
            ],
        ]
        for item in record.items.all():
            rows.append(
                [
                    cell(item.get_service_type_catalog_display()),
                    cell(item.replacement_part),
                    cell(item.part_price),
                    cell(item.get_consumable_display()),
                    cell(item.work_hours),
                    cell(item.note),
                ]
            )
        if len(rows) == 1:
            rows.append([cell("Nincsenek sor tételek"), cell("—"), cell("—"), cell("—"), cell("—"), cell("—")])

        table = Table(rows, repeatRows=1, colWidths=[24 * mm, 32 * mm, 24 * mm, 22 * mm, 20 * mm, 50 * mm])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F2937")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#9CA3AF")),
                    ("FONTNAME", (0, 0), (-1, 0), PDF_FONT_BOLD_NAME),
                    ("FONTNAME", (0, 1), (-1, -1), PDF_FONT_NAME),
                    ("FONTSIZE", (0, 0), (-1, -1), 8.8),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9FAFB")]),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        story.append(table)
        story.append(Spacer(1, 8))
        story.append(
            Paragraph(
                f"Teljes költség: {record.cost if record.cost is not None else '—'}",
                styles["InvoiceTotal"],
            )
        )
        story.append(Spacer(1, 12))

        story.append(Paragraph("Megjegyzések", styles["SectionHeading"]))
        story.append(Paragraph(record.notes if record.notes else "—", styles["Normal"]))

        doc.build(story)
        pdf = buffer.getvalue()
        buffer.close()

        filename = f"service_record_{record.pk}_{record.date:%Y%m%d}.pdf"
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response


class ServiceRecordCreateView(LoginRequiredMixin, VehicleContextMixin, FormConfigContextMixin, CreateView):
    model = ServiceRecord
    form_class = ServiceRecordForm
    template_name = "services/service_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["garage"] = get_active_garage(self.request)
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        garage = get_active_garage(self.request)
        overrides = get_label_overrides("service", garage)
        service_field_labels = SERVICE_FIELD_DEFAULT_LABELS.copy()
        service_field_labels.update({k: v for k, v in overrides.items() if v})
        context["service_field_labels"] = service_field_labels
        if self.request.POST:
            context["item_formset"] = ServiceRecordItemFormSet(
                self.request.POST,
                prefix="items",
                garage=garage,
            )
        else:
            context["item_formset"] = ServiceRecordItemFormSet(prefix="items", garage=garage)
        return context

    def form_valid(self, form):
        form.instance.vehicle = self.get_vehicle()
        context = self.get_context_data()
        item_formset = context["item_formset"]
        if not item_formset.is_valid():
            return self.render_to_response(self.get_context_data(form=form))
        messages.success(self.request, "Service record added.")
        self.object = form.save()
        item_formset.instance = self.object
        item_formset.save()
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))


class ServiceRecordUpdateView(LoginRequiredMixin, VehicleContextMixin, FormConfigContextMixin, UpdateView):
    model = ServiceRecord
    form_class = ServiceRecordForm
    template_name = "services/service_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["garage"] = get_active_garage(self.request)
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        garage = get_active_garage(self.request)
        overrides = get_label_overrides("service", garage)
        service_field_labels = SERVICE_FIELD_DEFAULT_LABELS.copy()
        service_field_labels.update({k: v for k, v in overrides.items() if v})
        context["service_field_labels"] = service_field_labels
        if self.request.POST:
            context["item_formset"] = ServiceRecordItemFormSet(
                self.request.POST,
                instance=self.object,
                prefix="items",
                garage=garage,
            )
        else:
            context["item_formset"] = ServiceRecordItemFormSet(
                instance=self.object,
                prefix="items",
                garage=garage,
            )
            if not self.object.items.exists() and (self.object.service_type or self.object.consumables):
                initial = {
                    "service_type": self.object.service_type,
                    "consumable": self.object.consumables,
                }
                if self.object.title:
                    initial["note"] = self.object.title
                context["item_formset"] = ServiceRecordItemFormSet(
                    instance=self.object,
                    prefix="items",
                    garage=garage,
                    queryset=ServiceRecordItem.objects.none(),
                    initial=[initial],
                )
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        item_formset = context["item_formset"]
        if not item_formset.is_valid():
            return self.render_to_response(self.get_context_data(form=form))
        messages.success(self.request, "Service record updated.")
        self.object = form.save()
        item_formset.instance = self.object
        item_formset.save()
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))


class ServiceRecordDeleteView(LoginRequiredMixin, VehicleContextMixin, DeleteView):
    model = ServiceRecord
    template_name = "services/service_confirm_delete.html"

    def get_success_url(self):
        return reverse_lazy("services:list", kwargs={"vehicle_pk": self.kwargs["vehicle_pk"]})

    def form_valid(self, form):
        messages.success(self.request, "Service record deleted.")
        return super().form_valid(form)
