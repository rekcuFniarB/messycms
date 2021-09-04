from django.conf import settings
import threading
from MessyCMS.models import Node
from django.shortcuts import render
    

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
        
        skip = False
        if request.resolver_match and request.resolver_match.app_name in  ('admin', 'messycms'):
            skip = True
        if 'HTTP_X_REQUESTED_WITH' in request.META:
            skip = True
        if not response.headers.get('Content-Type', '').startswith('text/html'):
            skip = True
        #if not template_node_id:
            #skip = True
        
        ## Get first available templates
        template_node = None
        node_section = None
        
        if not skip:
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
        
        if template_node:
            ## Tmp blank node
            node = Node()
            ## Applying response content to this blank node. (response.content is bytes)
            node.content = response.content.decode(response.charset)
            #template_node = Node.objects.get(pk=template_node_id)
            template_node.context['include'] = node
            templates = (
                f'{request.site.domain}/messycms/node.html',
                'messycms/node.html',
            )
            new_response = render(request, template_name=templates, context={'node': template_node})
            response.content = new_response.content
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
