from django.urls import path

from . import views

app_name = "monitoring"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("monitors/", views.MonitorListView.as_view(), name="monitor-list"),
    path("monitors/new/", views.MonitorCreateView.as_view(), name="monitor-create"),
    path("monitors/<int:pk>/", views.monitor_detail, name="monitor-detail"),
    path("monitors/<int:pk>/job-recovery/", views.job_recovery, name="job-recovery"),
    path("monitors/<int:pk>/job-history/export/", views.job_history_export, name="job-history-export"),
    path("monitors/<int:pk>/edit/", views.MonitorUpdateView.as_view(), name="monitor-update"),
    path("monitors/<int:pk>/delete/", views.MonitorDeleteView.as_view(), name="monitor-delete"),
    path("monitors/<int:pk>/rotate-token/", views.rotate_heartbeat_token, name="monitor-rotate-token"),
    path("incidents/", views.incident_list, name="incident-list"),
    path("maintenance/", views.MaintenanceListView.as_view(), name="maintenance-list"),
    path("maintenance/new/", views.MaintenanceCreateView.as_view(), name="maintenance-create"),
    path("maintenance/<int:pk>/edit/", views.MaintenanceUpdateView.as_view(), name="maintenance-update"),
    path("maintenance/<int:pk>/delete/", views.MaintenanceDeleteView.as_view(), name="maintenance-delete"),
    path("notifications/", views.notifications_view, name="notifications"),
    path("security/", views.security_view, name="security"),
    path("settings/", views.settings_view, name="settings"),
    path("api/v1/heartbeat/", views.push_heartbeat, name="push-heartbeat"),
    path("api/v1/jobs/signal/", views.job_signal, name="job-signal"),
    path("push/<str:token>/", views.push_heartbeat_legacy, name="push-heartbeat-legacy"),
    path("health/live/", views.health_live, name="health-live"),
    path("health/ready/", views.health_ready, name="health-ready"),
    path("api/v1/summary/", views.manager_summary, name="manager-summary"),
    path("api/v1/jobs/", views.manager_jobs, name="manager-jobs"),
    path("api/v1/jobs/<int:pk>/", views.manager_job_detail, name="manager-job-detail"),
]
