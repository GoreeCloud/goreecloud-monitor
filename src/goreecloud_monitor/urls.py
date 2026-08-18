from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

handler400 = "monitoring.error_views.bad_request"
handler403 = "monitoring.error_views.permission_denied"
handler404 = "monitoring.error_views.page_not_found"
handler500 = "monitoring.error_views.server_error"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("", include("monitoring.urls")),
]
