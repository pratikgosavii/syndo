import django_filters
from django import forms
from django_filters.widgets import RangeWidget

from .models import (
    event,
    product_category,
    product_subcategory,
    MainCategory,
    size,
    Pincode,
    State,
    home_banner,
    testimonials,
    customer_address,
    expense_category,
)
from vendor.models import NotificationCampaign


DATE_RANGE_WIDGET = RangeWidget(attrs={"type": "date"})


class StyledFilterSet(django_filters.FilterSet):
    """
    Adds bootstrap friendly styling to every generated filter widget so we
    can drop the filter form straight into the table header.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.form.fields.values():
            self._apply_widget_styles(field.widget)

    def _apply_widget_styles(self, widget):
        if hasattr(widget, "widgets"):
            for nested in widget.widgets:
                self._apply_widget_styles(nested)
            return

        existing = widget.attrs.get("class", "")
        if isinstance(widget, forms.CheckboxInput):
            widget.attrs["class"] = f"{existing} form-check-input".strip()
        elif isinstance(widget, forms.Select):
            widget.attrs["class"] = f"{existing} form-select form-select-sm".strip()
        else:
            widget.attrs["class"] = f"{existing} form-control form-control-sm".strip()
        widget.attrs.setdefault("placeholder", widget.attrs.get("placeholder", widget.attrs.get("aria-label", "")))


class EventFilter(StyledFilterSet):
    name = django_filters.CharFilter(lookup_expr="icontains")
    description = django_filters.CharFilter(lookup_expr="icontains")
    start_date = django_filters.DateFromToRangeFilter(widget=DATE_RANGE_WIDGET, label="Start date")
    date_created = django_filters.DateFromToRangeFilter(widget=DATE_RANGE_WIDGET, label="Created date")

    class Meta:
        model = event
        fields = ["name", "description", "start_date", "date_created"]


class StateFilter(StyledFilterSet):
    name = django_filters.CharFilter(lookup_expr="icontains")
    code = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = State
        fields = ["name", "code"]


class NotificationCampaignFilter(StyledFilterSet):
    campaign_name = django_filters.CharFilter(lookup_expr="icontains", label="Campaign name")
    description = django_filters.CharFilter(lookup_expr="icontains")
    status = django_filters.ChoiceFilter(choices=NotificationCampaign.STATUS_CHOICES)
    redirect_to = django_filters.ChoiceFilter(choices=NotificationCampaign._meta.get_field("redirect_to").choices)
    created_at = django_filters.DateFromToRangeFilter(widget=DATE_RANGE_WIDGET, label="Created date")

    class Meta:
        model = NotificationCampaign
        fields = ["campaign_name", "description", "status", "redirect_to", "created_at"]


class TestimonialFilter(StyledFilterSet):
    name = django_filters.CharFilter(lookup_expr="icontains")
    rating = django_filters.RangeFilter(label="Rating range")

    class Meta:
        model = testimonials
        fields = ["name", "rating"]


class PincodeFilter(StyledFilterSet):
    code = django_filters.CharFilter(lookup_expr="icontains", label="Pincode")
    city = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = Pincode
        fields = ["code", "city"]


class MainCategoryFilter(StyledFilterSet):
    name = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = MainCategory
        fields = ["name"]


class ProductCategoryFilter(StyledFilterSet):
    name = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = product_category
        fields = ["name"]


class ProductSubCategoryFilter(StyledFilterSet):
    category = django_filters.ModelChoiceFilter(queryset=product_category.objects.all().order_by("name"))
    name = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = product_subcategory
        fields = ["category", "name"]


class ExpenseCategoryFilter(StyledFilterSet):
    name = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = expense_category
        fields = ["name"]


class SizeFilter(StyledFilterSet):
    name = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = size
        fields = ["name"]


class CustomerAddressFilter(StyledFilterSet):
    name = django_filters.CharFilter(lookup_expr="icontains")
    type = django_filters.CharFilter(lookup_expr="icontains")
    address = django_filters.CharFilter(lookup_expr="icontains")
    pin_code = django_filters.CharFilter(lookup_expr="icontains", label="Pin code")
    city = django_filters.CharFilter(lookup_expr="icontains")
    state = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = customer_address
        fields = ["name", "type", "address", "pin_code", "city", "state"]


class HomeBannerFilter(StyledFilterSet):
    title = django_filters.CharFilter(lookup_expr="icontains")
    description = django_filters.CharFilter(lookup_expr="icontains")
    is_active = django_filters.BooleanFilter()

    class Meta:
        model = home_banner
        fields = ["title", "description", "is_active"]
