from django.urls import path

from config.views import BuildingPhotoProxyView, BuildingSurveyListView, StreetTypeDetailView, StreetTypeListView

urlpatterns = [
    path('street-types/', StreetTypeListView.as_view(), name='street-type-list'),
    path('street-types/<uuid:pk>/', StreetTypeDetailView.as_view(), name='street-type-detail'),
    path('building-surveys/', BuildingSurveyListView.as_view(), name='building-survey-list'),
    path('building-surveys/photo/', BuildingPhotoProxyView.as_view(), name='building-photo-proxy'),
]
