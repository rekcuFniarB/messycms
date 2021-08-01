# Register your models here.

from django.contrib import admin
#from django.contrib.auth.admin import UserAdmin
from .models import Node
#from mptt.admin import MPTTModelAdmin
from mptt.admin import DraggableMPTTAdmin

#class NodeAdmin(admin.ModelAdmin):
    #readonly_fields = ('id',)

admin.site.register(
    Node,
    DraggableMPTTAdmin,
    list_display=(
        'tree_actions',
        'indented_title',
        # ...more fields if you feel like it...
    ),
    list_display_links=(
        'indented_title',
    ),
    readonly_fields = ('id',)
)

#admin.site.register(Node, MPTTModelAdmin)

#admin.site.register(User, UserAdmin)
#admin.site.register(Node)
