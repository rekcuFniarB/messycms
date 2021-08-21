from django.conf import settings
import threading

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
