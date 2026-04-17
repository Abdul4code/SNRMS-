from django.urls import path

from config.views import StreetTypeDetailView, StreetTypeListView

urlpatterns = [
    path('street-types/', StreetTypeListView.as_view(), name='street-type-list'),
    path('street-types/<uuid:pk>/', StreetTypeDetailView.as_view(), name='street-type-detail'),
]
