from django.conf import settings
import threading
from MessyCMS.models import Node
from django.shortcuts import render
from django.utils.html import escape as html_escape
from django.http.response import HttpResponse, HttpResponseNotFound

_thread_locals = threading.local()

def log(*args, **kwargs):
    if settings.DEBUG:
        from pprint import pprint
        pprint(args)

def should_skip_middleware(request, response):
    skip = False
    if request.resolver_match:
        if request.resolver_match.app_name == 'admin':
            skip = True
        
        #if request.resolver_match.app_name == 'messycms' and type(response) is HttpResponse:
        #    ## response may be also HttpResponseNotFound, not bypassig it
        #    ## allow us insert error response into template node.
        #    skip = True
        
        if request.resolver_match.app_name == 'messycms' and type(response) is HttpResponseNotFound:
            skip = False
    
    if 'HTTP_X_REQUESTED_WITH' in request.META:
        skip = True
    if not response.headers.get('Content-Type', '').startswith('text/html'):
        skip = True
    if response.headers.get('Location', ''):
        skip = True
    if not hasattr(response, 'content') or not response.content:
        skip = True
    #if not template_node_id:
        #skip = True
    
    return skip

class DomainUrlconf:
    '''
    This middleware dynamically defines root urlconf for requested domain.
    Urlconfs can be defined in settings like this:
    HOSTS_URLCONF = {
        'example.com': 'example_com.urls',
        'exampe.net': 'example_net.urls',
    }
    '''
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        ## If there is special urlconf defined for hostname, use that
        ## or default if None
        if hasattr(request, 'site') and hasattr(settings, 'HOSTS_URLCONF'):
            request.urlconf = settings.HOSTS_URLCONF.get(request.site.domain, None)
        
        if not getattr(_thread_locals, 'request', None):
            _thread_locals.request = request
        
        ## Before view code
        
        response = self.get_response(request)
        
        ## After view code
        
        return response

class PluggableExternalAppsWrapper:
    '''
    This middleware takes response from 3rd party apps and inserts into MessyCMS template node.
    '''
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        
        ## Before view code
        
        response = self.get_response(request)
        
        ## After view code
        
        #template_node_id = getattr(settings, 'MESSYCMS_DEFAULT_TEMPLATE_NODE_ID', None)
        
        skip = True
        if request.resolver_match:
            ## settings.MESSYCMS_WRAP_ROUTES is list of routes templates like 'user/<id>/'
            for route in getattr(settings, 'MESSYCMS_WRAP_ROUTES', []):
                if route.startswith('/'):
                    if request.resolver_match.route.lstrip('/ ').startswith(route.strip('/ ')):
                        skip = False
                        break
                else:
                    if request.resolver_match.route.rstrip('/ ').endswith(route.strip('/ ')):
                        skip = False
                        break
        
        skip = skip or should_skip_middleware(request, response)
        
        ## Get first available templates
        if not skip:
            ## Tmp blank node
            node = Node()
            ## Applying response content to this blank node. (response.content is bytes)
            node.content = response.content.decode(response.charset)
            new_response = self.prepare_response(request, node)
            response.content = new_response.content
        
        return response
    
    @classmethod
    def get_template_node(cls, request):
        '''
        Get first available template for current site and language code
        '''
        template_node = None
        node_section = None
        
        queryset = Node.objects.filter(parent_id=None, sites__id=request.site.id, available=True)
        lang_code = getattr(request, 'LANGUAGE_CODE', None)
        if lang_code:
            ## Get first part (no lang subcode)
            lang_code = lang_code.split('-')[0]
            lng_queryset = queryset.get_descendants().filter(slug=lang_code, sites__id=request.site.id, available=True)
            node_section = lng_queryset.get_descendants().filter(type='inclusion_point').first()
        
        if not node_section:
            ## Node for current language not found, search global
            node_section = queryset.get_descendants().filter(type='inclusion_point').first()
        
        if node_section and node_section.parent_id and node_section.parent.type == '.conf':
            if node_section.parent.parent_id and node_section.parent.parent.type == 'content':
                template_node = node_section.parent.parent
        
        return template_node
    
    @classmethod
    def prepare_response(cls, request, node):
        '''
        Prepare response.
        request: Request object.
        node:    CMS Node object.
        Returns django HTTPResponse object.
        '''
        templates = {
            'internal': (
                f'{request.site.domain}/messycms/_node.html',
                'messycms/_node.html',
            ),
            'full': (
                f'{request.site.domain}/messycms/node.html',
                'messycms/node.html',
            )
        }
        
        request_node = node
        
        kwargs = {}
        httpStatusCode = node.prop('httpStatusCode')
        if httpStatusCode:
            kwargs['status'] = httpStatusCode
        responseContentType = node.prop('httpContentType')
        if responseContentType:
            kwargs['content_type'] = responseContentType
        
        if 'HTTP_X_REQUESTED_WITH' in request.META:
            ## If is ajax request, don't extend base template
            template_type = 'internal'
        elif responseContentType and not responseContentType.startswith('text/html'):
            template_type = 'internal'
        else: ## { not ajax
            template_type = 'full'
            
            if node.link_id:
                ## If link is defined, we use linked node as template for current
                inclusion_point = node.link.prop('inclusion_point')
                if inclusion_point:
                    inclusion_point.type = 'IncludeItem'
                    inclusion_point.link = node
                    inclusion_point.ts_updated = node.ts_updated ## for cache
                    node = node.link
            else:
                ## Try to use first available template
                template_node = cls.get_template_node(request)
                if template_node:
                    inclusion_point = template_node.prop('inclusion_point')
                    if inclusion_point:
                        inclusion_point.type = 'IncludeItem'
                        inclusion_point.link = node
                        inclusion_point.ts_updated = node.ts_updated ## for cache
                        node = template_node
            
            node.title = request_node.title
            node.ts_updated = request_node.ts_updated
        ## } endif not ajax
        
        context = {
            'node': node,
            'request_node': request_node,
            'template_node': node,
            'allnodes': {},
            'template_type': template_type
        }
        
        ## "allnodes" will contain all rendered subnodes
        response = render(request, templates[template_type], context, **kwargs)
        setattr(response, 'messyContext', context)
        
        responseContentType = response.headers.get('Content-Type', '')
        
        if responseContentType.startswith('text/html'):
            ## Inserting deferred nodes.
            ## For example, if node has slug "append-to-head"
            ## it will be appended to <head> element (inserted before closing </head> tag).
            for node in response.messyContext['allnodes'].values():
                append_to = node.append_to()
                if append_to:
                    append_to = append_to.encode(response.charset)
                    response.messyContext['node'] = node
                    append_render = render(request, templates['internal'], response.messyContext)
                    response.content = response.content.replace(append_to, append_render.content + append_to)
        
        return response

class MoveHtmlParts:
    '''
    Moving html parts to the header or to the body end.
    '''
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        
        ## Before view code
        
        response = self.get_response(request)
        
        ## After view code
        
        if not should_skip_middleware(request, response):
            snippets = self.substr(response.content, (b'<template ', b'</template>'))
            for snippet in snippets:
                partition = snippet.partition(b'>')
                if partition[1] and partition[2]:
                    ## is <template data-head>
                    if b'data-move-to-head' in partition[0]:
                        ## Removing from original place and blacing before </head>
                        response.content = response.content.replace(b'<template ' + snippet + b'</template>', b'').replace(b'</head>', partition[2] + b'\n</head>', 1)
                    elif b'data-move-to-bottom' in partition[0]:
                        ## Removing from original place and blacing before </body>
                        response.content = response.content.replace(b'<template ' + snippet + b'</template>', b'').replace(b'</body>', partition[2] + b'\n</body>', 1)
        
        return response
    
    @classmethod
    def substr(cls, string, wrapper):
        '''
        Find substring enclosed by wrapper;
        Args:
            string: input string or bytes
            wrapper: tuple of two strings.
        Returns: list of found substrings.
        '''
        found = []
        start = 0
        end = 0
        
        while start > -1 and end > -1:
            start = string.find(wrapper[0], start)
            if start > -1:
                start += len(wrapper[0])
                end = string.find(wrapper[1], start)
                if end > -1:
                    substring = string[start:end]
                    start = end + len(wrapper[1])
                    if substring:
                        found.append(substring)
        
        return found

class OpenGraph:
    '''
    Adds opengraph meta tags to header
    '''
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        
        ## Before view code
        
        response = self.get_response(request)
        
        ## After view code
        
        if hasattr(response, 'messyContext') and not should_skip_middleware(request, response):
            og_html = ''
            
            og_title = response.messyContext['request_node'].prop('ogTitle', '') or response.messyContext['request_node'].title
            if og_title:
                og_title = html_escape(og_title)
                og_html += f'<meta property="og:title" content="{og_title}"/>\n'
            
            og_image = response.messyContext['request_node'].prop('ogImage', None) or response.messyContext['template_node'].prop('ogImage', None)
            if og_image:
                og_image = html_escape(og_image)
                og_html += f'<meta property="og:image" content="{og_image}"/>\n'
            
            og_description = response.messyContext['request_node'].prop('ogDescription', None) or response.messyContext['template_node'].prop('ogDescription', None)
            if og_description:
                og_description = html_escape(og_description)
                og_html += f'<meta property="og:description" content="{og_description}"/>\n'
            
            
            try:
                og_url = 'https://'
                if not request.is_secure():
                    og_url='http://'
                og_url += request.META.get('HTTP_HOST')
                og_url += response.messyContext['request_node'].get_absolute_url()
                og_html += f'<meta property="og:url" content="{html_escape(og_url)}">\n'
            except:
                pass
            
            if og_html:
                if 'twitter:cart' not in og_html:
                    og_html += '<meta name="twitter:card" content="summary"/>\n'
                og_html += '</head>\n'
                og_html = og_html.encode(response.charset)
                ## Appending to the end of html head
                response.content = response.content.replace('</head>'.encode(response.charset), og_html, 1)
        
        return response

class DBRouter:
    '''Switching databases based on hostname
        https://docs.djangoproject.com/en/dev/topics/db/multi-db/
    '''
    
    def db_for_read(self, model, **hints):
        return self.get_by_request_hostname()
    
    def db_for_write(self, model, **hints):
        return self.get_by_request_hostname()
    
    def get_by_request_hostname(self):
        db_name = None
        if hasattr(_thread_locals, 'request') and hasattr(_thread_locals.request, 'site'):
            if _thread_locals.request.site.domain in settings.DATABASES:
                db_name = _thread_locals.request.site.domain
        
        return db_name
