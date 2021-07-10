# Register your models here.

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Article
#from mptt.admin import MPTTModelAdmin
from mptt.admin import DraggableMPTTAdmin

#class ArticleAdmin(admin.ModelAdmin):
    #readonly_fields = ('id',)

admin.site.register(
    Article,
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

#admin.site.register(Article, MPTTModelAdmin)

admin.site.register(User, UserAdmin)
#admin.site.register(Article)
