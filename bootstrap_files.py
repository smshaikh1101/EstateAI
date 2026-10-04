from pathlib import Path

BASE = Path(__file__).resolve().parent

def write(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.replace("\r\n", "\n"), encoding="utf-8")

# ----------------------
# Root files
# ----------------------
write(BASE / ".gitignore", """\
venv/
__pycache__/
*.pyc
.env
*.sqlite3
media/
staticfiles/
.pytest_cache/
.ruff_cache/
""")

write(BASE / ".env.example", """\
DJANGO_SECRET_KEY=replace-me
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
""")

write(BASE / "requirements.txt", """\
Django>=5.0,<6.0
django-environ>=0.11
pillow>=10.0
whitenoise>=6.0
django-widget-tweaks>=1.5
""")

write(BASE / "requirements-dev.txt", """\
-r requirements.txt
pytest>=8.0
pytest-django>=4.8
ruff>=0.6
black>=24.0
bandit>=1.7
pip-audit>=2.7
pre-commit>=3.7
detect-secrets>=1.5
""")

write(BASE / "pyproject.toml", """\
[tool.black]
line-length = 100

[tool.ruff]
line-length = 100
lint.select = ["E", "F", "I", "B", "UP"]
lint.ignore = ["E501"]
""")

write(BASE / "pytest.ini", """\
[pytest]
DJANGO_SETTINGS_MODULE = config.settings
python_files = tests.py test_*.py *_tests.py
""")

write(BASE / ".pre-commit-config.yaml", """\
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: end-of-file-fixer
      - id: trailing-whitespace

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.6.9
    hooks:
      - id: ruff
        args: [--fix]

  - repo: https://github.com/psf/black
    rev: 24.8.0
    hooks:
      - id: black

  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.5.0
    hooks:
      - id: detect-secrets
        args: ["--baseline", ".secrets.baseline"]
""")

# GitHub Actions CI
write(BASE / ".github" / "workflows" / "ci.yml", """\
name: CI

on: [push, pull_request]

jobs:
  test-and-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements-dev.txt

      - name: Format/Lint
        run: |
          ruff check .
          black --check .

      - name: Security scans
        run: |
          bandit -r . -x venv,migrations -ll
          pip-audit -r requirements.txt

      - name: Tests
        env:
          DJANGO_SECRET_KEY: testsecret
          DJANGO_DEBUG: "True"
          DJANGO_ALLOWED_HOSTS: "127.0.0.1,localhost"
        run: |
          pytest -q
""")

# ----------------------
# Django settings + urls
# ----------------------
write(BASE / "config" / "settings.py", """\
from pathlib import Path
import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DJANGO_DEBUG=(bool, False),
    DJANGO_ALLOWED_HOSTS=(list, []),
)

environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY", default="insecure-change-me")
DEBUG = env.bool("DJANGO_DEBUG", default=False)
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["127.0.0.1", "localhost"])

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",

    "widget_tweaks",

    "accounts",
    "listings",
    "verification.apps.VerificationConfig",
    "messaging",
    "tools",
    "aiassistant",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",

    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en"
LANGUAGES = [("en", "English"), ("hi", "Hindi"), ("mr", "Marathi")]
LOCALE_PATHS = [BASE_DIR / "locale"]

TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {"staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"}}

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_REDIRECT_URL = "home"
LOGOUT_REDIRECT_URL = "home"
LOGIN_URL = "login"
""")

write(BASE / "config" / "urls.py", """\
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.conf.urls.i18n import i18n_patterns

urlpatterns = [
    path("i18n/", include("django.conf.urls.i18n")),
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
""")

# ----------------------
# Accounts
# ----------------------
write(BASE / "accounts" / "forms.py", """\
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")
""")

write(BASE / "accounts" / "views.py", """\
from django.urls import reverse_lazy
from django.views.generic import CreateView
from .forms import SignUpForm


class SignUpView(CreateView):
    form_class = SignUpForm
    template_name = "registration/signup.html"
    success_url = reverse_lazy("login")
""")

write(BASE / "accounts" / "urls.py", """\
from django.urls import path
from .views import SignUpView

urlpatterns = [
    path("signup/", SignUpView.as_view(), name="signup"),
]
""")

# ----------------------
# Listings
# ----------------------
write(BASE / "listings" / "models.py", """\
from django.conf import settings
from django.db import models


class Property(models.Model):
    LAND_TYPES = [
        ("farm", "Farm Land"),
        ("residential", "Residential"),
        ("commercial", "Commercial"),
        ("industrial", "Industrial"),
        ("plot", "Plot"),
    ]

    AREA_UNITS = [
        ("sqft", "Sq Ft"),
        ("sq_m", "Sq Meter"),
        ("acre", "Acre"),
        ("hectare", "Hectare"),
        ("guntha", "Guntha"),
    ]

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="properties")

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    land_type = models.CharField(max_length=20, choices=LAND_TYPES)
    district = models.CharField(max_length=100)
    taluka = models.CharField(max_length=100, blank=True)
    village = models.CharField(max_length=100, blank=True)

    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    area_value = models.DecimalField(max_digits=12, decimal_places=2)
    area_unit = models.CharField(max_length=20, choices=AREA_UNITS, default="sqft")
    area_sq_m = models.FloatField(default=0.0)

    price_inr = models.IntegerField()
    contact_phone = models.CharField(max_length=20, blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        v = float(self.area_value)
        if self.area_unit == "sqft":
            self.area_sq_m = v * 0.092903
        elif self.area_unit == "sq_m":
            self.area_sq_m = v
        elif self.area_unit == "acre":
            self.area_sq_m = v * 4046.8564224
        elif self.area_unit == "hectare":
            self.area_sq_m = v * 10000.0
        elif self.area_unit == "guntha":
            self.area_sq_m = v * 101.17141056
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} ({self.district})"


class PropertyImage(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="property_images/")
    uploaded_at = models.DateTimeField(auto_now_add=True)
""")

write(BASE / "listings" / "forms.py", """\
from django.forms import ModelForm
from .models import Property


class PropertyForm(ModelForm):
    class Meta:
        model = Property
        fields = [
            "title",
            "description",
            "land_type",
            "district",
            "taluka",
            "village",
            "latitude",
            "longitude",
            "area_value",
            "area_unit",
            "price_inr",
            "contact_phone",
            "is_active",
        ]
""")

write(BASE / "listings" / "views.py", """\
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
""")

write(BASE / "listings" / "urls.py", """\
from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("properties/new/", views.property_create, name="property_create"),
    path("properties/<int:pk>/", views.property_detail, name="property_detail"),
    path("properties/<int:pk>/edit/", views.property_edit, name="property_edit"),
]
""")

write(BASE / "listings" / "admin.py", """\
from django.contrib import admin
from .models import Property, PropertyImage

admin.site.register(Property)
admin.site.register(PropertyImage)
""")

# ----------------------
# Verification (trust score + docs)
# ----------------------
write(BASE / "verification" / "apps.py", """\
from django.apps import AppConfig


class VerificationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "verification"

    def ready(self):
        from . import signals  # noqa
""")

write(BASE / "verification" / "models.py", """\
from django.conf import settings
from django.db import models


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, blank=True)
    phone_verified = models.BooleanField(default=False)

    def trust_score(self) -> int:
        score = 0
        if self.user.email:
            score += 10
        if self.phone:
            score += 10
        if self.phone_verified:
            score += 20
        approved_docs = self.documents.filter(status="approved").count()
        score += min(60, approved_docs * 30)
        return min(100, score)

    def __str__(self):
        return f"Profile({self.user.username})"


class VerificationDocument(models.Model):
    DOC_TYPES = [
        ("id", "ID Proof"),
        ("land", "Land Document (7/12, Property Card etc.)"),
        ("other", "Other"),
    ]
    STATUS = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="verification_docs")
    doc_type = models.CharField(max_length=20, choices=DOC_TYPES)
    file = models.FileField(upload_to="verification_docs/")
    status = models.CharField(max_length=20, choices=STATUS, default="pending")
    note = models.CharField(max_length=200, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"{self.user.username}:{self.doc_type}:{self.status}"
""")

write(BASE / "verification" / "signals.py", """\
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Profile


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
""")

write(BASE / "verification" / "forms.py", """\
from django import forms
from .models import VerificationDocument


class UploadDocForm(forms.ModelForm):
    class Meta:
        model = VerificationDocument
        fields = ["doc_type", "file"]
""")

write(BASE / "verification" / "views.py", """\
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .forms import UploadDocForm
from .models import Profile, VerificationDocument


@login_required
def dashboard(request):
    profile = Profile.objects.get(user=request.user)
    docs = VerificationDocument.objects.filter(user=request.user)
    return render(request, "verification/dashboard.html", {"profile": profile, "docs": docs})


@login_required
def upload_doc(request):
    if request.method == "POST":
        form = UploadDocForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.user = request.user
            doc.save()
            return redirect("verify_dashboard")
    else:
        form = UploadDocForm()
    return render(request, "verification/upload.html", {"form": form})
""")

write(BASE / "verification" / "urls.py", """\
from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="verify_dashboard"),
    path("upload/", views.upload_doc, name="verify_upload"),
]
""")

write(BASE / "verification" / "admin.py", """\
from django.contrib import admin
from .models import Profile, VerificationDocument

admin.site.register(Profile)
admin.site.register(VerificationDocument)
""")

# ----------------------
# Messaging
# ----------------------
write(BASE / "messaging" / "models.py", """\
from django.conf import settings
from django.db import models
from listings.models import Property


class Thread(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="buy_threads")
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sell_threads")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["property", "buyer", "seller"], name="unique_thread")
        ]

    def __str__(self):
        return f"Thread({self.property_id}) {self.buyer}->{self.seller}"


class Message(models.Model):
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
""")

write(BASE / "messaging" / "forms.py", """\
from django import forms


class MessageForm(forms.Form):
    body = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}))
""")

write(BASE / "messaging" / "views.py", """\
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from listings.models import Property
from .forms import MessageForm
from .models import Thread, Message


@login_required
def thread_list(request):
    threads = Thread.objects.filter(Q(buyer=request.user) | Q(seller=request.user)).order_by("-created_at")
    return render(request, "messaging/thread_list.html", {"threads": threads})


@login_required
def start_thread(request, property_id: int):
    prop = get_object_or_404(Property, pk=property_id, is_active=True)
    if prop.owner == request.user:
        return redirect("property_detail", pk=prop.pk)

    thread, _ = Thread.objects.get_or_create(property=prop, buyer=request.user, seller=prop.owner)
    return redirect("thread_detail", thread_id=thread.id)


@login_required
def thread_detail(request, thread_id: int):
    thread = get_object_or_404(Thread, id=thread_id)
    if request.user not in [thread.buyer, thread.seller]:
        return redirect("thread_list")

    if request.method == "POST":
        form = MessageForm(request.POST)
        if form.is_valid():
            Message.objects.create(thread=thread, sender=request.user, body=form.cleaned_data["body"])
            return redirect("thread_detail", thread_id=thread.id)
    else:
        form = MessageForm()

    return render(request, "messaging/thread_detail.html", {"thread": thread, "form": form})
""")

write(BASE / "messaging" / "urls.py", """\
from django.urls import path
from . import views

urlpatterns = [
    path("", views.thread_list, name="thread_list"),
    path("start/<int:property_id>/", views.start_thread, name="start_thread"),
    path("<int:thread_id>/", views.thread_detail, name="thread_detail"),
]
""")

write(BASE / "messaging" / "admin.py", """\
from django.contrib import admin
from .models import Thread, Message

admin.site.register(Thread)
admin.site.register(Message)
""")

# ----------------------
# Tools
# ----------------------
write(BASE / "tools" / "views.py", """\
from django.shortcuts import render


def index(request):
    return render(request, "tools/index.html")


def walk_area(request):
    return render(request, "tools/walk_area.html")
""")

write(BASE / "tools" / "urls.py", """\
from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="tools_index"),
    path("walk-area/", views.walk_area, name="tools_walk_area"),
]
""")

# ----------------------
# AI Assistant (placeholder)
# ----------------------
write(BASE / "aiassistant" / "views.py", """\
from django.shortcuts import render

FAQ = [
    ("How to verify seller?", "Upload documents and check approval status. Always meet safely and verify originals."),
    ("What is 7/12?", "In Maharashtra, 7/12 extract shows land details, ownership, and cultivation info."),
]


def chat(request):
    answer = None
    q = ""
    if request.method == "POST":
        q = (request.POST.get("q") or "").strip()
        answer = "I can help with property search, docs checklist, and basic pricing. Ask a specific question."
        for k, v in FAQ:
            if k.lower() in q.lower():
                answer = v
                break
    return render(request, "aiassistant/chat.html", {"q": q, "answer": answer})
""")

write(BASE / "aiassistant" / "urls.py", """\
from django.urls import path
from . import views

urlpatterns = [
    path("", views.chat, name="ai_chat"),
]
""")

# ----------------------
# Templates + static
# ----------------------
write(BASE / "templates" / "base.html", """\
{% load i18n %}
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>{% block title %}EstateAI{% endblock %}</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
  <link href="/static/app.css" rel="stylesheet">
</head>
<body class="container py-4">
  <nav class="d-flex gap-3 align-items-center mb-4">
    <a href="{% url 'home' %}">{% trans "Home" %}</a>
    <a href="{% url 'property_create' %}">{% trans "Post Property" %}</a>
    <a href="{% url 'thread_list' %}">{% trans "Inbox" %}</a>
    <a href="{% url 'verify_dashboard' %}">{% trans "Verification" %}</a>
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
""")

write(BASE / "templates" / "registration" / "login.html", """\
{% extends "base.html" %}
{% load i18n %}
{% block content %}
<h3>{% trans "Login" %}</h3>
<form method="post" class="card card-body">
  {% csrf_token %}
  {{ form.as_p }}
  <button class="btn btn-primary">{% trans "Login" %}</button>
</form>
{% endblock %}
""")

write(BASE / "templates" / "registration" / "signup.html", """\
{% extends "base.html" %}
{% load i18n %}
{% block content %}
<h3>{% trans "Signup" %}</h3>
<form method="post" class="card card-body">
  {% csrf_token %}
  {{ form.as_p }}
  <button class="btn btn-primary">{% trans "Create account" %}</button>
</form>
{% endblock %}
""")

write(BASE / "templates" / "listings" / "property_list.html", """\
{% extends "base.html" %}
{% load i18n humanize %}
{% block content %}
<h3>{% trans "Properties" %}</h3>

<form class="row g-2 mb-3" method="get">
  <div class="col-md-4">
    <input class="form-control" name="q" placeholder="{% trans 'Search' %}" value="{{ filters.q }}">
  </div>
  <div class="col-md-3">
    <input class="form-control" name="district" placeholder="{% trans 'District' %}" value="{{ filters.district }}">
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
      <div class="d-flex justify-content-between">
        <strong>{{ p.title }}</strong>
        <span>₹ {{ p.price_inr|intcomma }}</span>
      </div>
      <div class="text-muted">{{ p.district }} {% if p.taluka %} / {{ p.taluka }}{% endif %}</div>
    </a>
  {% empty %}
    <div class="text-muted">{% trans "No properties found." %}</div>
  {% endfor %}
</div>
{% endblock %}
""")

write(BASE / "templates" / "listings" / "property_detail.html", """\
{% extends "base.html" %}
{% load humanize i18n %}
{% block content %}
<h3>{{ property.title }}</h3>
<p class="text-muted">{{ property.district }}{% if property.taluka %} / {{ property.taluka }}{% endif %}{% if property.village %} / {{ property.village }}{% endif %}</p>

<p>{{ property.description|linebreaks }}</p>

<ul>
  <li>{% trans "Type" %}: {{ property.get_land_type_display }}</li>
  <li>{% trans "Area" %}: {{ property.area_value }} {{ property.get_area_unit_display }}</li>
  <li>{% trans "Price" %}: ₹ {{ property.price_inr|intcomma }}</li>
</ul>

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
""")

write(BASE / "templates" / "listings" / "property_form.html", """\
{% extends "base.html" %}
{% load i18n %}
{% block content %}
<h3>{% if mode == "create" %}{% trans "Post Property" %}{% else %}{% trans "Edit Property" %}{% endif %}</h3>

<form method="post" class="card card-body">
  {% csrf_token %}
  {{ form.as_p }}
  <button class="btn btn-primary">{% trans "Save" %}</button>
</form>
{% endblock %}
""")

write(BASE / "templates" / "verification" / "dashboard.html", """\
{% extends "base.html" %}
{% load i18n %}
{% block content %}
<h3>{% trans "Verification" %}</h3>

<p>{% trans "Trust score" %}: <strong>{{ profile.trust_score }}</strong> / 100</p>

<a class="btn btn-primary mb-3" href="{% url 'verify_upload' %}">{% trans "Upload document" %}</a>

<ul class="list-group">
  {% for d in docs %}
    <li class="list-group-item d-flex justify-content-between">
      <span>{{ d.get_doc_type_display }}</span>
      <span>{{ d.get_status_display }}</span>
    </li>
  {% empty %}
    <li class="list-group-item text-muted">{% trans "No documents uploaded yet." %}</li>
  {% endfor %}
</ul>
{% endblock %}
""")

write(BASE / "templates" / "verification" / "upload.html", """\
{% extends "base.html" %}
{% load i18n %}
{% block content %}
<h3>{% trans "Upload document" %}</h3>
<form method="post" enctype="multipart/form-data" class="card card-body">
  {% csrf_token %}
  {{ form.as_p }}
  <button class="btn btn-primary">{% trans "Upload" %}</button>
</form>
{% endblock %}
""")

write(BASE / "templates" / "messaging" / "thread_list.html", """\
{% extends "base.html" %}
{% load i18n %}
{% block content %}
<h3>{% trans "Inbox" %}</h3>

<ul class="list-group">
  {% for t in threads %}
    <a class="list-group-item list-group-item-action" href="{% url 'thread_detail' t.id %}">
      {{ t.property.title }}
    </a>
  {% empty %}
    <li class="list-group-item text-muted">{% trans "No conversations yet." %}</li>
  {% endfor %}
</ul>
{% endblock %}
""")

write(BASE / "templates" / "messaging" / "thread_detail.html", """\
{% extends "base.html" %}
{% load i18n %}
{% block content %}
<h3>{% trans "Chat" %}: {{ thread.property.title }}</h3>

<div class="card card-body mb-3" style="max-height: 300px; overflow:auto;">
  {% for m in thread.messages.all %}
    <div class="mb-2">
      <strong>{{ m.sender.username }}</strong>: {{ m.body }}
      <div class="text-muted" style="font-size: 12px;">{{ m.created_at }}</div>
    </div>
  {% endfor %}
</div>

<form method="post" class="card card-body">
  {% csrf_token %}
  {{ form.as_p }}
  <button class="btn btn-primary">{% trans "Send" %}</button>
</form>
{% endblock %}
""")

write(BASE / "templates" / "tools" / "index.html", """\
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

<a class="btn btn-outline-primary" href="{% url 'tools_walk_area' %}">{% trans "Walk boundary (GPS)" %}</a>
{% endblock %}
""")

write(BASE / "templates" / "tools" / "walk_area.html", """\
{% extends "base.html" %}
{% load i18n %}
{% block content %}
<h3>{% trans "Walk boundary (GPS)" %}</h3>
<p class="text-muted">{% trans "Open this page on your phone browser. Accuracy depends on GPS." %}</p>

<div class="d-flex gap-2 mb-3">
  <button class="btn btn-primary" onclick="startTrack()">{% trans "Start" %}</button>
  <button class="btn btn-secondary" onclick="stopTrack()">{% trans "Stop" %}</button>
  <button class="btn btn-outline-danger" onclick="resetTrack()">{% trans "Reset" %}</button>
</div>

<div class="card card-body">
  <div>{% trans "Points" %}: <span id="count">0</span></div>
  <div>{% trans "Estimated area" %}: <strong id="area">0</strong> m²</div>
  <pre id="log" style="white-space: pre-wrap;"></pre>
</div>

<script src="/static/walk_area.js"></script>
{% endblock %}
""")

write(BASE / "templates" / "aiassistant" / "chat.html", """\
{% extends "base.html" %}
{% load i18n %}
{% block content %}
<h3>{% trans "AI Help (MVP)" %}</h3>

<form method="post" class="card card-body mb-3">
  {% csrf_token %}
  <input class="form-control mb-2" name="q" placeholder="{% trans 'Ask something...' %}">
  <button class="btn btn-primary">{% trans "Ask" %}</button>
</form>

{% if answer %}
  <div class="alert alert-info">{{ answer }}</div>
{% endif %}
{% endblock %}
""")

write(BASE / "static" / "app.css", """\
body { max-width: 980px; }
""")

write(BASE / "static" / "walk_area.js", """\
let watchId = null;
let points = [];

function toMeters(lat, lon, refLat, refLon) {
  const R = 6371000;
  const x = (lon - refLon) * Math.cos((lat + refLat) * 0.5 * Math.PI / 180) * Math.PI/180 * R;
  const y = (lat - refLat) * Math.PI/180 * R;
  return [x, y];
}

function polygonAreaMeters2(pointsLatLon) {
  if (pointsLatLon.length < 3) return 0;
  const ref = pointsLatLon[0];
  const xy = pointsLatLon.map(p => toMeters(p.lat, p.lon, ref.lat, ref.lon));
  let sum = 0;
  for (let i = 0; i < xy.length; i++) {
    const [x1, y1] = xy[i];
    const [x2, y2] = xy[(i + 1) % xy.length];
    sum += (x1 * y2 - x2 * y1);
  }
  return Math.abs(sum) / 2;
}

function render() {
  document.getElementById("count").innerText = points.length;
  const area = polygonAreaMeters2(points);
  document.getElementById("area").innerText = area.toFixed(2);
  document.getElementById("log").innerText = JSON.stringify(points, null, 2);
}

function startTrack() {
  if (!navigator.geolocation) {
    alert("Geolocation not supported");
    return;
  }
  if (watchId !== null) return;

  watchId = navigator.geolocation.watchPosition(
    (pos) => {
      points.push({ lat: pos.coords.latitude, lon: pos.coords.longitude, t: Date.now() });
      render();
    },
    (err) => alert(err.message),
    { enableHighAccuracy: true, maximumAge: 0, timeout: 10000 }
  );
}

function stopTrack() {
  if (watchId !== null) {
    navigator.geolocation.clearWatch(watchId);
    watchId = null;
  }
}

function resetTrack() {
  stopTrack();
  points = [];
  render();
}

render();
""")

# tools urls/views created, but we must create tools/urls.py already above; done.
# Now write tools/urls.py and aiassistant/urls.py created; done.

print("Bootstrap files written successfully.")