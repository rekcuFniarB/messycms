from django.conf import settings
from django.contrib import admin
#from django.contrib.auth.admin import UserAdmin
from .models import Node
from . import plugins
#from mptt.admin import MPTTModelAdmin
from mptt.admin import DraggableMPTTAdmin
from django.urls import path, reverse
from django.http import JsonResponse
import json
from django.core.exceptions import PermissionDenied
#from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q
from django import forms
from django.shortcuts import render
from django.apps import apps

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
    
    def delete_model(self, request, obj):
        if not request.user.is_superuser:
            if obj.author != request.user and obj.group not in request.user.groups.all():
                ## Prevent deleting if no permission
                raise PermissionDenied
        return super().delete_model(request, obj)
    
    def get_queryset(self, request, *args, **kwargs):
        qs = super().get_queryset(request)
        
        query = request.GET.get('q', '')
        if query.startswith('parentId'):
            parent_id = plugins.str2int(query.replace('parentId', ''))
            if parent_id:
                qs = qs.filter(pk=parent_id).get_descendants(include_self=True)
        elif query.startswith('sections'):
            parent_id = plugins.str2int(query.replace('sections', ''))
            if parent_id:
                qs = qs.filter(pk=parent_id).get_descendants(include_self=True)
                qs = qs.filter(parent__type='.conf')
        
        if request.path.endswith('/node/') and not query.startswith('sections') and not query.startswith('all'):
            qs = qs.filter(type='content').filter(parent__type='content')
        
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
        return [
            path('fields-toggle-maps.json', self.fields_toggle_maps),
            path('nodes-links.json', self.nodes_links),
            path('toggle-available/<int:pk>/', self.toggle_available),
            path('select-model-modal/', self.select_model_modal),
            path('select-model-modal/<str:model_name>/', self.select_model_modal),
            path('select-model-modal/<str:model_name>/<str:item_id>/', self.select_model_modal),
        ] + super().get_urls()
    
    def toggle_available(self, request, pk):
        '''
        Ajax request to toggle node availability.
        '''
        if not request.user.is_staff:
            raise PermissionDenied('For staff only')
        
        if request.method != 'POST':
            raise PermissionDenied('Bad request method.')
        
        node = None
        
        if pk:
            try:
                node = Node.objects.get(pk=pk)
            except:
                pass
        
        result = {}
        
        if node and node.type == 'content':
            if not request.user.is_superuser and node.author != request.user and node.group not in request.user.groups.all():
                ## Prevent deleting if no permission
                raise PermissionDenied
            
            result['change'] = [node.available]
            
            if node.available:
                node.available = False
            else:
                node.available = True
            
            result['change'].append(node.available)
            
            node.save()
        
        return JsonResponse({"succes": bool(node), 'result': result})
    
    def fields_toggle_maps(self, request):
        '''
        Ajax request for fields mappings.
        '''
        
        if not request.user.is_staff:
            raise PermissionDenied
        field = request.GET.get('field', '')
        plugin_instance = plugins.get_plugin_instance(field)
        if plugin_instance:
            fields_maps = {field: plugin_instance.fields_toggle}
        else:
            fields_maps = Node.fields_toggle
        return JsonResponse(fields_maps)
    
    def select_model_modal(self, request, model_name='', item_id=''):
        '''
        Invoked by ajax request for popup form.
        '''
        
        if not request.user.is_staff:
            raise PermissionDenied
        
        model_items_choices = [('', '')]
        ## Filling ids choices for selected model.
        if model_name:
            model_qs = Node.get_from_model(None, model_name)
            for item in model_qs:
                model_items_choices.append((item.pk, f'{item.pk}: {str(item)}'))
        
        form = modelItemForm({
            'model_name': model_name,
            'model_item_id': item_id
        })
        
        form.fields['model_item_id'].choices = model_items_choices
        
        return render(
            request,
            'messycms/admin/select_model_modal.html',
            {'form': form}
        )
    
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
                'value': reverse('messycms:node-by-path', kwargs={'path': item.id}),
                'data-node-id': f'{item.id}'
            })
        
        ## TypeError: In order to allow non-dict objects to be serialized set the safe parameter to False.
        return JsonResponse(result, safe=False)
    
    class Media:
        js = [
            ## Include this script in admin interface.
            'messycms/js/admin.js',
            'messycms/js/messycms.js',
        ]
        css = {
            'all': ('messycms/css/admin.css',)
        }
        if 'tinymce' in settings.INSTALLED_APPS:
            js.append('tinymce/tinymce.min.js')
        else:
            js.append(f'https://cdn.tiny.cloud/1/{getattr(settings, "TinyMCE_API_Key", "no-api-key")}/tinymce/5/tinymce.min.js')

## Select model form for popup
class modelItemForm(forms.Form):
    def get_installed_models():
        result = [('', '-')]
        ## Getting list of available models
        for app_name, app_models in apps.all_models.items():
            for model_name, model in app_models.items():
                result.append((f'{model.__module__}.{model.__name__}', f'{app_name}/{model_name}'))
        return result
    
    model_name = forms.ChoiceField(required=False, choices=get_installed_models)
    model_item_id = forms.ChoiceField(required=False, choices=[('', '')])

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
