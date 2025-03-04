from django import forms
from .models import Role, Person, Group, Participation, CoreCompetency, Theme, Badges, Pathways


class RoleForm(forms.ModelForm):

    class Meta:
        model = Role
        fields = ['title', 'description', 'is_active']
        exclude = []
        widgets = None
        localized_fields = None
        labels = {}
        help_texts = {}
        error_messages = {}

    def __init__(self, *args, **kwargs):
        return super(RoleForm, self).__init__(*args, **kwargs)

    def is_valid(self):
        return super(RoleForm, self).is_valid()

    def full_clean(self):
        return super(RoleForm, self).full_clean()

    def clean_title(self):
        title = self.cleaned_data.get("title", None)
        return title

    def clean_description(self):
        description = self.cleaned_data.get("description", None)
        return description

    def clean_is_active(self):
        is_active = self.cleaned_data.get("is_active", None)
        return is_active

    def clean(self):
        return super(RoleForm, self).clean()

    def validate_unique(self):
        return super(RoleForm, self).validate_unique()

    def save(self, commit=True):
        return super(RoleForm, self).save(commit)


class PersonForm(forms.ModelForm):

    class Meta:
        model = Person
        fields = ['user', 'profile_picture', 'role']
        exclude = []
        widgets = None
        localized_fields = None
        labels = {}
        help_texts = {}
        error_messages = {}

    def __init__(self, *args, **kwargs):
        return super(PersonForm, self).__init__(*args, **kwargs)

    def is_valid(self):
        return super(PersonForm, self).is_valid()

    def full_clean(self):
        return super(PersonForm, self).full_clean()

    def clean_user(self):
        user = self.cleaned_data.get("user", None)
        return user

    def clean_profile_picture(self):
        profile_picture = self.cleaned_data.get("profile_picture", None)
        return profile_picture

    def clean_role(self):
        role = self.cleaned_data.get("role", None)
        return role

    def clean(self):
        return super(PersonForm, self).clean()

    def validate_unique(self):
        return super(PersonForm, self).validate_unique()

    def save(self, commit=True):
        return super(PersonForm, self).save(commit)


class GroupForm(forms.ModelForm):

    class Meta:
        model = Group
        fields = ['name', 'description', 'core_competency_1', 'core_competency_2', 'core_competency_3']
        exclude = []
        widgets = None
        localized_fields = None
        labels = {}
        help_texts = {}
        error_messages = {}

    def __init__(self, *args, **kwargs):
        return super(GroupForm, self).__init__(*args, **kwargs)

    def is_valid(self):
        return super(GroupForm, self).is_valid()

    def full_clean(self):
        return super(GroupForm, self).full_clean()

    def clean_name(self):
        name = self.cleaned_data.get("name", None)
        return name

    def clean_description(self):
        description = self.cleaned_data.get("description", None)
        return description

    def clean_core_competency_1(self):
        core_competency_1 = self.cleaned_data.get("core_competency_1", None)
        return core_competency_1

    def clean_core_competency_2(self):
        core_competency_2 = self.cleaned_data.get("core_competency_2", None)
        return core_competency_2

    def clean_core_competency_3(self):
        core_competency_3 = self.cleaned_data.get("core_competency_3", None)
        return core_competency_3

    def clean(self):
        return super(GroupForm, self).clean()

    def validate_unique(self):
        return super(GroupForm, self).validate_unique()

    def save(self, commit=True):
        return super(GroupForm, self).save(commit)


class ParticipationForm(forms.ModelForm):

    class Meta:
        model = Participation
        fields = ['person', 'group', 'hours', 'special_recognition', 'years', 'elementary', 'high']
        exclude = []
        widgets = None
        localized_fields = None
        labels = {}
        help_texts = {}
        error_messages = {}

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(ParticipationForm, self).__init__(*args, **kwargs)
        
        # Restrict person choices based on user permissions
        if self.user and not (self.user.is_superuser or self.user.groups.filter(name='Administrators').exists()):
            try:
                # If not admin/superuser, only allow selecting themselves
                person = Person.objects.get(user=self.user)
                self.fields['person'].queryset = Person.objects.filter(id=person.id)
                self.fields['person'].initial = person
                self.fields['person'].widget.attrs['disabled'] = True  # Make it read-only
                self.fields['person'].required = False  # Not required in form since we'll set it in save
            except Person.DoesNotExist:
                # If no person record, empty queryset
                self.fields['person'].queryset = Person.objects.none()

    def is_valid(self):
        return super(ParticipationForm, self).is_valid()

    def full_clean(self):
        return super(ParticipationForm, self).full_clean()

    def clean_person(self):
        person = self.cleaned_data.get("person", None)
        
        # If the field is disabled, it won't be in cleaned_data, so we need to get it manually
        if not person and self.user and not (self.user.is_superuser or self.user.groups.filter(name='Administrators').exists()):
            try:
                person = Person.objects.get(user=self.user)
            except Person.DoesNotExist:
                raise forms.ValidationError("User profile not found.")
                
        return person

    def clean_group(self):
        group = self.cleaned_data.get("group", None)
        return group

    def clean_hours(self):
        hours = self.cleaned_data.get("hours", None)
        return hours

    def clean_special_recognition(self):
        special_recognition = self.cleaned_data.get("special_recognition", None)
        return special_recognition

    def clean_years(self):
        years = self.cleaned_data.get("years", None)
        return years

    def clean_elementary(self):
        elementary = self.cleaned_data.get("elementary", None)
        return elementary

    def clean_high(self):
        high = self.cleaned_data.get("high", None)
        return high

    def clean(self):
        return super(ParticipationForm, self).clean()

    def validate_unique(self):
        return super(ParticipationForm, self).validate_unique()

    def save(self, commit=True):
        instance = super(ParticipationForm, self).save(commit=False)
        
        # If person is None (because disabled field), set it
        if instance.person is None and self.user and not (self.user.is_superuser or self.user.groups.filter(name='Administrators').exists()):
            try:
                instance.person = Person.objects.get(user=self.user)
            except Person.DoesNotExist:
                pass
                
        if commit:
            instance.save()
            
        return instance


class CoreCompetencyForm(forms.ModelForm):

    class Meta:
        model = CoreCompetency
        fields = ['title', 'description', 'is_active']
        exclude = []
        widgets = None
        localized_fields = None
        labels = {}
        help_texts = {}
        error_messages = {}

    def __init__(self, *args, **kwargs):
        return super(CoreCompetencyForm, self).__init__(*args, **kwargs)

    def is_valid(self):
        return super(CoreCompetencyForm, self).is_valid()

    def full_clean(self):
        return super(CoreCompetencyForm, self).full_clean()

    def clean_title(self):
        title = self.cleaned_data.get("title", None)
        return title

    def clean_description(self):
        description = self.cleaned_data.get("description", None)
        return description

    def clean_is_active(self):
        is_active = self.cleaned_data.get("is_active", None)
        return is_active

    def clean(self):
        return super(CoreCompetencyForm, self).clean()

    def validate_unique(self):
        return super(CoreCompetencyForm, self).validate_unique()

    def save(self, commit=True):
        return super(CoreCompetencyForm, self).save(commit)


class ThemeForm(forms.ModelForm):

    class Meta:
        model = Theme
        fields = ['group', 'color_palette', 'font_choices', 'logo', 'background_image']
        exclude = []
        widgets = None
        localized_fields = None
        labels = {}
        help_texts = {}
        error_messages = {}

    def __init__(self, *args, **kwargs):
        return super(ThemeForm, self).__init__(*args, **kwargs)

    def is_valid(self):
        return super(ThemeForm, self).is_valid()

    def full_clean(self):
        return super(ThemeForm, self).full_clean()

    def clean_group(self):
        group = self.cleaned_data.get("group", None)
        return group

    def clean_color_palette(self):
        color_palette = self.cleaned_data.get("color_palette", None)
        return color_palette

    def clean_font_choices(self):
        font_choices = self.cleaned_data.get("font_choices", None)
        return font_choices

    def clean_logo(self):
        logo = self.cleaned_data.get("logo", None)
        return logo

    def clean_background_image(self):
        background_image = self.cleaned_data.get("background_image", None)
        return background_image

    def clean(self):
        return super(ThemeForm, self).clean()

    def validate_unique(self):
        return super(ThemeForm, self).validate_unique()

    def save(self, commit=True):
        return super(ThemeForm, self).save(commit)


class BadgesForm(forms.ModelForm):

    class Meta:
        model = Badges
        fields = ['title', 'description', 'is_active']
        exclude = []
        widgets = None
        localized_fields = None
        labels = {}
        help_texts = {}
        error_messages = {}

    def __init__(self, *args, **kwargs):
        return super(BadgesForm, self).__init__(*args, **kwargs)

    def is_valid(self):
        return super(BadgesForm, self).is_valid()

    def full_clean(self):
        return super(BadgesForm, self).full_clean()

    def clean_title(self):
        title = self.cleaned_data.get("title", None)
        return title

    def clean_description(self):
        description = self.cleaned_data.get("description", None)
        return description

    def clean_is_active(self):
        is_active = self.cleaned_data.get("is_active", None)
        return is_active

    def clean(self):
        return super(BadgesForm, self).clean()

    def validate_unique(self):
        return super(BadgesForm, self).validate_unique()

    def save(self, commit=True):
        return super(BadgesForm, self).save(commit)


class PathwaysForm(forms.ModelForm):

    class Meta:
        model = Pathways
        fields = ['title', 'description', 'core_competencies', 'groups', 'is_active']
        exclude = []
        widgets = None
        localized_fields = None
        labels = {}
        help_texts = {}
        error_messages = {}

    def __init__(self, *args, **kwargs):
        return super(PathwaysForm, self).__init__(*args, **kwargs)

    def is_valid(self):
        return super(PathwaysForm, self).is_valid()

    def full_clean(self):
        return super(PathwaysForm, self).full_clean()

    def clean_title(self):
        title = self.cleaned_data.get("title", None)
        return title

    def clean_description(self):
        description = self.cleaned_data.get("description", None)
        return description

    def clean_core_competencies(self):
        core_competencies = self.cleaned_data.get("core_competencies", None)
        return core_competencies

    def clean_groups(self):
        groups = self.cleaned_data.get("groups", None)
        return groups

    def clean_is_active(self):
        is_active = self.cleaned_data.get("is_active", None)
        return is_active

    def clean(self):
        return super(PathwaysForm, self).clean()

    def validate_unique(self):
        return super(PathwaysForm, self).validate_unique()

    def save(self, commit=True):
        return super(PathwaysForm, self).save(commit)    