from django.urls import re_path
from AqApp import views
from django.urls import include, path


urlpatterns=[
    re_path(r'^site$',views.site_api),
    re_path(r'^site/([0-9]+)$',views.site_api),
    re_path(r'^pollutant$',views.pollutant_api),
    re_path(r'^pollutant/([0-9]+)$',views.pollutant_api),
    # path('api/v1/sample/response', views.ListUsers.as_view()),
    path('api/v1/pollutant/list/', views.PollutantDataAPIView.as_view()),
    path('api/v1/location/list/', views.LocationDataAPIView.as_view()),
    path('api/v1/location/source/<str:source>/list/', views.LocationSourceDataAPIView.as_view()),
    path('api/v1/lat-long/nearest-location/list/', views.NearestLocationAPIView.as_view()),
    path('api/v1/slicefromcataglog/recentandarchive/', views.SliceFromCatagLog.as_view()),
    path('api/v1/lat-long/nearest-forcast-location/list/', views.NearestLocationOfForcastAPIView.as_view()),
    path('api/v1/lat-long/forcast/list/', views.LocationOfForcastAPIView.as_view()),
    path('api/v1/lat-long/recent-archive/list/', views.RecentArchiveLocationAPIView.as_view()),
    path('api/v1/location/source/<str:source>/geos/list/', views.GeosLocationSourceDataAPIView.as_view()),
    
]
