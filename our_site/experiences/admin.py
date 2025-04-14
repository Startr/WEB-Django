from django.contrib import admin
from django.utils.html import format_html
from .models import *
from django.core.cache import cache
from django import forms
from django.shortcuts import render
from django.urls import path, reverse
from django import forms
from django.contrib import messages
import csv
import random
import string
from io import TextIOWrapper, StringIO
from django.http import HttpResponseRedirect, HttpResponse
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.db.models import Case, When, Value, IntegerField
from .admin_widgets import YearSelectorWidget


class ParticipationInline(admin.TabularInline):
    model = Participation
    extra = 1  # Allows adding new participations directly from the Person admin page
    formfield_overrides = {
        models.JSONField: {'widget': YearSelectorWidget()},
    }
    
    def get_queryset(self, request):
        # Get the base queryset
        queryset = super().get_queryset(request)
        
        # Annotate queryset to prioritize Facilitators
        # This adds a 'sort_order' value: 1 for Facilitators, 2 for others
        return queryset.annotate(
            sort_order=Case(
                When(person__role__title='Facilitator', then=Value(1)),
                default=Value(2),
                output_field=IntegerField(),
            )
        ).order_by('sort_order', 'person__user__first_name', 'person__user__last_name')


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


class CSVUploadForm(forms.Form):
    csv_file = forms.FileField(label='CSV File')
    create_users = forms.BooleanField(required=False, label='Create new users')


def generate_password(length=10):
    """Generate a random pronounceable password"""
    vowels = 'aeiou'
    consonants = 'bcdfghjklmnpqrstvwxyz'
    first_part = ''.join(random.choice(consonants) + random.choice(vowels) for _ in range(length//2))
    number_part = ''.join(random.choice(string.digits) for _ in range(2))
    special_char = random.choice('!@#$%^&*')
    return first_part.capitalize() + number_part + special_char


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
    change_list_template = "admin/person_changelist.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('import-people-csv/', 
                 self.admin_site.admin_view(self.import_people_csv_view), 
                 name='experiences_person_import-people-csv'),
                 
            path('import-guardians-csv/', 
                 self.admin_site.admin_view(self.import_guardians_csv_view), 
                 name='experiences_person_import-guardians-csv'),
                 
            path('download-csv-template/', 
                 self.admin_site.admin_view(self.download_csv_template),
                 name='download_people_csv_template'),
                 
            path('download-guardian-csv-template/', 
                 self.admin_site.admin_view(self.download_guardian_csv_template),
                 name='download_guardian_csv_template'),
                 
            path('download-imported-users/', 
                 self.admin_site.admin_view(self.download_imported_users),
                 name='download_imported_users'),
        ]
        return custom_urls + urls
    
    def import_people_csv_view(self, request):
        """View to import people from CSV file."""
        if request.method == 'POST':
            form = CSVUploadForm(request.POST, request.FILES)
            if form.is_valid():
                csv_file = request.FILES['csv_file']
                create_users = form.cleaned_data['create_users']
                
                # Process the CSV file
                csv_file_wrapper = TextIOWrapper(csv_file.file, encoding='utf-8-sig')
                csv_reader = csv.DictReader(csv_file_wrapper)
                
                # Validate CSV structure
                required_fields = ['email', 'role']
                for field in required_fields:
                    if field not in csv_reader.fieldnames:
                        messages.error(request, f"CSV file missing required '{field}' column")
                        return HttpResponseRedirect(request.path)
                
                # Track results for display
                created_users = []
                updated_people = 0
                skipped_rows = 0
                errors = []
                
                # Process each row
                for row in csv_reader:
                    try:
                        # Check required fields
                        email = row.get('email', '').strip()
                        role_title = row.get('role', '').strip()
                        
                        if not email or not role_title:
                            errors.append(f"Row {csv_reader.line_num}: Missing required fields")
                            skipped_rows += 1
                            continue
                        
                        # Check if role exists
                        try:
                            role = Role.objects.get(title=role_title)
                        except Role.DoesNotExist:
                            errors.append(f"Row {csv_reader.line_num}: Role '{role_title}' does not exist")
                            skipped_rows += 1
                            continue
                        
                        # Get or create user
                        first_name = row.get('first_name', '').strip()
                        last_name = row.get('last_name', '').strip()
                        graduating_year = row.get('graduating_year', '').strip()
                        
                        try:
                            user = User.objects.get(email=email)
                            # Update existing user info if provided
                            if first_name and not user.first_name:
                                user.first_name = first_name
                            if last_name and not user.last_name:
                                user.last_name = last_name
                            user.save()
                            
                        except User.DoesNotExist:
                            if create_users:
                                # Create new user
                                username = email.split('@')[0]
                                # Make sure username is unique
                                base_username = username
                                counter = 1
                                while User.objects.filter(username=username).exists():
                                    username = f"{base_username}{counter}"
                                    counter += 1
                                    
                                # Generate password
                                password = generate_password()
                                
                                # Create user
                                user = User.objects.create_user(
                                    username=username,
                                    email=email,
                                    password=password,
                                    first_name=first_name,
                                    last_name=last_name
                                )
                                
                                created_users.append({
                                    'email': email,
                                    'username': username,
                                    'password': password,
                                    'name': f"{first_name} {last_name}".strip()
                                })
                            else:
                                errors.append(f"Row {csv_reader.line_num}: User with email '{email}' does not exist and create_users is not checked")
                                skipped_rows += 1
                                continue
                        
                        # Get or create person
                        person, created = Person.objects.get_or_create(
                            user=user,
                            defaults={
                                'role': role,
                                'graduating_year': graduating_year if graduating_year else None
                            }
                        )
                        
                        if not created:
                            # Update existing person
                            if graduating_year:
                                person.graduating_year = graduating_year
                            person.role = role
                            person.save()
                            updated_people += 1
                    
                    except Exception as e:
                        errors.append(f"Row {csv_reader.line_num}: {str(e)}")
                        skipped_rows += 1
                
                # Show results
                if created_users:
                    messages.success(request, f"Created {len(created_users)} new users")
                    
                    # Provide CSV download for created users
                    csv_output = StringIO()
                    csv_writer = csv.writer(csv_output)
                    csv_writer.writerow(['Username', 'Email', 'Password', 'Name'])
                    for user_data in created_users:
                        csv_writer.writerow([
                            user_data['username'], 
                            user_data['email'],
                            user_data['password'],
                            user_data['name']
                        ])
                    
                    # Store the CSV data in the session for download
                    request.session['user_import_csv'] = csv_output.getvalue()
                    
                    # Link to download the CSV
                    download_url = reverse('admin:download_imported_users')
                    messages.info(request, format_html(
                        'Download <a href="{}">user credentials CSV</a> to share with new users.', 
                        download_url
                    ))
                
                if updated_people > 0:
                    messages.success(request, f"Updated {updated_people} existing people")
                    
                if skipped_rows > 0:
                    messages.warning(request, f"Skipped {skipped_rows} rows due to errors")
                    
                for error in errors[:10]:  # Show first 10 errors
                    messages.error(request, error)
                    
                if len(errors) > 10:
                    messages.error(request, f"... and {len(errors) - 10} more errors")
                    
                return HttpResponseRedirect(reverse('admin:experiences_person_changelist'))
        else:
            form = CSVUploadForm()
            
        context = {
            'title': 'Import People from CSV',
            'form': form,
            'opts': self.model._meta,
        }
        return render(request, 'admin/people_csv_form.html', context)
    
    def import_guardians_csv_view(self, request):
        """View to import guardian-student relations from CSV file."""
        if request.method == 'POST':
            form = CSVUploadForm(request.POST, request.FILES)
            if form.is_valid():
                csv_file = request.FILES['csv_file']
                
                # Process the CSV file
                csv_file_wrapper = TextIOWrapper(csv_file.file, encoding='utf-8-sig')
                csv_reader = csv.DictReader(csv_file_wrapper)
                
                # Validate CSV structure
                required_fields = ['guardian_email', 'student_email', 'relationship']
                for field in required_fields:
                    if field not in csv_reader.fieldnames:
                        messages.error(request, f"CSV file missing required '{field}' column")
                        return HttpResponseRedirect(request.path)
                
                # Track results for display
                created_relations = 0
                skipped_rows = 0
                errors = []
                
                # Process each row
                for row in csv_reader:
                    try:
                        # Check required fields
                        guardian_email = row.get('guardian_email', '').strip()
                        student_email = row.get('student_email', '').strip()
                        relationship = row.get('relationship', '').strip()
                        
                        if not guardian_email or not student_email or not relationship:
                            errors.append(f"Row {csv_reader.line_num}: Missing required fields")
                            skipped_rows += 1
                            continue
                        
                        # Check if users exist
                        try:
                            guardian_user = User.objects.get(email=guardian_email)
                        except User.DoesNotExist:
                            errors.append(f"Row {csv_reader.line_num}: Guardian with email '{guardian_email}' not found")
                            skipped_rows += 1
                            continue
                            
                        try:
                            student_user = User.objects.get(email=student_email)
                        except User.DoesNotExist:
                            errors.append(f"Row {csv_reader.line_num}: Student with email '{student_email}' not found")
                            skipped_rows += 1
                            continue
                        
                        # Check if people exist
                        try:
                            guardian = Person.objects.get(user=guardian_user)
                        except Person.DoesNotExist:
                            errors.append(f"Row {csv_reader.line_num}: Guardian person record for '{guardian_email}' not found")
                            skipped_rows += 1
                            continue
                            
                        try:
                            student = Person.objects.get(user=student_user)
                        except Person.DoesNotExist:
                            errors.append(f"Row {csv_reader.line_num}: Student person record for '{student_email}' not found")
                            skipped_rows += 1
                            continue
                        
                        # Create or update the relationship
                        relation, created = GuardianStudent.objects.get_or_create(
                            guardian=guardian,
                            student=student,
                            defaults={'relationship': relationship}
                        )
                        
                        if not created:
                            relation.relationship = relationship
                            relation.save()
                        
                        created_relations += 1
                    
                    except Exception as e:
                        errors.append(f"Row {csv_reader.line_num}: {str(e)}")
                        skipped_rows += 1
                
                # Show results
                if created_relations > 0:
                    messages.success(request, f"Created/updated {created_relations} guardian-student relationships")
                    
                if skipped_rows > 0:
                    messages.warning(request, f"Skipped {skipped_rows} rows due to errors")
                    
                for error in errors[:10]:  # Show first 10 errors
                    messages.error(request, error)
                    
                if len(errors) > 10:
                    messages.error(request, f"... and {len(errors) - 10} more errors")
                    
                return HttpResponseRedirect(reverse('admin:experiences_guardianstulient_changelist'))
        else:
            form = CSVUploadForm()
            
        context = {
            'title': 'Import Guardian-Student Relations',
            'form': form,
            'opts': self.model._meta,
        }
        return render(request, 'admin/people_csv_form.html', context)
    
    def download_csv_template(self, request):
        """Provide a downloadable example CSV template."""
        csv_content = "email,role,first_name,last_name,graduating_year\n"
        csv_content += "john.doe@example.com,Student,John,Doe,2026\n"
        csv_content += "jane.smith@example.com,Facilitator,Jane,Smith,"
        
        response = HttpResponse(csv_content, content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="people_import_template.csv"'
        return response
    
    def download_guardian_csv_template(self, request):
        """Provide a downloadable guardian relationship CSV template."""
        csv_content = "guardian_email,student_email,relationship\n"
        csv_content += "parent@example.com,student@example.com,Parent\n"
        csv_content += "guardian@example.com,student@example.com,Guardian"
        
        response = HttpResponse(csv_content, content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="guardian_relationships_template.csv"'
        return response
    
    def download_imported_users(self, request):
        """Download CSV with user credentials for newly created users."""
        csv_data = request.session.get('user_import_csv', '')
        if not csv_data:
            messages.error(request, "No user data available for download")
            return HttpResponseRedirect(reverse('admin:experiences_person_changelist'))
        
        response = HttpResponse(csv_data, content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="imported_user_credentials.csv"'
        
        # Clear the session data
        del request.session['user_import_csv']
        
        return response

    def get_full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username

    def get_guardians(self, obj):
        guardians = obj.guardians.all()
        if not guardians:
            return "-"
        return ", ".join([str(g) for g in guardians])

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
        # Only superusers and administrators can delete
        if not obj:  # This is the list view
            return True
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
class GroupAdmin(VisibilityModelAdmin):                    # Provide CSV download for created users
    list_display = ('name', 'visibility_badge', 'get_facilitators', 'description', 'core_competency_1', 'core_competency_2', 'core_competency_3', 'last_modified')
    search_fields = ('name', 'description')
    list_filter = ('is_public', 'core_competency_1', 'core_competency_2', 'core_competency_3')
    filter_horizontal = ('members',)
    inlines = [ParticipationInline]

    @admin.display(description='Facilitators')
    def get_facilitators(self, obj):
        # Find all facilitators for this group
        facilitators = obj.members.filter(
            role__title='Facilitator', 
            participation__group=obj
        ).distinct()
        # Return a comma-separated list of facilitator names
        if facilitators.exists():
            return ", ".join([f.user.get_full_name() or f.user.username for f in facilitators])
        return "-"

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
        # Only superusers and administrators can delete
        if not obj:  # This is the list view
            return True
        return request.user.is_superuser or request.user.groups.filter(name='Administrators').exists()


@admin.register(Participation)                
class ParticipationAdmin(admin.ModelAdmin):
    list_display = ('person', 'group', 'hours', 'special_recognition', 'years_display', 'elementary', 'high')
    list_filter = ('elementary', 'high', 'group')
    search_fields = ('person__user__username', 'group__name')
    formfield_overrides = {
        models.JSONField: {'widget': YearSelectorWidget()},
    }
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


@admin.register(ModelVisibilitySettings)
class ModelVisibilitySettingsAdmin(admin.ModelAdmin):
    list_display = ('model_name', 'access_level', 'last_modified', 'modified_by')
    list_filter = ('access_level',)
    readonly_fields = ('last_modified', 'modified_by')

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        obj.modified_by = request.user
        cache.delete(f'model_visibility_{obj.model_name}')  # Clear cache on save

@admin.register(Badges)
class BadgesAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('title', 'description')