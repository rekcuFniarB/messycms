from django import template
from ..models import Node
from django.utils import safestring
from .. import plugins
from django.urls import resolve

register = template.Library()

@register.simple_tag()
def path_by_id(id):
    '''
    Returns full path of item by it's ID
    '''
    path = '#'
    try:
        node = Node.objects.get(pk=id)
        path = node.path()
    except Node.DoesNotExist:
        pass
    
    return safestring.mark_safe(path)

@register.simple_tag(takes_context=True)
def render(context, node, *args, **kwargs):
    plugins.render(node, context['request'])
    return node.content

@register.simple_tag(takes_context=True)
def render_view(context, path, *args, **kwargs):
    resolved = resolve(path)
    response = resolved.func(context['request'], **resolved.kwargs)
    return safestring.mark_safe(response.content.decode(response.charset))
