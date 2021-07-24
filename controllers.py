from .models import Article
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

## Show First article
def main(request):
    ''' Default ("/" URI) requet handler. '''
    recursion[0] = 0 ## reset counter
    
    if hasattr(settings, 'MAIN_ARTICLE'):
        article = Article.objects.get(pk=settings.MAIN_ARTICLE)
    else:
        article = Article.objects.order_by('tree_id', 'level')[0]
    article.content = parseTags(article, request)
    return render(request, 'content.html', {'article': article})
    #return JsonResponse(articles, safe=False)

## get requested article
def show(request, id=0, path=''):
    ''' /article/<int:id>/ request handler.'''
    
    if path:
        path_list = [x for x in path.split('/') if x]
        
        objects = None
        for path_part in path_list:
            if not objects:
                ## First iteration
                objects = Article.objects.filter(Q(pk=str2int(path_part)) | Q(slug=path_part))
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
        
        article = objects.first() ## or last()
        
        last_slug = path_list[-1]
        
        if not article:
            raise Http404(f'Article {last_slug} not found')
        
        if article.id != str2int(last_slug) and article.slug != last_slug:
            raise Http404(f'Got wrong article {article.id} {article.slug} while {last_slug} expected.')
        
    elif id:
        try:
           article = Article.objects.get(pk=id)
        except Article.DoesNotExist:
           raise Http404('Requested article with ID %s doesn not exists.' % id)
    else:
        raise Http404('Bad request, no page id or slug given.')
    
    if article.fmt != 'html' or not article.available or article.slug.startswith('.'):
        raise PermissionDenied
    
    if article.get_absolute_url().strip('/') != request.path.strip('/'):
        ## redirects to get_absolute_url() of model
        return redirect(article)
    
    #plugins.render_node(article, request)
    
    return render(request, 'messcms/base.html', {'node': article})

def str2int(string):
    try:
        value = int(string)
    except:
        value = 0
    return value
