# Register your models here.

from django.contrib import admin
#from django.contrib.auth.admin import UserAdmin
from .models import Node
#from mptt.admin import MPTTModelAdmin
from mptt.admin import DraggableMPTTAdmin
from django.urls import path, reverse
from django.http import JsonResponse
import json
from django.core.exceptions import PermissionDenied
#from django.contrib.admin.views.decorators import staff_member_required

class NodeAdmin(DraggableMPTTAdmin):
    readonly_fields = ('id',)
    list_display = (
        'tree_actions',
        'indented_title',
        'available'
        # ...more fields if you feel like it...
    )
    list_display_links = (
        'indented_title',
    )
    
    def save_model(self, request, obj, form, change):
        ## It is executed before model's save()
        if not obj.author:
            ## Set author to current user if blank.
            obj.author = request.user
        obj.save()
    
    def get_urls(self):
        return super().get_urls() + [
            path('fields-toggle-maps.json', self.fields_toggle_maps),
            path('nodes-links.json', self.nodes_links),
        ]
    
    def fields_toggle_maps(self, request):
        if not request.user.is_staff:
            raise PermissionDenied
        return JsonResponse(Node.fields_toggle)
    
    #@staff_member_required
    def nodes_links(self, request):
        if not request.user.is_staff:
            raise PermissionDenied
        
        result = []
        
        querySet = Node.objects.filter(type='content', available=True, sites__id=request.site.id).order_by('lft', 'rght')
        
        for item in querySet:
            if item.parent_id and item.parent.type != 'content':
                continue
            
            result.append({
                'title': f'{"." * item.level} {str(item)}',
                'value': reverse('messycms-node-by-path', kwargs={'path': item.id}),
                'data-node-id': f'{item.id}'
            })
        
        ## TypeError: In order to allow non-dict objects to be serialized set the safe parameter to False.
        return JsonResponse(result, safe=False)
    
    class Media:
        js = (
            ## Include this script in admin interface.
            'messycms/js/admin.js',
            'https://cdn.tiny.cloud/1/no-api-key/tinymce/5/tinymce.min.js'
        )
    
#admin.site.register(
    #Node,
    #DraggableMPTTAdmin,
    #list_display=(
        #'tree_actions',
        #'indented_title',
        ## ...more fields if you feel like it...
    #),
    #list_display_links=(
        #'indented_title',
    #),
    #readonly_fields = ('id',)
#)

#admin.site.register(Node, MPTTModelAdmin)
admin.site.register(Node, NodeAdmin)
#admin.site.register(User, UserAdmin)
#admin.site.register(Node)
