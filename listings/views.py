from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import PropertyForm
from .locations import TALUKAS_BY_DISTRICT, DISTRICTS
from .models import Property, PropertyImage


def home(request):
    qs = (
        Property.objects.filter(is_active=True)
        .select_related("owner", "owner__profile")
        .prefetch_related("images")
        .order_by("-created_at")
    )

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

    return render(
        request,
        "listings/property_list.html",
        {
            "properties": qs[:50],
            "filters": {"q": q, "district": district, "land_type": land_type, "min_price": min_price, "max_price": max_price},
            "land_types": Property.LAND_TYPES,
            "districts": DISTRICTS,
        },
    )


def property_detail(request, pk: int):
    prop = (
        Property.objects.select_related("owner", "owner__profile")
        .prefetch_related("images")
        .get(pk=pk, is_active=True)
    )
    return render(request, "listings/property_detail.html", {"property": prop})


@login_required
def my_listings(request):
    qs = Property.objects.filter(owner=request.user).prefetch_related("images").order_by("-created_at")
    return render(request, "listings/my_listings.html", {"properties": qs})


@login_required
def property_create(request):
    if request.method == "POST":
        form = PropertyForm(request.POST, request.FILES)
        if form.is_valid():
            prop = form.save(commit=False)
            prop.owner = request.user
            prop.save()

            for f in request.FILES.getlist("images"):
                PropertyImage.objects.create(property=prop, image=f)

            return redirect("property_detail", pk=prop.pk)
    else:
        form = PropertyForm()
    return render(request, "listings/property_form.html", {"form": form, "mode": "create"})


@login_required
def property_edit(request, pk: int):
    prop = get_object_or_404(Property, pk=pk, owner=request.user)
    if request.method == "POST":
        form = PropertyForm(request.POST, request.FILES, instance=prop)
        if form.is_valid():
            prop = form.save()

            for f in request.FILES.getlist("images"):
                PropertyImage.objects.create(property=prop, image=f)

            return redirect("property_detail", pk=prop.pk)
    else:
        form = PropertyForm(instance=prop)

    return render(request, "listings/property_form.html", {"form": form, "mode": "edit", "property": prop})


def talukas_api(request):
    district = (request.GET.get("district") or "").strip()
    talukas = TALUKAS_BY_DISTRICT.get(district, [])
    return JsonResponse({"district": district, "talukas": talukas})


def properties_geo_api(request):
    qs = Property.objects.filter(is_active=True, latitude__isnull=False, longitude__isnull=False).order_by("-created_at")[:300]
    data = []
    for p in qs:
        data.append(
            {"id": p.id, "title": p.title, "district": p.district, "taluka": p.taluka, "price_inr": p.price_inr, "lat": float(p.latitude), "lon": float(p.longitude)}
        )
    return JsonResponse({"properties": data})


def nearby_page(request):
    return render(request, "listings/nearby.html")
