from django.contrib import admin
from .models import *


class ParticipationInline(admin.TabularInline):
    model = Participation
    extra = 1  # Allows adding new participations directly from the Person admin page


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active', 'description')
    list_filter = ('is_active',)
    search_fields = ('title',)


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    @admin.display(description='Full Name')
    def get_full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username

    list_display = ('get_full_name', 'graduating_year', 'role', 'is_active', 'get_participations')
    list_filter = ('role', 'user__is_active', 'graduating_year')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    fields = ('user', 'graduating_year', 'role', 'profile_picture')
    inlines = [ParticipationInline]

    def is_active(self, obj):
        return obj.user.is_active
    is_active.boolean = True  # Display as a boolean icon in the admin


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'core_competency_1', 'core_competency_2', 'core_competency_3')
    search_fields = ('name', 'description')
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