from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, re_path, include
from rest_framework import permissions
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView




urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('djoser.urls.jwt')),
    path('api/auth/', include('djoser.urls.authtoken')),
    path('api/users/', include('users.urls')),
    path('api/learning/', include('learning_paths.urls')),
    path('api/learning/', include('learning.urls')),
    path('api/courses/', include('courses.urls')),
    path('api/gramafication/', include('gramafication.urls')),
    


    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
   

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
