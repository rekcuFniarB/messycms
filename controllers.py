from .models import Node
from django.shortcuts import render
from django.http import JsonResponse, Http404
from django.core.exceptions import PermissionDenied
from pprint import pprint
import re
import os
from django.conf import settings
from django.db.models import Q
from django.shortcuts import redirect
from . import plugins

recursion = [0, 30] ## [count, max]

## Show First node
def main(request):
    ''' Default ("/" URI) requet handler. '''
    recursion[0] = 0 ## reset counter
    
    if hasattr(settings, 'MAIN_ARTICLE'):
        node = Node.objects.get(pk=settings.MAIN_ARTICLE)
    else:
        node = Node.objects.order_by('tree_id', 'level')[0]
    node.content = parseTags(node, request)
    return render(request, 'content.html', {'node': node})
    #return JsonResponse(nodes, safe=False)

## get requested node
def show(request, id=0, path=''):
    ''' /<str:path>/ request handler.'''
    
    if path:
        path_list = [x for x in path.split('/') if x]
        
        objects = None
        for path_part in path_list:
            if not objects:
                ## First iteration
                objects = Node.objects.filter(Q(pk=str2int(path_part)) | Q(slug=path_part))
            else:
                ## objects is QuerySet, it hasn't get_children() method
                querysets = []
                for item in objects:
                    querysets.append(item.get_children().filter(Q(pk=str2int(path_part)) | Q(slug=path_part)))
                if len(querysets):
                    ## combining all querysets from previous for loop
                    objects = querysets.pop()
                    for queryset in querysets:
                        objects = objects | queryset
        
        node = objects.first() ## or last()
        
        last_slug = path_list[-1]
        
        if not node:
            raise Http404(f'Node {last_slug} not found')
        
        if node.id != str2int(last_slug) and node.slug != last_slug:
            raise Http404(f'Got wrong node {node.id} {node.slug} while {last_slug} expected.')
        
    elif id:
        try:
           node = Node.objects.get(pk=id)
        except Node.DoesNotExist:
           raise Http404(f'Requested node with ID {id} does not exist.')
    else:
        raise Http404('Bad request, no page id or slug given.')
    
    if node.type != 'html' or not node.available or node.slug.startswith('.'):
        raise PermissionDenied
    
    if node.get_absolute_url().strip('/') != request.path.strip('/'):
        ## redirects to get_absolute_url() of model
        return redirect(node)
    
    #plugins.render(node, request)
    
    return render(request, 'messycms/base.html', {'node': node})

def str2int(string):
    try:
        value = int(string)
    except:
        value = 0
    return value
