from . import controllers
from django.urls import path

urlpatterns = [
    path('<int:id>/', controllers.show_album, name='tgimages-show-album'),
]
