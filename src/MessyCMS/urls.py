from . import controllers
from django.urls import path, include
from .models import Node
from django.conf import settings

app_name = 'messycms' ## namespace

urlpatterns = [
    path('', controllers.show_node, name='root-path'),
    path('<int:id>/', controllers.show_node, name='node-by-id'),
    path('<path:path>/', controllers.show_node, name='node-by-path'),
]
