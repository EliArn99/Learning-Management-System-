
from django.contrib import admin
from django.urls import path, include
from dashboards.views import home
# from users.views import login_view
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path("", home, name="home"),
    path("admin/", admin.site.urls),
    path("courses/", include("courses.urls")),
    path("assignments/", include("assignments.urls")),
    path("dashboard/", include("dashboards.urls")),
    path("messages/", include("messaging.urls")),
    path("users/", include("users.urls")),
    path("quizz/", include("quizz.urls", namespace="quizz")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
