import io
import os
from xml.sax.saxutils import escape

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView
from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from apps.core.mixins import FormConfigContextMixin, ModuleEnabledMixin, VehicleOwnerMixin
from apps.formconfig.utils import get_enabled_modules, get_label_overrides
from apps.garages.utils import get_active_garage
from apps.services.models import ServiceRecord, ServiceRecordItem

from .forms import QuoteForm, QuoteItemFormSet
from .models import Quote

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

QUOTE_FIELD_DEFAULT_LABELS = {
    "date": "Dátum",
    "title": "Cím",
    "total_estimate": "Becsült végösszeg",
    "notes": "Megjegyzés",
    "item_service_type": "Szerviztípus",
    "item_replacement_part": "Cserélt alkatrész",
    "item_part_price": "Alkatrész ára",
    "item_consumable": "Fogyóanyag",
    "item_work_hours": "Munkaóra",
    "item_note": "Megjegyzés",
}


class VehicleContextMixin(ModuleEnabledMixin, VehicleOwnerMixin):
    module_key = "quotes"

    def get_queryset(self):
        return Quote.objects.filter(vehicle=self.get_vehicle()).prefetch_related("items")


class QuoteListView(LoginRequiredMixin, VehicleContextMixin, ListView):
    model = Quote
    template_name = "quotes/quote_list.html"
    context_object_name = "quotes"

    def get_queryset(self):
        qs = super().get_queryset()
        query = (self.request.GET.get("q") or "").strip()
        if query:
            base_filter = (
                Q(title__icontains=query)
                | Q(notes__icontains=query)
                | Q(items__service_type__icontains=query)
                | Q(items__replacement_part__icontains=query)
                | Q(items__consumable__icontains=query)
                | Q(items__note__icontains=query)
            )
            qs = qs.filter(base_filter).distinct()
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_query"] = (self.request.GET.get("q") or "").strip()
        return context


class GlobalQuoteHistoryView(LoginRequiredMixin, ModuleEnabledMixin, ListView):
    module_key = "quotes"
    model = Quote
    template_name = "quotes/quote_history_all.html"
    context_object_name = "quotes"

    def get_queryset(self):
        garage = get_active_garage(self.request)
        qs = Quote.objects.select_related("vehicle", "converted_service").prefetch_related("items")
        if garage:
            qs = qs.filter(vehicle__garage=garage)
        else:
            qs = qs.filter(vehicle__owner=self.request.user)
        return qs.order_by("date", "created_at")


class QuoteDetailView(LoginRequiredMixin, VehicleContextMixin, DetailView):
    model = Quote
    template_name = "quotes/quote_detail.html"
    context_object_name = "quote"


class QuotePDFView(LoginRequiredMixin, VehicleContextMixin, DetailView):
    model = Quote

    def get(self, request, *args, **kwargs):
        quote = self.get_object()
        vehicle = self.get_vehicle()
        ensure_pdf_font()

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=18 * mm,
            leftMargin=18 * mm,
            topMargin=16 * mm,
            bottomMargin=16 * mm,
            title=f"Árajánlat {quote.pk}",
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
                name="QuoteTotal",
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
            return Paragraph(escape(text), styles["TableCell"])

        def header_cell(value):
            return Paragraph(escape(str(value)), styles["TableHeaderCell"])

        story.append(Paragraph("ÁRAJÁNLAT", styles["Title"]))
        story.append(Paragraph(f"Árajánlat #{quote.pk}", styles["Muted"]))
        story.append(Spacer(1, 10))

        details_rows = [
            ["Jármű", str(vehicle)],
            ["Dátum", f"{quote.date:%d %b %Y}"],
            ["Cím", quote.title or "—"],
        ]
        details_table = Table(details_rows, colWidths=[38 * mm, 134 * mm])
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

        story.append(Paragraph("Árajánlat sorok", styles["SectionHeading"]))
        rows = [[
            header_cell("Szerviztípus"),
            header_cell("Cserélt alkatrész"),
            header_cell("Alkatrész ára"),
            header_cell("Fogyóanyag"),
            header_cell("Munkaóra"),
            header_cell("Megjegyzés"),
        ]]
        for item in quote.items.all():
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
                f"Becsült végösszeg: {quote.total_estimate if quote.total_estimate is not None else '—'}",
                styles["QuoteTotal"],
            )
        )
        story.append(Spacer(1, 12))
        story.append(Paragraph("Megjegyzések", styles["SectionHeading"]))
        story.append(Paragraph(quote.notes if quote.notes else "—", styles["Normal"]))

        doc.build(story)
        pdf = buffer.getvalue()
        buffer.close()

        filename = f"quote_{quote.pk}_{quote.date:%Y%m%d}.pdf"
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response


class QuoteConvertToServiceView(LoginRequiredMixin, VehicleContextMixin, View):
    def post(self, request, *args, **kwargs):
        quote = get_object_or_404(self.get_queryset(), pk=kwargs["pk"])
        vehicle = self.get_vehicle()

        garage = get_active_garage(request)
        if "services" not in get_enabled_modules(garage):
            messages.error(request, "Service module is disabled, cannot convert quote.")
            return HttpResponseRedirect(quote.get_absolute_url())

        if quote.converted_service_id:
            messages.info(request, "Quote is already converted to a service record.")
            return HttpResponseRedirect(quote.converted_service.get_absolute_url())

        with transaction.atomic():
            service = ServiceRecord.objects.create(
                vehicle=vehicle,
                date=quote.date,
                title=quote.title,
                cost=quote.total_estimate,
                notes=quote.notes,
            )
            for item in quote.items.all():
                ServiceRecordItem.objects.create(
                    record=service,
                    service_type=item.service_type,
                    replacement_part=item.replacement_part,
                    part_price=item.part_price,
                    consumable=item.consumable,
                    note=item.note,
                    work_hours=item.work_hours,
                )
            quote.converted_service = service
            quote.save(update_fields=["converted_service"])

        messages.success(request, "Quote converted to service record.")
        return HttpResponseRedirect(service.get_absolute_url())


class QuoteCreateView(LoginRequiredMixin, VehicleContextMixin, FormConfigContextMixin, CreateView):
    model = Quote
    form_class = QuoteForm
    template_name = "quotes/quote_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["garage"] = get_active_garage(self.request)
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        garage = get_active_garage(self.request)
        overrides = get_label_overrides("quote", garage)
        quote_field_labels = QUOTE_FIELD_DEFAULT_LABELS.copy()
        quote_field_labels.update({k: v for k, v in overrides.items() if v})
        context["quote_field_labels"] = quote_field_labels
        if self.request.POST:
            context["item_formset"] = QuoteItemFormSet(self.request.POST, prefix="items", garage=garage)
        else:
            context["item_formset"] = QuoteItemFormSet(prefix="items", garage=garage)
        return context

    def form_valid(self, form):
        form.instance.vehicle = self.get_vehicle()
        context = self.get_context_data()
        item_formset = context["item_formset"]
        if not item_formset.is_valid():
            return self.render_to_response(self.get_context_data(form=form))
        self.object = form.save()
        item_formset.instance = self.object
        item_formset.save()
        messages.success(self.request, "Quote created.")
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))


class QuoteUpdateView(LoginRequiredMixin, VehicleContextMixin, FormConfigContextMixin, UpdateView):
    model = Quote
    form_class = QuoteForm
    template_name = "quotes/quote_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["garage"] = get_active_garage(self.request)
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        garage = get_active_garage(self.request)
        overrides = get_label_overrides("quote", garage)
        quote_field_labels = QUOTE_FIELD_DEFAULT_LABELS.copy()
        quote_field_labels.update({k: v for k, v in overrides.items() if v})
        context["quote_field_labels"] = quote_field_labels
        if self.request.POST:
            context["item_formset"] = QuoteItemFormSet(
                self.request.POST,
                instance=self.object,
                prefix="items",
                garage=garage,
            )
        else:
            context["item_formset"] = QuoteItemFormSet(instance=self.object, prefix="items", garage=garage)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        item_formset = context["item_formset"]
        if not item_formset.is_valid():
            return self.render_to_response(self.get_context_data(form=form))
        self.object = form.save()
        item_formset.instance = self.object
        item_formset.save()
        messages.success(self.request, "Quote updated.")
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))


class QuoteDeleteView(LoginRequiredMixin, VehicleContextMixin, DeleteView):
    model = Quote
    template_name = "quotes/quote_confirm_delete.html"

    def get_success_url(self):
        return reverse_lazy("quotes:list", kwargs={"vehicle_pk": self.kwargs["vehicle_pk"]})

    def form_valid(self, form):
        messages.success(self.request, "Quote deleted.")
        return super().form_valid(form)
