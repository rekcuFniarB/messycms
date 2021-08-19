from . import controllers
from django.urls import path

urlpatterns = [
    path('', controllers.show, name='messycms-root-path'),
    path('<int:id>/', controllers.show, name='messycms-node-by-id'),
    path('<path:path>/', controllers.show, name='messycms-node-by-path'),
]
