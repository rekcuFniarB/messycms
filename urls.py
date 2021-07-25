from . import controllers
from django.urls import path

urlpatterns = [
    path('', controllers.show, name='messycms-root-path'),
    #path('node/<int:id>/', controllers.show),
    path('<path:path>/', controllers.show, name='messycms-node-by-path'),
]
