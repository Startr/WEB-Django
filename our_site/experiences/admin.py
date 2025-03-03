from django.contrib import admin
from django.utils.html import format_html
from .models import *
from django.core.cache import cache


class ParticipationInline(admin.TabularInline):
    model = Participation
    extra = 1  # Allows adding new participations directly from the Person admin page


class VisibilityModelAdmin(admin.ModelAdmin):
    list_display = ('get_name', 'visibility_badge', 'last_modified')
    list_filter = ('is_public',)
    actions = ['make_public', 'make_private']
    
    def get_name(self, obj):
        return str(obj)
    get_name.short_description = 'Name'
    
    def visibility_badge(self, obj):
        if obj.is_public:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 10px; border-radius: 10px;">'
                '✓ Public</span>'
            )
        return format_html(
            '<span style="background-color: #dc3545; color: white; padding: 3px 10px; border-radius: 10px;">'
            '✕ Private</span>'
        )
    visibility_badge.short_description = 'Visibility'
    
    def make_public(self, request, queryset):
        updated = queryset.update(is_public=True)
        self.message_user(request, f'{updated} items are now public.')
    make_public.short_description = "Make selected items public"
    
    def make_private(self, request, queryset):
        updated = queryset.update(is_public=False)
        self.message_user(request, f'{updated} items are now private.')
    make_private.short_description = "Make selected items private"


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active', 'description')
    list_filter = ('is_active',)
    search_fields = ('title',)


@admin.register(Person)
class PersonAdmin(VisibilityModelAdmin):
    @admin.display(description='Full Name')
    def get_full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username

    list_display = ('get_full_name', 'visibility_badge', 'graduating_year', 'role', 'is_active', 'get_participations', 'last_modified')
    list_filter = ('is_public', 'role', 'user__is_active', 'graduating_year')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    fields = ('user', 'graduating_year', 'role', 'profile_picture', 'is_public')
    inlines = [ParticipationInline]

    def is_active(self, obj):
        return obj.user.is_active
    is_active.boolean = True  # Display as a boolean icon in the admin


@admin.register(Group)
class GroupAdmin(VisibilityModelAdmin):
    list_display = ('name', 'visibility_badge', 'description', 'core_competency_1', 'core_competency_2', 'core_competency_3', 'last_modified')
    search_fields = ('name', 'description')
    list_filter = ('is_public', 'core_competency_1', 'core_competency_2', 'core_competency_3')
    filter_horizontal = ('members',)
    inlines = [ParticipationInline]


@admin.register(Participation)
class ParticipationAdmin(admin.ModelAdmin):
    list_display = ('person', 'group', 'hours', 'special_recognition', 'years_display', 'elementary', 'high')
    list_filter = ('elementary', 'high', 'group')
    search_fields = ('person__user__username', 'group__name')

    def years_display(self, obj):
        return ", ".join(map(str, obj.years))
    years_display.short_description = "Years"


@admin.register(CoreCompetency)
class CoreCompetencyAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active', 'description')
    list_filter = ('is_active',)
    search_fields = ('title',)


@admin.register(Theme)
class ThemeAdmin(admin.ModelAdmin):
    list_display = ('group', 'font_choices', 'color_palette', 'logo', 'background_image')
    search_fields = ('group__name',)


@admin.register(Pathways)
class PathwaysAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('title', 'description')

@admin.register(Badges)
class BadgesAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('title', 'description')

@admin.register(ModelVisibilitySettings)
class ModelVisibilitySettingsAdmin(admin.ModelAdmin):
    list_display = ('model_name', 'access_level', 'last_modified', 'modified_by')
    list_filter = ('access_level',)
    readonly_fields = ('last_modified', 'modified_by')
    
    def save_model(self, request, obj, form, change):
        obj.modified_by = request.user
        cache.delete(f'model_visibility_{obj.model_name}')  # Clear cache on save
        super().save_model(request, obj, form, change)

    def has_delete_permission(self, request, obj=None):
        return False  # Prevent deletion of visibility settings