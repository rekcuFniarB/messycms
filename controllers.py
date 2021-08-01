from .models import Node
from django.shortcuts import render
from django.http import JsonResponse, Http404
from django.core.exceptions import PermissionDenied
#from pprint import pprint
import re
import os
from django.conf import settings
from django.db.models import Q
from django.shortcuts import redirect
from . import plugins

## get requested node
def show(request, id=0, path=''):
    ''' /<str:path>/ request handler.'''
    
    if path:
        path_list = [x for x in path.split('/') if x]
        last_slug = path_list[-1]
        
        ## Get root for requested domain
        objects = Node.objects.filter(parent_id=None, sites__id=request.site.id)
        
        #for path_part in path_list:
            
        
        for path_part in path_list:
            if not objects:
                ## First iteration
                objects = Node.objects.filter(Q(pk=str2int(path_part)) | Q(slug=path_part), sites__id=request.site.id)
            else:
                ## objects is QuerySet, it hasn't get_children() method
                querysets = []
                for item in objects:
                    queryset = item.get_children().filter(Q(pk=str2int(path_part)) | Q(slug=path_part), sites__id=request.site.id)
                    if queryset:
                        querysets.append(queryset)
                if len(querysets):
                    ## combining all querysets from previous for loop
                    objects = querysets.pop()
                    for queryset in querysets:
                        if queryset:
                            objects = objects | queryset
                #else:
                    #raise Http404(f'Path part "{path_part}" not found.')
        
        node = objects.filter(Q(pk=str2int(last_slug)) | Q(slug=last_slug), sites__id=request.site.id).first() ## or last()
        
        if not node:
            ## If node was not found by exact path, trying to find anywhere
            ## and redirect to actual path.
            objects = Node.objects.filter(Q(pk=str2int(last_slug)) | Q(slug=last_slug), sites__id=request.site.id)
            if objects.count() == 1:
                ## found
                node = objects.first()
                if node.get_absolute_url().strip('/') == request.path.strip('/'):
                    ## Path is same. It means that some path parts are disabled.
                    raise Http404(f'Path "{request.path}" not found.')
            elif objects.count() > 1:
                ## FIXME on 404 page show list of links to choose
                raise Http404(f'Too many nodes with slug "{last_slug}" found.')
            else:
                raise Http404(f'Node "{last_slug}" not found')
        
        if node.id != str2int(last_slug) and node.slug != last_slug:
            raise Http404(f'Got wrong node "{node.id} {node.slug}" while "{last_slug}" expected.')
        
    elif id:
        ## This was for testing, actually not used
        try:
           node = Node.objects.get(pk=id)
        except Node.DoesNotExist:
           raise Http404(f'Requested node with ID {id} does not exist.')
    else:
        ## Main page requested
        node = Node.objects.filter(parent_id=None, sites__id=request.site.id).first()
        if not node:
            raise Http404(f'Main page for requested site {request.site} not found.')
    
    if node.type != 'html' or not node.available or node.slug.startswith('.'):
        raise PermissionDenied
    
    if node.get_absolute_url().strip('/') != request.path.strip('/'):
        ## redirects to real path if node was moved.
        return redirect(node)
    
    ## If node has redirect property
    if hasattr(node.conf, 'redirect'):
        ## If it's a link to another node
        if hasattr(node.conf.redirect, 'link_id') and node.conf.redirect.link_id:
            return redirect(node.conf.redirect.link)
        ## If it's a string URL
        elif node.conf.redirect:
            return redirect(node.conf.redirect)
    
    #plugins.render(node, request)
    
    return render(
        request,
        (
            f'{request.site.domain}/messycms/base.html',
            'messycms/base.html',
        ),
        {'node': node}
    )

def str2int(string):
    try:
        value = int(string)
    except:
        value = 0
    return value
