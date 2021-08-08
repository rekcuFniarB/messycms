from . import models
from django.shortcuts import render
from django.http import JsonResponse, Http404
from django.core.exceptions import PermissionDenied

def show_album(request, id):
    try:
        root = models.TGImages.objects.get(pk=id)
        nodes = root.get_children().filter(available=True)
    except models.TGImages.DoesNotExist:
        raise Http404(f'Album does not exist')
    
    return render(
        request,
        'tgimages/album.html',
        {'nodes': nodes, 'node': root}
    )
