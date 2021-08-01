# Register your models here.

from django.contrib import admin
#from django.contrib.auth.admin import UserAdmin
from .models import Node
#from mptt.admin import MPTTModelAdmin
from mptt.admin import DraggableMPTTAdmin

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
