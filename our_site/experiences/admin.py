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
                '✓&NonBreakingSpace;Public</span>'
            )
        return format_html(
            '<span style="background-color: #dc3545; color: white; padding: 3px 10px; border-radius: 10px;">'
            '✕&NonBreakingSpace;Private</span>'
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


class GuardianStudentInline(admin.TabularInline):
    model = GuardianStudent
    fk_name = 'student'
    extra = 1
    verbose_name = "Guardian"
    verbose_name_plural = "Guardians"


class StudentGuardianInline(admin.TabularInline):
    model = GuardianStudent
    fk_name = 'guardian'
    extra = 1
    verbose_name = "Student"
    verbose_name_plural = "Students"


@admin.register(GuardianStudent)
class GuardianStudentAdmin(admin.ModelAdmin):
    list_display = ('guardian', 'relationship', 'student', 'is_active', 'date_added')
    list_filter = ('is_active', 'relationship', 'date_added')
    search_fields = ('guardian__user__username', 'guardian__user__first_name', 'guardian__user__last_name',
                    'student__user__username', 'student__user__first_name', 'student__user__last_name')
    raw_id_fields = ('guardian', 'student')
    date_hierarchy = 'date_added'

    def has_change_permission(self, request, obj=None):
        if not obj:  # This is the list view
            return True
        # Superusers can edit anything
        if request.user.is_superuser:
            return True
        # Administrators can edit any relationship
        if request.user.groups.filter(name='Administrators').exists():
            return True
        # Guardians can edit their own relationships
        return obj and (obj.guardian.user == request.user or obj.student.user == request.user)

    def has_delete_permission(self, request, obj=None):
        if not obj:  # This is the list view
            return True
        # Only superusers and administrators can delete
        return request.user.is_superuser or request.user.groups.filter(name='Administrators').exists()


@admin.register(Person)
class PersonAdmin(VisibilityModelAdmin):
    @admin.display(description='Full Name')
    def get_full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username

    @admin.display(description='Guardians')
    def get_guardians(self, obj):
        guardians = obj.guardians.all()
        if not guardians:
            return "-"
        return ", ".join([str(g) for g in guardians])

    @admin.display(description='Students')
    def get_students(self, obj):
        students = obj.students.all()
        if not students:
            return "-"
        return ", ".join([str(s) for s in students])

    list_display = ('get_full_name', 'visibility_badge', 'graduating_year', 'role', 'is_active', 
                   'get_participations', 'get_guardians', 'get_students', 'last_modified')
    list_filter = ('is_public', 'role', 'user__is_active', 'graduating_year', 
                  'guardian_relationships__is_active', 'student_relationships__is_active')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 
                    'guardian_relationships__student__user__username',
                    'student_relationships__guardian__user__username')
    fields = ('user', 'graduating_year', 'role', 'profile_picture', 'is_public')
    inlines = [ParticipationInline, GuardianStudentInline, StudentGuardianInline]

    def is_active(self, obj):
        return obj.user.is_active
    is_active.boolean = True

    def has_change_permission(self, request, obj=None):
        if not obj:  # This is the list view
            return True
        # Superusers can edit anything
        if request.user.is_superuser:
            return True
        # Administrators can edit any person
        if request.user.groups.filter(name='Administrators').exists():
            return True
        # Users can edit their own profile
        return obj and obj.user == request.user

    def has_delete_permission(self, request, obj=None):
        if not obj:  # This is the list view
            return True
        # Only superusers and administrators can delete
        return request.user.is_superuser or request.user.groups.filter(name='Administrators').exists()

    def has_view_permission(self, request, obj=None):
        # Everyone with admin access can view
        return True

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if request.user.groups.filter(name='Administrators').exists():
            return qs
        # Regular users can only see their own profile
        return qs.filter(user=request.user)

    def save_model(self, request, obj, form, change):
        if not change:  # This is a new object
            if not request.user.is_superuser and not request.user.groups.filter(name='Administrators').exists():
                obj.user = request.user  # Force the user to be the current user
        super().save_model(request, obj, form, change)

    def get_readonly_fields(self, request, obj=None):
        if not request.user.is_superuser and not request.user.groups.filter(name='Administrators').exists():
            return ('user',)  # Regular users can't change the user field
        return super().get_readonly_fields(request, obj)


@admin.register(Group)
class GroupAdmin(VisibilityModelAdmin):
    list_display = ('name', 'visibility_badge', 'description', 'core_competency_1', 'core_competency_2', 'core_competency_3', 'last_modified')
    search_fields = ('name', 'description')
    list_filter = ('is_public', 'core_competency_1', 'core_competency_2', 'core_competency_3')
    filter_horizontal = ('members',)
    inlines = [ParticipationInline]

    def has_view_permission(self, request, obj=None):
        # Everyone can view all groups
        return True

    def has_change_permission(self, request, obj=None):
        if not obj:  # This is the list view
            return True
        # Superusers can edit anything
        if request.user.is_superuser:
            return True
        # Administrators can edit any group
        if request.user.groups.filter(name='Administrators').exists():
            return True
        # Check if the user is a facilitator and a member of this group
        try:
            person = request.user.person
            return person.role.title == 'Facilitator' and person in obj.members.all()
        except:
            return False

    def has_delete_permission(self, request, obj=None):
        if not obj:  # This is the list view
            return True
        # Only superusers and administrators can delete
        return request.user.is_superuser or request.user.groups.filter(name='Administrators').exists()

    def get_queryset(self, request):
        # Everyone can see all groups
        return super().get_queryset(request)


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