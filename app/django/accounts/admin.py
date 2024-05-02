from django.contrib import admin
from import_export.admin import ImportExportMixin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .forms import UserCreationForm, UserChangeForm
from .models import User, StaffAuth, Profile, Todo, Scrape


# class StaffAuthInline(admin.StackedInline):
#     model = StaffAuth


# class ProfileInline(admin.StackedInline):
#     model = Profile
#
#
# class TodosInline(admin.StackedInline):
#     model = Todo


class UserAdmin(ImportExportMixin, BaseUserAdmin):
    # The forms to add and change user instances
    form = UserChangeForm
    add_form = UserCreationForm

    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    list_display = ('username', 'email', 'is_staff', 'is_active', 'is_superuser', 'last_login', 'date_joined')
    list_filter = ('is_superuser', 'is_active',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('username',)}),
        (_('Permissions'), {'fields': ('is_staff', 'is_active', 'is_superuser', 'rebs_manager', 'work_manager')}),
    )
    # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2')}
         ),
    )
    search_fields = ('email', 'username')
    ordering = ('-date_joined',)
    filter_horizontal = ()
    # inlines = (StaffAuthInline, ProfileInline, TodosInline)


class ScrapeAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('pk', 'user', 'post', 'title', 'created')
    list_display_links = ('user', 'post')


# Now register the new UserAdmin...
admin.site.register(User, UserAdmin)
admin.site.register(Scrape, ScrapeAdmin)
