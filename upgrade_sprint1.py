from pathlib import Path

BASE = Path(__file__).resolve().parent


def write(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.replace("\r\n", "\n"), encoding="utf-8")


# -----------------------
# config/urls.py (Fix APIs to be NON-language-prefixed)
# -----------------------
write(
    BASE / "config" / "urls.py",
    """\
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.conf.urls.i18n import i18n_patterns

from listings import views as listing_views

urlpatterns = [
    path("i18n/", include("django.conf.urls.i18n")),

    # APIs without language prefix (so JS can call /api/.. safely)
    path("api/talukas/", listing_views.talukas_api, name="talukas_api"),
    path("api/properties-geo/", listing_views.properties_geo_api, name="properties_geo_api"),
]

urlpatterns += i18n_patterns(
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("accounts/", include("accounts.urls")),
    path("", include("listings.urls")),
    path("verify/", include("verification.urls")),
    path("inbox/", include("messaging.urls")),
    path("tools/", include("tools.urls")),
    path("ai/", include("aiassistant.urls")),
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
""",
)

# -----------------------
# verification/signals.py (Ensure profile exists for old users too)
# -----------------------
write(
    BASE / "verification" / "signals.py",
    """\
from django.contrib.auth.models import User
from django.db.models.signals import post_save, post_migrate
from django.dispatch import receiver
from .models import Profile


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)


@receiver(post_migrate)
def ensure_profiles(sender, **kwargs):
    # sender is an AppConfig
    try:
        if getattr(sender, "name", "") != "verification":
            return
    except Exception:
        return

    for u in User.objects.all():
        Profile.objects.get_or_create(user=u)
""",
)

# -----------------------
# listings/locations.py (starter Maharashtra dataset)
# -----------------------
write(
    BASE / "listings" / "locations.py",
    """\
DISTRICTS = [
    "Ahmednagar","Akola","Amravati","Aurangabad","Beed","Bhandara","Buldhana","Chandrapur",
    "Dhule","Gadchiroli","Gondia","Hingoli","Jalgaon","Jalna","Kolhapur","Latur",
    "Mumbai City","Mumbai Suburban","Nagpur","Nanded","Nandurbar","Nashik","Osmanabad",
    "Palghar","Parbhani","Pune","Raigad","Ratnagiri","Sangli","Satara","Sindhudurg",
    "Solapur","Thane","Wardha","Washim","Yavatmal",
]

# Starter Taluka dataset (expand later)
TALUKAS_BY_DISTRICT = {
    "Pune": ["Haveli","Mulshi","Maval","Shirur","Baramati","Daund","Purandar","Bhor","Velhe","Junnar","Khed","Indapur","Ambegaon"],
    "Nashik": ["Nashik","Igatpuri","Dindori","Niphad","Sinnar","Yeola","Malegaon","Baglan","Kalwan","Chandwad","Deola","Trimbakeshwar"],
    "Nagpur": ["Nagpur Urban","Nagpur Rural","Hingna","Kamptee","Ramtek","Umred","Katol","Narkhed","Saoner","Kalameshwar","Parseoni","Kuhi","Bhiwapur","Mauda"],
    "Thane": ["Thane","Kalyan","Bhiwandi","Ulhasnagar","Shahapur","Murbad","Ambernath"],
    "Mumbai Suburban": ["Andheri","Borivali","Kurla"],
    "Kolhapur": ["Karvir","Panhala","Hatkanangale","Shirol","Gadhinglaj","Kagal"],
    "Raigad": ["Alibag","Panvel","Karjat","Khalapur","Mahad","Mangaon","Murud","Pen","Roha","Shrivardhan","Tala","Uran"],
}
""",
)

# -----------------------
# listings/forms.py (district dropdown + taluka suggestions)
# -----------------------
write(
    BASE / "listings" / "forms.py",
    """\
from django import forms
from django.forms import ModelForm
from .models import Property
from .locations import DISTRICTS

DISTRICT_CHOICES = [("", "Select district")] + [(d, d) for d in DISTRICTS]


class PropertyForm(ModelForm):
    district = forms.CharField(widget=forms.Select(choices=DISTRICT_CHOICES))

    class Meta:
        model = Property
        fields = [
            "title","description","land_type",
            "district","taluka","village",
            "latitude","longitude",
            "area_value","area_unit",
            "price_inr","contact_phone",
            "is_active",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["taluka"].widget.attrs.update(
            {"list": "taluka-list", "autocomplete": "off", "placeholder": "Start typing taluka..."}
        )
""",
)

# -----------------------
# listings/views.py (images + my listings + APIs + nearby page)
# -----------------------
write(
    BASE / "listings" / "views.py",
    """\
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
""",
)

# -----------------------
# listings/urls.py
# -----------------------
write(
    BASE / "listings" / "urls.py",
    """\
from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("my/", views.my_listings, name="my_listings"),
    path("nearby/", views.nearby_page, name="nearby_page"),

    path("properties/new/", views.property_create, name="property_create"),
    path("properties/<int:pk>/", views.property_detail, name="property_detail"),
    path("properties/<int:pk>/edit/", views.property_edit, name="property_edit"),
]
""",
)

# -----------------------
# Templates
# -----------------------
write(
    BASE / "templates" / "base.html",
    """\
{% load i18n %}
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>{% block title %}EstateAI{% endblock %}</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
  <link href="/static/app.css" rel="stylesheet">
  {% block head %}{% endblock %}
</head>
<body class="container py-4">
  <nav class="d-flex flex-wrap gap-3 align-items-center mb-4">
    <a href="{% url 'home' %}">{% trans "Home" %}</a>
    <a href="{% url 'nearby_page' %}">{% trans "Near me" %}</a>

    {% if user.is_authenticated %}
      <a href="{% url 'my_listings' %}">{% trans "My Listings" %}</a>
      <a href="{% url 'property_create' %}">{% trans "Post Property" %}</a>
      <a href="{% url 'thread_list' %}">{% trans "Inbox" %}</a>
      <a href="{% url 'verify_dashboard' %}">{% trans "Verification" %}</a>
    {% endif %}

    <a href="{% url 'tools_index' %}">{% trans "Tools" %}</a>
    <a href="{% url 'ai_chat' %}">{% trans "AI Help" %}</a>

    <div class="ms-auto d-flex gap-2 align-items-center">
      <form action="{% url 'set_language' %}" method="post" class="m-0">
        {% csrf_token %}
        <input name="next" type="hidden" value="{{ request.path }}">
        <select name="language" onchange="this.form.submit()">
          <option value="en" {% if LANGUAGE_CODE == 'en' %}selected{% endif %}>EN</option>
          <option value="hi" {% if LANGUAGE_CODE == 'hi' %}selected{% endif %}>HI</option>
          <option value="mr" {% if LANGUAGE_CODE == 'mr' %}selected{% endif %}>MR</option>
        </select>
      </form>

      {% if user.is_authenticated %}
        <span class="text-muted">{{ user.username }}</span>
        <a href="{% url 'logout' %}">{% trans "Logout" %}</a>
      {% else %}
        <a href="{% url 'login' %}">{% trans "Login" %}</a>
        <a href="{% url 'signup' %}">{% trans "Signup" %}</a>
      {% endif %}
    </div>
  </nav>

  {% block content %}{% endblock %}
</body>
</html>
""",
)

write(
    BASE / "templates" / "listings" / "property_list.html",
    """\
{% extends "base.html" %}
{% load i18n humanize %}
{% block content %}
<h3>{% trans "Properties" %}</h3>

<form class="row g-2 mb-3" method="get">
  <div class="col-md-4">
    <input class="form-control" name="q" placeholder="{% trans 'Search' %}" value="{{ filters.q }}">
  </div>

  <div class="col-md-3">
    <select class="form-select" name="district">
      <option value="">{% trans "All districts" %}</option>
      {% for d in districts %}
        <option value="{{ d }}" {% if filters.district == d %}selected{% endif %}>{{ d }}</option>
      {% endfor %}
    </select>
  </div>

  <div class="col-md-3">
    <select class="form-select" name="land_type">
      <option value="">{% trans "All land types" %}</option>
      {% for v, label in land_types %}
        <option value="{{ v }}" {% if filters.land_type == v %}selected{% endif %}>{{ label }}</option>
      {% endfor %}
    </select>
  </div>

  <div class="col-md-1">
    <input class="form-control" name="min_price" placeholder="{% trans 'Min' %}" value="{{ filters.min_price }}">
  </div>
  <div class="col-md-1">
    <input class="form-control" name="max_price" placeholder="{% trans 'Max' %}" value="{{ filters.max_price }}">
  </div>

  <div class="col-12">
    <button class="btn btn-primary">{% trans "Filter" %}</button>
  </div>
</form>

<div class="list-group">
  {% for p in properties %}
    <a class="list-group-item list-group-item-action" href="{% url 'property_detail' p.pk %}">
      <div class="d-flex justify-content-between align-items-center">
        <div>
          <strong>{{ p.title }}</strong>
          <div class="text-muted">{{ p.district }}{% if p.taluka %} / {{ p.taluka }}{% endif %}</div>
        </div>
        <div class="text-end">
          <div>₹ {{ p.price_inr|intcomma }}</div>
          <span class="badge text-bg-success">Trust {{ p.owner.profile.trust_score }}/100</span>
        </div>
      </div>
    </a>
  {% empty %}
    <div class="text-muted">{% trans "No properties found." %}</div>
  {% endfor %}
</div>
{% endblock %}
""",
)

write(
    BASE / "templates" / "listings" / "property_form.html",
    """\
{% extends "base.html" %}
{% load i18n %}
{% block content %}
<h3>{% if mode == "create" %}{% trans "Post Property" %}{% else %}{% trans "Edit Property" %}{% endif %}</h3>

<form method="post" enctype="multipart/form-data" class="card card-body">
  {% csrf_token %}
  {{ form.as_p }}

  <label class="form-label">{% trans "Property images" %}</label>
  <input class="form-control mb-3" type="file" name="images" multiple accept="image/*">

  <datalist id="taluka-list"></datalist>

  {% if mode == "edit" and property %}
    <div class="mb-3">
      <div class="text-muted mb-2">{% trans "Existing images" %}</div>
      <div class="d-flex flex-wrap gap-2">
        {% for img in property.images.all %}
          <img src="{{ img.image.url }}" style="width:120px;height:90px;object-fit:cover;border:1px solid #ddd;">
        {% empty %}
          <span class="text-muted">{% trans "No images yet." %}</span>
        {% endfor %}
      </div>
    </div>
  {% endif %}

  <button class="btn btn-primary">{% trans "Save" %}</button>
</form>

<script src="/static/property_form.js"></script>
{% endblock %}
""",
)

write(
    BASE / "templates" / "listings" / "property_detail.html",
    """\
{% extends "base.html" %}
{% load humanize i18n %}

{% block head %}
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
{% endblock %}

{% block content %}
<h3>{{ property.title }}</h3>

<div class="d-flex flex-wrap gap-2 align-items-center mb-2">
  <span class="text-muted">
    {{ property.district }}{% if property.taluka %} / {{ property.taluka }}{% endif %}{% if property.village %} / {{ property.village }}{% endif %}
  </span>
  <span class="badge text-bg-success">Trust {{ property.owner.profile.trust_score }}/100</span>
  <span class="text-muted">{% trans "Seller" %}: {{ property.owner.username }}</span>
</div>

{% if property.images.all %}
  <div class="d-flex flex-wrap gap-2 mb-3">
    {% for img in property.images.all %}
      <img src="{{ img.image.url }}" style="width:260px;height:180px;object-fit:cover;border:1px solid #ddd;">
    {% endfor %}
  </div>
{% endif %}

<p>{{ property.description|linebreaks }}</p>

<ul>
  <li>{% trans "Type" %}: {{ property.get_land_type_display }}</li>
  <li>{% trans "Area" %}: {{ property.area_value }} {{ property.get_area_unit_display }}</li>
  <li>{% trans "Price" %}: ₹ {{ property.price_inr|intcomma }}</li>
</ul>

{% if property.latitude and property.longitude %}
  <div class="mb-3">
    <div class="text-muted mb-2">{% trans "Map" %}</div>
    <div id="map" style="height: 320px; border: 1px solid #ddd;"></div>
  </div>

  <script>
    const lat = {{ property.latitude }};
    const lon = {{ property.longitude }};
    const map = L.map('map').setView([lat, lon], 13);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19 }).addTo(map);
    L.marker([lat, lon]).addTo(map).bindPopup("{{ property.title|escapejs }}");
  </script>
{% endif %}

{% if user.is_authenticated %}
  {% if property.owner_id == user.id %}
    <a class="btn btn-outline-secondary" href="{% url 'property_edit' property.pk %}">{% trans "Edit" %}</a>
  {% else %}
    <a class="btn btn-primary" href="{% url 'start_thread' property.pk %}">{% trans "Message seller" %}</a>
  {% endif %}
{% else %}
  <a class="btn btn-primary" href="{% url 'login' %}">{% trans "Login to message seller" %}</a>
{% endif %}
{% endblock %}
""",
)

write(
    BASE / "templates" / "listings" / "my_listings.html",
    """\
{% extends "base.html" %}
{% load humanize i18n %}
{% block content %}
<h3>{% trans "My Listings" %}</h3>

<div class="list-group">
  {% for p in properties %}
    <div class="list-group-item">
      <div class="d-flex justify-content-between align-items-center">
        <div>
          <strong><a href="{% url 'property_detail' p.pk %}">{{ p.title }}</a></strong>
          <div class="text-muted">{{ p.district }}{% if p.taluka %} / {{ p.taluka }}{% endif %}</div>
        </div>
        <div class="text-end">
          <div>₹ {{ p.price_inr|intcomma }}</div>
          <a class="btn btn-sm btn-outline-secondary" href="{% url 'property_edit' p.pk %}">{% trans "Edit" %}</a>
        </div>
      </div>
    </div>
  {% empty %}
    <div class="text-muted">{% trans "No listings yet." %}</div>
  {% endfor %}
</div>
{% endblock %}
""",
)

write(
    BASE / "templates" / "listings" / "nearby.html",
    """\
{% extends "base.html" %}
{% load i18n %}
{% block content %}
<h3>{% trans "Properties Near Me" %}</h3>
<p class="text-muted">{% trans "Allow location permission in your browser to see distance-sorted properties." %}</p>

<div class="d-flex gap-2 mb-3">
  <button class="btn btn-primary" onclick="loadNearby()">{% trans "Find nearby" %}</button>
</div>

<div id="status" class="text-muted mb-2"></div>
<div id="results" class="list-group"></div>

<script src="/static/nearby.js"></script>
{% endblock %}
""",
)

# -----------------------
# Static JS
# -----------------------
write(
    BASE / "static" / "property_form.js",
    """\
async function refreshTalukas() {
  const districtEl = document.getElementById("id_district");
  const talukaList = document.getElementById("taluka-list");
  if (!districtEl || !talukaList) return;

  const district = districtEl.value || "";
  talukaList.innerHTML = "";
  if (!district) return;

  try {
    const resp = await fetch(`/api/talukas/?district=${encodeURIComponent(district)}`);
    const data = await resp.json();
    (data.talukas || []).forEach(t => {
      const opt = document.createElement("option");
      opt.value = t;
      talukaList.appendChild(opt);
    });
  } catch (e) {}
}

document.addEventListener("DOMContentLoaded", () => {
  const districtEl = document.getElementById("id_district");
  if (districtEl) {
    districtEl.addEventListener("change", refreshTalukas);
    refreshTalukas();
  }
});
""",
)

write(
    BASE / "static" / "nearby.js",
    """\
function haversineKm(lat1, lon1, lat2, lon2) {
  const R = 6371;
  const dLat = (lat2-lat1) * Math.PI / 180;
  const dLon = (lon2-lon1) * Math.PI / 180;
  const a =
    Math.sin(dLat/2) * Math.sin(dLat/2) +
    Math.cos(lat1 * Math.PI/180) * Math.cos(lat2 * Math.PI/180) *
    Math.sin(dLon/2) * Math.sin(dLon/2);
  return 2 * R * Math.asin(Math.sqrt(a));
}

function langPrefix() {
  const parts = window.location.pathname.split("/").filter(Boolean);
  const maybeLang = parts[0] || "";
  if (maybeLang.length === 2) return "/" + maybeLang;
  return "";
}

async function loadNearby() {
  const status = document.getElementById("status");
  const results = document.getElementById("results");
  results.innerHTML = "";
  status.innerText = "Requesting your location...";

  if (!navigator.geolocation) {
    status.innerText = "Geolocation not supported.";
    return;
  }

  navigator.geolocation.getCurrentPosition(async (pos) => {
    const myLat = pos.coords.latitude;
    const myLon = pos.coords.longitude;

    status.innerText = "Loading properties...";
    const resp = await fetch("/api/properties-geo/");
    const data = await resp.json();
    const props = data.properties || [];

    const withDistance = props.map(p => ({
      ...p,
      distance_km: haversineKm(myLat, myLon, p.lat, p.lon)
    })).sort((a,b) => a.distance_km - b.distance_km);

    status.innerText = `Found ${withDistance.length} properties with location.`;

    const prefix = langPrefix();
    withDistance.slice(0, 50).forEach(p => {
      const a = document.createElement("a");
      a.className = "list-group-item list-group-item-action";
      a.href = `${prefix}/properties/${p.id}/`;
      a.innerHTML = `
        <div class="d-flex justify-content-between">
          <strong>${p.title}</strong>
          <span>${p.distance_km.toFixed(2)} km</span>
        </div>
        <div class="text-muted">${p.district}${p.taluka ? " / " + p.taluka : ""} — ₹ ${p.price_inr}</div>
      `;
      results.appendChild(a);
    });

  }, (err) => {
    status.innerText = err.message;
  }, { enableHighAccuracy: true, timeout: 10000 });
}
""",
)

# -----------------------
# Tools: valuation calculator
# -----------------------
write(
    BASE / "tools" / "views.py",
    """\
from django.shortcuts import render


def index(request):
    return render(request, "tools/index.html")


def walk_area(request):
    return render(request, "tools/walk_area.html")


def valuation(request):
    result = None
    area_value = request.GET.get("area_value", "").strip()
    area_unit = request.GET.get("area_unit", "sq_m").strip()
    rate = request.GET.get("rate_inr_per_sq_m", "").strip()

    unit_to_sq_m = {"sqft": 0.092903, "sq_m": 1.0, "acre": 4046.8564224, "hectare": 10000.0, "guntha": 101.17141056}

    try:
        if area_value and rate:
            a = float(area_value)
            r = float(rate)
            area_sq_m = a * unit_to_sq_m.get(area_unit, 1.0)
            est = area_sq_m * r
            result = {"area_sq_m": area_sq_m, "estimate_inr": est}
    except ValueError:
        result = {"error": "Please enter valid numbers."}

    return render(request, "tools/valuation.html", {"result": result, "area_value": area_value, "area_unit": area_unit, "rate": rate})
""",
)

write(
    BASE / "tools" / "urls.py",
    """\
from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="tools_index"),
    path("walk-area/", views.walk_area, name="tools_walk_area"),
    path("valuation/", views.valuation, name="tools_valuation"),
]
""",
)

write(
    BASE / "templates" / "tools" / "index.html",
    """\
{% extends "base.html" %}
{% load i18n %}
{% block content %}
<h3>{% trans "Tools" %}</h3>

<div class="card card-body mb-3">
  <h5>{% trans "Area conversion (quick)" %}</h5>
  <ul>
    <li>1 guntha = 101.1714 sq m</li>
    <li>1 acre = 4046.8564 sq m</li>
    <li>1 sq ft = 0.092903 sq m</li>
  </ul>
</div>

<div class="d-flex gap-2">
  <a class="btn btn-outline-primary" href="{% url 'tools_walk_area' %}">{% trans "Walk boundary (GPS)" %}</a>
  <a class="btn btn-outline-secondary" href="{% url 'tools_valuation' %}">{% trans "Valuation calculator" %}</a>
</div>
{% endblock %}
""",
)

write(
    BASE / "templates" / "tools" / "valuation.html",
    """\
{% extends "base.html" %}
{% load i18n humanize %}
{% block content %}
<h3>{% trans "Valuation Calculator" %}</h3>

<form class="row g-2 mb-3" method="get">
  <div class="col-md-3">
    <label class="form-label">{% trans "Area value" %}</label>
    <input class="form-control" name="area_value" value="{{ area_value }}" placeholder="e.g. 10">
  </div>
  <div class="col-md-3">
    <label class="form-label">{% trans "Area unit" %}</label>
    <select class="form-select" name="area_unit">
      <option value="sq_m" {% if area_unit == "sq_m" %}selected{% endif %}>Sq Meter</option>
      <option value="sqft" {% if area_unit == "sqft" %}selected{% endif %}>Sq Ft</option>
      <option value="guntha" {% if area_unit == "guntha" %}selected{% endif %}>Guntha</option>
      <option value="acre" {% if area_unit == "acre" %}selected{% endif %}>Acre</option>
      <option value="hectare" {% if area_unit == "hectare" %}selected{% endif %}>Hectare</option>
    </select>
  </div>
  <div class="col-md-4">
    <label class="form-label">{% trans "Rate (INR per sq meter)" %}</label>
    <input class="form-control" name="rate_inr_per_sq_m" value="{{ rate }}" placeholder="e.g. 15000">
  </div>
  <div class="col-md-2 d-flex align-items-end">
    <button class="btn btn-primary w-100">{% trans "Calculate" %}</button>
  </div>
</form>

{% if result %}
  {% if result.error %}
    <div class="alert alert-danger">{{ result.error }}</div>
  {% else %}
    <div class="alert alert-info">
      <div>{% trans "Converted area" %}: <strong>{{ result.area_sq_m|floatformat:2 }}</strong> m²</div>
      <div>{% trans "Estimated valuation" %}: <strong>₹ {{ result.estimate_inr|floatformat:0|intcomma }}</strong></div>
    </div>
  {% endif %}
{% endif %}
{% endblock %}
""",
)

# -----------------------
# Tests: update to use reverse (works with i18n patterns)
# -----------------------
write(
    BASE / "listings" / "tests.py",
    """\
import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import translation
from listings.models import Property


@pytest.mark.django_db
def test_home_page(client):
    with translation.override("en"):
        resp = client.get(reverse("home"))
    assert resp.status_code == 200


@pytest.mark.django_db
def test_create_property_requires_login(client):
    with translation.override("en"):
        resp = client.get(reverse("property_create"))
    assert resp.status_code == 302


@pytest.mark.django_db
def test_logged_in_can_create_property(client):
    u = User.objects.create_user(username="seller1", password="pass12345")
    client.login(username="seller1", password="pass12345")

    with translation.override("en"):
        url = reverse("property_create")

    resp = client.post(
        url,
        data={
            "title": "Test Plot",
            "description": "Nice plot",
            "land_type": "plot",
            "district": "Pune",
            "taluka": "Haveli",
            "village": "TestVillage",
            "latitude": "18.5204",
            "longitude": "73.8567",
            "area_value": "10",
            "area_unit": "guntha",
            "price_inr": "1000000",
            "contact_phone": "9999999999",
            "is_active": "on",
        },
        follow=True,
    )
    assert resp.status_code == 200
    assert Property.objects.filter(title="Test Plot").exists()
""",
)

print("Sprint-1 upgrade files written successfully.")