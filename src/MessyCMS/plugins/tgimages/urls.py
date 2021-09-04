from . import controllers
from django.urls import path
app_name = 'tgimages'
urlpatterns = [
    path('<int:id>/', controllers.show_album, name='tgimages-show-album'),
]
