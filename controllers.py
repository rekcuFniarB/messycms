from .models import Article
from django.shortcuts import render
from django.http import JsonResponse, Http404
from pprint import pprint
import re
import os
from django.conf import settings

recursion = [0, 30] ## [count, max]

## Show First article
def main(request):
    ''' Default ("/" URI) requet handler. '''
    recursion[0] = 0 ## reset counter
    
    if hasattr(settings, 'MAIN_ARTICLE'):
        article = Article.objects.get(pk=settings.MAIN_ARTICLE)
    else:
        article = Article.objects.order_by('tree_id', 'level')[0]
    article.content = parseTags(article.content, request)
    return render(request, 'content.html', {'article': article})
    #return JsonResponse(articles, safe=False)

## get requested article
def show(request, id):
    ''' /article/<int:id>/ request handler.'''
    
    recursion[0] = 0 ## reset counter
    try:
        article = Article.objects.get(pk=id)
    except Article.DoesNotExist:
        raise Http404('Requested article with ID %s doesn not exists.' % id)
    
    article.content = parseTags(article.content, request)
    response = render(request, 'content.html', {'article': article})
    print('Show(): #22 article.content')
    return response

## Tags parsing
def parseTags(content, request):
    ''' Tags parsing function.
    Args:
        content: string, article body or other text which may contain tags.
        request: request object.'''
    if recursion[0] > recursion[1]:
        ## avoid infinite recursion
        return content
    recursion[0] += 1 ## count this function calls
    
    ## If we have special tags in content, try to find and process them
    if '<!-- #' in content:
        ## If processing in recursion, process only main part of content
        if recursion[0] > 1 and '<!-- # main # -->' in content:
            ## remove part before "<!-- main -->"
            content = content.split('<!-- # main # -->')[1:]
            content = ''.join(content)
            ## remove part after "<!-- endmain -->"
            content = content.split('<!-- # endmain # -->')[:-1]
            content = ''.join(content)
        
        ## Tag format: <!-- # tagname param class # -->
        matches = re.findall(r'<!-- # (\S+?) (\S+?) (\S+?) # -->', content, re.MULTILINE)
        for match in matches:
            tag = '<!-- # %s %s %s # -->' % (match[0], match[1], match[2])
            if match[0] == 'menu':
                ## It's a <!-- # menu # --> tag
                nodes = getChildTree(match[1])
            elif match[0] == 'article':
                ## It's an <!-- # article # --> tag
                nodes = getArticle(match[1])
                ## Recursive content parsing
                nodes.content = parseTags(nodes.content, request)
            elif match[0] == 'articles':
                ## <!-- # articles # --> tag
                nodes = getArticles(match[1])
                for node in nodes:
                    node.content = parseTags(node.content, request)
            
            ## template subdir
            tdir = 'tags'
            
            ## So, we can get three templates:
            ##     class-type-item.html
            ##     class-type.html
            ##     type.html
            
            templates = (
                os.path.join(tdir, f'{match[0]}-{match[2]}-{match[1]}.html'),
                os.path.join(tdir, f'{match[0]}-{match[2]}.html'),
                os.path.join(tdir, f'{match[2]}-{match[0]}.html'),
                os.path.join(tdir, f'{match[0]}-{match[1]}.html'),
                os.path.join(tdir, f'{match[0]}.html'),
                
            )
            
            ## get content body of response object
            cblock = render(request, templates, {'nodes': nodes}).content.decode('utf-8')
            #cblock = '<div class="%s">%s</div>' % (match[2], cblock)
            cblock = '<!-- block %s -->%s<!-- endblock %s -->' % (match[2], cblock, match[2])
            ## inserting in the tag place
            content = content.replace(tag, cblock)
    
    return content

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
