from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from .forms import PropertyForm
from .models import Property


def home(request):
    qs = Property.objects.filter(is_active=True).order_by("-created_at")

    q = request.GET.get("q", "").strip()
    district = request.GET.get("district", "").strip()
    land_type = request.GET.get("land_type", "").strip()
    min_price = request.GET.get("min_price", "").strip()
    max_price = request.GET.get("max_price", "").strip()

    if q:
        qs = qs.filter(
            Q(title__icontains=q)
            | Q(description__icontains=q)
            | Q(district__icontains=q)
            | Q(taluka__icontains=q)
            | Q(village__icontains=q)
        )
    if district:
        qs = qs.filter(district__icontains=district)
    if land_type:
        qs = qs.filter(land_type=land_type)
    if min_price.isdigit():
        qs = qs.filter(price_inr__gte=int(min_price))
    if max_price.isdigit():
        qs = qs.filter(price_inr__lte=int(max_price))

    context = {
        "properties": qs[:50],
        "filters": {"q": q, "district": district, "land_type": land_type, "min_price": min_price, "max_price": max_price},
        "land_types": Property.LAND_TYPES,
        "title": _("EstateAI - Properties"),
    }
    return render(request, "listings/property_list.html", context)


def property_detail(request, pk: int):
    prop = get_object_or_404(Property, pk=pk, is_active=True)
    return render(request, "listings/property_detail.html", {"property": prop})


@login_required
def property_create(request):
    if request.method == "POST":
        form = PropertyForm(request.POST)
        if form.is_valid():
            prop = form.save(commit=False)
            prop.owner = request.user
            prop.save()
            return redirect("property_detail", pk=prop.pk)
    else:
        form = PropertyForm()
    return render(request, "listings/property_form.html", {"form": form, "mode": "create"})


@login_required
def property_edit(request, pk: int):
    prop = get_object_or_404(Property, pk=pk, owner=request.user)
    if request.method == "POST":
        form = PropertyForm(request.POST, instance=prop)
        if form.is_valid():
            form.save()
            return redirect("property_detail", pk=prop.pk)
    else:
        form = PropertyForm(instance=prop)
    return render(request, "listings/property_form.html", {"form": form, "mode": "edit"})
