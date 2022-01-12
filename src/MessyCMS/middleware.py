from django.conf import settings
import threading
from MessyCMS.models import Node
from django.shortcuts import render
from django.http.response import HttpResponse, HttpResponseNotFound

_thread_locals = threading.local()

def log(*args, **kwargs):
    if settings.DEBUG:
        from pprint import pprint
        pprint(args)

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
        if not response.content:
            skip = True
        #if not template_node_id:
            #skip = True
        
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
        
        response = {'context': {'node': node, 'request_node': request_node, 'allnodes': {}, 'template_type': template_type}}
        ## "allnodes" will contain all rendered subnodes
        response['response'] = render(request, templates[template_type], response['context'], **kwargs)
        
        responseContentType = response['response'].headers.get('Content-Type', '')
        
        if responseContentType.startswith('text/html'):
            ## Inserting deferred nodes.
            ## For example, if node has slug "append-to-head"
            ## it will be appended to <head> element (inserted before closing </head> tag).
            for node in response['context']['allnodes'].values():
                append_to = node.append_to()
                if append_to:
                    append_to = append_to.encode(response['response'].charset)
                    response['context']['node'] = node
                    append_render = render(request, templates['internal'], response['context'])
                    response['response'].content = response['response'].content.replace(append_to, append_render.content + append_to)
        
        return response['response']

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
