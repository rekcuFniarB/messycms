from django import template
from ..models import Article
from django.utils import safestring
from .. import plugins

register = template.Library()

@register.simple_tag()
def path_by_id(id):
    '''
    Returns full path of item by it's ID
    '''
    path = '#'
    try:
        article = Article.objects.get(pk=id)
        path = article.path()
    except Article.DoesNotExist:
        pass
    
    return safestring.mark_safe(path)

@register.simple_tag(takes_context=True)
def render(context, node, *args, **kwargs):
    plugins.render(node, context['request'])
    return node.content

