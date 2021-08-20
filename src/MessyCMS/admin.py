from django.conf import settings
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
from django.db.models import Q

# Register your models here.

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
        if not obj.group:
            ## Set to current user group if blank.
            obj.group = request.user.groups.first()
        
        if not form.cleaned_data.get('sites') and hasattr(request, 'site'):
            ## Setting current site if not set.
            ## Just assigning to obj.sites doesn't work because of m2m field.
            form.cleaned_data['sites'] = request.site.__class__.objects.filter(id=request.site.id)
        
        #obj.save()
        return super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(Q(author=request.user) | Q(group__in=request.user.groups.all())).filter(sites=request.site.id)
    
    def get_form(self, request, obj=None, **kwargs):
        if not request.user.is_superuser:
            kwargs['exclude'] = ['author', 'group', 'link']
        
        form = super().get_form(request, obj, **kwargs)
        
        if not request.user.is_superuser:
            ## Filter dropdown elements by current user and group
            form.base_fields['parent']._queryset = form.base_fields['parent']._queryset.filter(Q(author=request.user) | Q(group__in=request.user.groups.all()))
            ## Show only current site in list. We can not exclude this field completely
            ## because it will not allow to set site in save_model() otherwise.
            form.base_fields['sites']._queryset = form.base_fields['sites']._queryset.filter(id=request.site.id)
        
        return form
    
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
        
        querySet = self.get_queryset(request).filter(type='content', available=True, sites__id=request.site.id)
        
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
        js = [
            ## Include this script in admin interface.
            'messycms/js/admin.js',
        ]
        if 'tinymce' in settings.INSTALLED_APPS:
            js.append('tinymce/tinymce.min.js')
        else:
            js.append(f'https://cdn.tiny.cloud/1/{getattr(settings, "TinyMCE_API_Key", "no-api-key")}/tinymce/5/tinymce.min.js')

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
