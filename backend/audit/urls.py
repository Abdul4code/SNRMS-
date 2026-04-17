from django.urls import path

from audit.views import ActivityLogListView

urlpatterns = [
    path('logs/', ActivityLogListView.as_view(), name='activity-log-list'),
]
