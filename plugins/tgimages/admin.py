# Register your models here.

from django.contrib import admin
from .models import TGImages
#from mptt.admin import MPTTModelAdmin
from mptt.admin import DraggableMPTTAdmin

admin.site.register(
    TGImages,
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
