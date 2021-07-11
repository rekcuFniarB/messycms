from .models import Article
from django.shortcuts import render
from django.http import JsonResponse, Http404
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
        
        if article.get_absolute_url().strip('/') != request.path.strip('/'):
            ## redirects to get_absolute_url() of model
            return redirect(article)
        
    elif id:
        try:
           article = Article.objects.get(pk=id)
        except Article.DoesNotExist:
           raise Http404('Requested article with ID %s doesn not exists.' % id)
    else:
        raise Http404('Bad request, no page id or slug given.')
    
    recursion[0] = 0 ## reset counter
    
    ## If page has config
    if article.pageconf():
        plugins.render(request, article)
    else:
        parseTags(article, request)
    
    return render(request, 'messcms/base.html', {'article': article})

## Tags parsing
def parseTags(article, request):
    ''' Tags parsing function.
    Args:
        article: article object.
        request: request object.'''
    if recursion[0] > recursion[1]:
        ## avoid infinite recursion
        return article
    recursion[0] += 1 ## count this function calls
    
    ## If we have special tags in content, try to find and process them
    if '<!-- #' in article.content:
        ## If processing in recursion, process only main part of content
        if recursion[0] > 1 and '<!-- # main # -->' in article.content:
            ## remove part before "<!-- main -->"
            article.content = article.content.split('<!-- # main # -->')[1:]
            article.content = ''.join(article.content)
            ## remove part after "<!-- endmain -->"
            article.content = article.content.split('<!-- # endmain # -->')[:-1]
            article.content = ''.join(article.content)
        
        ## Tag format: <!-- # tagname param class # -->
        matches = re.findall(r'<!-- # (\S+?) (\S+?) (\S+?) # -->', article.content, re.MULTILINE)
        for match in matches:
            tag = '<!-- # %s %s %s # -->' % (match[0], match[1], match[2])
            nodes = None
            
            parsed_id = match[1]
            if parsed_id == 'self_id':
                parsed_id = article.id
            
            if match[0] == 'menu':
                ## It's a <!-- # menu # --> tag
                nodes = getChildTree(parsed_id)
            elif match[0] == 'article':
                ## It's an <!-- # article # --> tag
                if match[1] == 'self_id':
                    nodes = article
                else:
                    nodes = getArticle(parsed_id)
                    ## Recursive content parsing
                    nodes.content = parseTags(nodes, request)
            elif match[0] == 'articles':
                ## <!-- # articles # --> tag
                nodes = getArticles(parsed_id)
                for node in nodes:
                    node = parseTags(node, request)
            #elif match[0] == 'template':
            #    nodes = getArticle(parse_id)
            #    nodes.content = parseTags(nodes, request)
                
            
            ## template subdir
            tdir = 'tags'
            
            ## So, we can get three templates:
            ##     type-class-item.html
            ##     type-class.html
            ##     type.html
            
            templates = (
                os.path.join(tdir, f'{match[0]}-{match[2]}-{parsed_id}.html'),
                os.path.join(tdir, f'{match[0]}-{match[2]}.html'),
                os.path.join(tdir, f'{match[2]}-{match[0]}.html'),
                os.path.join(tdir, f'{match[0]}-{parsed_id}.html'),
                os.path.join(tdir, f'{match[0]}.html'),
                
            )
            
            if nodes:
                ## get content body of response object
                cblock = render(request, templates, {'nodes': nodes}).content.decode('utf-8')
                #cblock = '<div class="%s">%s</div>' % (match[2], cblock)
                cblock = '<!-- block %s -->%s<!-- endblock %s -->' % (match[2], cblock, match[2])
                ## inserting in the tag place
                article.content = article.content.replace(tag, cblock)
    
    return article

def getChildTree(id):
    ''' Get child nodes of specified object.'''
    id = int(id)
    if id == 0:
        return Article.objects.all()
    else:
        #return Article.objects.get(id=id).get_children() ## only one level for some reason
        #return Article.objects.get(id=id).children.all() ## same as above
        #return Article.objects.get(id=id) ## fail
        #return Article.objects.get(id=id).get_family() ## this returns also root node
        #return Article.objects.get(id=id).get_ancestors() ## empty
        return Article.objects.get(id=id).get_descendants() ## OK

def getArticle(id):
    ''' getArticle(id): get article object with specified id.'''
    id = int(id)
    return Article.objects.get(id=id)

def getArticles(id):
    ''' Get only one level articles which are children of article with specified id.'''
    id = int(id)
    if id == 0:
        return Article.objects.all()
    else:
        return Article.objects.get(id=id).get_children()

def testTree(request, id):
    tree = Article.objects.all()
    return render(request, 'menu.html', {'nodes': tree})

def str2int(string):
    try:
        value = int(string)
    except:
        value = 0
    return value
