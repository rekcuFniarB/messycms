from . import controllers
from django.urls import path

urlpatterns = [
    path('', controllers.main),
    path('article/<int:id>/', controllers.show),
    path('tree/<int:id>/', controllers.testTree),
]
