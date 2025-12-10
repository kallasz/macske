from django.contrib import admin
from django.urls import include, path
from stream.urls import dash_urlpatterns
from django.conf import settings
from django.conf.urls.static import static
from stream import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name="index"),
    path('dash/', include(dash_urlpatterns)),
    path('stream/', views.stream, name="stream"),
    # path('stream/', include(stream_urlpatterns)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)