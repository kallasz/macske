from django.urls import path, re_path
from . import views
from . import consumers_phone
from . import consumers_arpi

# urlpatterns = [
#     path('phone/', views.phone_stream, name='phone_stream'),
#     path('arpi/', views.arpi_stream, name='arpi_stream'),
# ]

dash_urlpatterns = [
    path('', views.dash, name='dash_index'),
    path('arpi/', views.arpi_stream, name='arpi_stream'),
    path('catdetections/', views.dash_cat_detections, name='dash_cat_detections')
]

websocket_urlpatterns = [
    path('stream/phone/ws/', consumers_phone.PhoneStreamConsumer.as_asgi()),
    path('stream/arpi/ws/', consumers_arpi.ArpiStreamConsumer.as_asgi())
]
