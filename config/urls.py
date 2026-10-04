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
