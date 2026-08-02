from django.urls import path

from config.views import (BuildingPhotoProxyView, StreetViewProxyView, PublicSettingsView, CommunityListView, LocalityWardView, BuildingSurveyListView, RenewalSettingsView,
    StreetBuildingsView, StreetListView, StreetMergeView, StreetSplitView, StreetSummaryView,
    StreetUpdateView, StreetTypeDetailView, StreetTypeListView)

urlpatterns = [
    path('streetview/', StreetViewProxyView.as_view(), name='streetview'),
    path('public-settings/', PublicSettingsView.as_view(), name='public-settings'),

    path('street-types/', StreetTypeListView.as_view(), name='street-type-list'),
    path('street-types/<uuid:pk>/', StreetTypeDetailView.as_view(), name='street-type-detail'),
    path('building-surveys/', BuildingSurveyListView.as_view(), name='building-survey-list'),
    path('building-surveys/photo/', BuildingPhotoProxyView.as_view(), name='building-photo-proxy'),
    path('streets/', StreetListView.as_view(), name='street-list'),
    path('streets/summary/', StreetSummaryView.as_view(), name='street-summary'),
    path('locality-wards/', LocalityWardView.as_view(), name='locality-wards'),
    path('communities/', CommunityListView.as_view(), name='communities'),
    path('streets/merge/', StreetMergeView.as_view(), name='street-merge'),
    path('streets/<uuid:pk>/split/', StreetSplitView.as_view(), name='street-split'),
    path('streets/<uuid:pk>/update/', StreetUpdateView.as_view(), name='street-update'),
    path('streets/<uuid:pk>/buildings/', StreetBuildingsView.as_view(), name='street-buildings'),
    path('renewal-settings/', RenewalSettingsView.as_view(), name='renewal-settings'),
]
