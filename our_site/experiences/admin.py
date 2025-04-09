from django.contrib import admin
from django.utils.html import format_html
from .models import *
from django.core.cache import cache
from django import forms
from django.shortcuts import render
from django.urls import path
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


class CsvImportForm(forms.Form):
    csv_file = forms.FileField(
        label='Select a CSV file',
        help_text='The file should have guardian_email, student_email, relationship columns'
    )
    create_users = forms.BooleanField(
        label='Create new users if not found',
        required=False,
        initial=True,
        help_text='If checked, will create new users with random passwords for emails not found in the system'
    )


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
        my_urls = [
            path('import-csv/', self.import_csv, name='import-guardians-csv'),
            path('download-results/', self.download_results, name='download-import-results'),
            path('import-people/', self.import_people_csv, name='import-people-csv'),
        ]
        return my_urls + urls

    def download_results(self, request):
        """Download the import results as a CSV file"""
        if not request.session.get('import_results'):
            self.message_user(request, "No import results to download", level=messages.ERROR)
            return HttpResponseRedirect("../")
            
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="new_users.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Email', 'Full Name', 'Username', 'Password', 'Role'])
        
        for result in request.session.get('import_results', []):
            writer.writerow([
                result.get('email', ''),
                result.get('full_name', ''),
                result.get('username', ''),
                result.get('password', ''),
                result.get('role', '')
            ])
            
        return response

    def import_csv(self, request):
        if request.method == "POST":
            try:
                csv_file = TextIOWrapper(request.FILES["csv_file"].file, encoding='utf-8')
                reader = csv.DictReader(csv_file)
                create_users = 'create_users' in request.POST
                
                # Validate CSV headers
                required_fields = ['guardian_email', 'student_email', 'relationship']
                missing_fields = [field for field in required_fields if field not in reader.fieldnames]
                if missing_fields:
                    raise ValidationError(f'Missing required fields in CSV: {", ".join(missing_fields)}')

                # Process each row
                success_count = 0
                error_messages = []
                new_users = []
                default_role = None
                
                try:
                    # Try to get a default student role
                    default_role = Role.objects.get(title__icontains='student')
                except:
                    try:
                        # If no student role, get any role
                        default_role = Role.objects.first()
                    except:
                        pass
                
                for row in reader:
                    try:
                        # Process guardian
                        guardian = None
                        try:
                            guardian_user = User.objects.get(email=row['guardian_email'])
                            guardian = Person.objects.get(user=guardian_user)
                        except User.DoesNotExist:
                            if create_users:
                                # Create new user for guardian
                                password = generate_password()
                                guardian_email = row['guardian_email']
                                username = guardian_email.split('@')[0]
                                
                                # Ensure unique username
                                base_username = username
                                count = 1
                                while User.objects.filter(username=username).exists():
                                    username = f"{base_username}{count}"
                                    count += 1
                                
                                # Create user
                                guardian_user = User.objects.create_user(
                                    username=username,
                                    email=guardian_email,
                                    password=password
                                )
                                guardian_user.first_name = row.get('guardian_first_name', '')
                                guardian_user.last_name = row.get('guardian_last_name', '')
                                guardian_user.save()
                                
                                # Create person
                                guardian = Person.objects.create(
                                    user=guardian_user,
                                    role=default_role
                                )
                                
                                # Add to new users list
                                new_users.append({
                                    'email': guardian_email,
                                    'username': username,
                                    'password': password,
                                    'full_name': guardian_user.get_full_name(),
                                    'role': 'Guardian'
                                })
                            else:
                                raise ValueError(f"Guardian with email {row['guardian_email']} not found")
                        except Person.DoesNotExist:
                            if create_users:
                                # Create person for existing user
                                guardian = Person.objects.create(
                                    user=guardian_user,
                                    role=default_role
                                )
                            else:
                                raise ValueError(f"Person object for user {guardian_user.username} not found")
                        
                        # Process student
                        student = None
                        try:
                            student_user = User.objects.get(email=row['student_email'])
                            student = Person.objects.get(user=student_user)
                        except User.DoesNotExist:
                            if create_users:
                                # Create new user for student
                                password = generate_password()
                                student_email = row['student_email']
                                username = student_email.split('@')[0]
                                
                                # Ensure unique username
                                base_username = username
                                count = 1
                                while User.objects.filter(username=username).exists():
                                    username = f"{base_username}{count}"
                                    count += 1
                                
                                # Create user
                                student_user = User.objects.create_user(
                                    username=username,
                                    email=student_email,
                                    password=password
                                )
                                student_user.first_name = row.get('student_first_name', '')
                                student_user.last_name = row.get('student_last_name', '')
                                student_user.save()
                                
                                # Create person
                                student = Person.objects.create(
                                    user=student_user,
                                    role=default_role,
                                    graduating_year=row.get('graduating_year', None)
                                )
                                
                                # Add to new users list
                                new_users.append({
                                    'email': student_email,
                                    'username': username,
                                    'password': password,
                                    'full_name': student_user.get_full_name(),
                                    'role': 'Student'
                                })
                            else:
                                raise ValueError(f"Student with email {row['student_email']} not found")
                        except Person.DoesNotExist:
                            if create_users:
                                # Create person for existing user
                                student = Person.objects.create(
                                    user=student_user,
                                    role=default_role,
                                    graduating_year=row.get('graduating_year', None)
                                )
                            else:
                                raise ValueError(f"Person object for user {student_user.username} not found")

                        # Create or update relationship
                        relationship, created = GuardianStudent.objects.get_or_create(
                            guardian=guardian,
                            student=student,
                            defaults={
                                'relationship': row['relationship'],
                                'notes': row.get('notes', ''),
                                'is_active': True
                            }
                        )

                        if not created and not relationship.is_active:
                            relationship.is_active = True
                            relationship.relationship = row['relationship']
                            if 'notes' in row:
                                relationship.notes = row['notes']
                            relationship.save()

                        success_count += 1

                    except Exception as e:
                        error_messages.append(f'Row {reader.line_num}: Error - {str(e)}')

                # Show results
                if success_count:
                    self.message_user(request, f'Successfully processed {success_count} relationships')
                
                for error in error_messages:
                    self.message_user(request, error, level=messages.WARNING)
                
                # Store import results in session for download
                request.session['import_results'] = new_users
                
                # If we have new users, show the results page
                if new_users:
                    context = {'new_users': new_users}
                    return render(request, "admin/import_results.html", context)
                
                return HttpResponseRedirect("../")
                
            except Exception as e:
                self.message_user(request, f'Error processing CSV file: {str(e)}', level=messages.ERROR)
                return HttpResponseRedirect("../")

        form = CsvImportForm()
        payload = {"form": form}
        return render(request, "admin/csv_form.html", payload)

    def import_people_csv(self, request):
        """Import people from a CSV file"""
        if request.method == "POST":
            try:
                csv_file = TextIOWrapper(request.FILES["csv_file"].file, encoding='utf-8')
                reader = csv.DictReader(csv_file)
                create_users = 'create_users' in request.POST
                
                # Validate CSV headers
                required_fields = ['email', 'role']
                missing_fields = [field for field in required_fields if field not in reader.fieldnames]
                if missing_fields:
                    raise ValidationError(f'Missing required fields in CSV: {", ".join(missing_fields)}')
                
                # Validate that all roles exist
                all_roles = set(Role.objects.values_list('title', flat=True))
                
                # Process each row
                success_count = 0
                error_messages = []
                new_users = []
                
                for row in reader:
                    try:
                        if not row['email'] or not row['role']:
                            raise ValidationError(f"Row {reader.line_num}: Email and role are required fields")
                            
                        # Validate role
                        role_title = row['role'].strip()
                        if role_title not in all_roles:
                            raise ValidationError(f"Row {reader.line_num}: Role '{role_title}' does not exist")
                            
                        try:
                            role = Role.objects.get(title=role_title)
                        except Role.DoesNotExist:
                            raise ValidationError(f"Row {reader.line_num}: Role '{role_title}' does not exist")
                        
                        # Check if user already exists
                        email = row['email'].strip().lower()
                        try:
                            user = User.objects.get(email=email)
                            # User exists, check if person exists
                            try:
                                person = Person.objects.get(user=user)
                                # Update person if they exist
                                person.role = role
                                if 'graduating_year' in row and row['graduating_year']:
                                    try:
                                        person.graduating_year = int(row['graduating_year'])
                                    except ValueError:
                                        error_messages.append(f"Row {reader.line_num}: Invalid graduating year '{row['graduating_year']}'")
                                person.save()
                                success_count += 1
                            except Person.DoesNotExist:
                                # Create new person record for existing user
                                person = Person.objects.create(
                                    user=user,
                                    role=role,
                                    graduating_year=int(row['graduating_year']) if row.get('graduating_year') else None
                                )
                                success_count += 1
                        except User.DoesNotExist:
                            if create_users:
                                # Create a new user and person
                                password = generate_password()
                                
                                # Create username from email or first/last name
                                if 'first_name' in row and 'last_name' in row and row['first_name'] and row['last_name']:
                                    base_username = f"{row['first_name'].lower()}.{row['last_name'].lower()}"
                                else:
                                    base_username = email.split('@')[0]
                                
                                # Ensure username is unique
                                username = base_username
                                count = 1
                                while User.objects.filter(username=username).exists():
                                    username = f"{base_username}{count}"
                                    count += 1
                                
                                # Create user
                                user = User.objects.create_user(
                                    username=username,
                                    email=email,
                                    password=password
                                )
                                
                                # Add first and last name if provided
                                if 'first_name' in row:
                                    user.first_name = row['first_name']
                                if 'last_name' in row:
                                    user.last_name = row['last_name']
                                user.save()
                                
                                # Create person
                                person = Person.objects.create(
                                    user=user,
                                    role=role,
                                    graduating_year=int(row['graduating_year']) if row.get('graduating_year') else None,
                                )
                                
                                # Add to new users list
                                new_users.append({
                                    'email': email,
                                    'username': username,
                                    'password': password,
                                    'full_name': user.get_full_name() or username,
                                    'role': role_title
                                })
                                
                                success_count += 1
                            else:
                                raise ValidationError(f"Row {reader.line_num}: User with email {email} not found and create_users is not enabled")
                    
                    except Exception as e:
                        error_messages.append(f'Row {reader.line_num}: Error - {str(e)}')
                
                # Show results
                if success_count:
                    self.message_user(request, f'Successfully processed {success_count} people')
                
                for error in error_messages:
                    self.message_user(request, error, level=messages.WARNING)
                
                # Store import results in session for download
                request.session['import_results'] = new_users
                
                # If we have new users, show the results page
                if new_users:
                    context = {'new_users': new_users}
                    return render(request, "admin/import_results.html", context)
                
                return HttpResponseRedirect("../")
            
            except Exception as e:
                self.message_user(request, f'Error processing CSV file: {str(e)}', level=messages.ERROR)
                return HttpResponseRedirect("../")
        
        form = CsvImportForm()
        # Change the help text for the form
        form.fields['csv_file'].help_text = 'The file should have email and role columns. Optional columns: first_name, last_name, graduating_year'
        payload = {
            "form": form,
            "title": "Import People from CSV"
        }
        return render(request, "admin/people_csv_form.html", payload)

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