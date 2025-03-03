from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib import admin
from django.utils.html import format_html

class BaseVisibilityModel(models.Model):
    is_public = models.BooleanField(
        default=True,
        help_text="Controls whether this item is visible to the public"
    )
    last_modified = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True

class Role(models.Model):
    title = models.CharField(max_length=50, unique=True)  # Unique title for the role
    description = models.TextField(blank=True)  # Optional description of the role
    is_active = models.BooleanField(default=True)  # Whether this role is currently active

    def __str__(self):
        return f"{self.title} ({'Active' if self.is_active else 'Inactive'})"


class Person(BaseVisibilityModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)
    graduating_year = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.role.title if self.role else 'No Role'})"

    def is_active(self):
        """Returns True if the user is active based on their last login time."""
        return self.user.last_login >= timezone.now() - timezone.timedelta(days=30)

    @admin.display(description="Participation Details")
    def get_participations(self):
        """Returns a string representation of all participations."""
        participations = Participation.objects.filter(person=self)
        return ", ".join([f"{p.group.name} ({', '.join(map(str, p.years))})" for p in participations])

    class Meta:
        verbose_name_plural = "People"


class Group(BaseVisibilityModel):
    name = models.CharField(max_length=100)
    members = models.ManyToManyField('Person', through='Participation')
    description = models.TextField(blank=True)
    core_competency_1 = models.ForeignKey('CoreCompetency', on_delete=models.SET_NULL, null=True, blank=True, related_name='group_core_1')
    core_competency_2 = models.ForeignKey('CoreCompetency', on_delete=models.SET_NULL, null=True, blank=True, related_name='group_core_2')
    core_competency_3 = models.ForeignKey('CoreCompetency', on_delete=models.SET_NULL, null=True, blank=True, related_name='group_core_3')

    class Meta:
        verbose_name_plural = "Activity Groups"

    def __str__(self):
        return self.name


class Participation(models.Model):
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    hours = models.PositiveIntegerField(null=True, blank=True)  # Hours of participation
    special_recognition = models.TextField(blank=True, null=True)  # Optional special recognition
    years = models.JSONField(default=list)  # List of years they participated
    elementary = models.BooleanField(default=False)  # Elementary level participation
    high = models.BooleanField(default=False)  # High school level participation

    class Meta:
        verbose_name_plural = "All Activity Participation"

    def __str__(self):
        return f"{self.person} in {self.group} ({', '.join(map(str, self.years))})"


class CoreCompetency(models.Model):
    title = models.CharField(max_length=100, unique=True)  # Unique title for the competency
    description = models.TextField(blank=True)  # Optional description
    is_active = models.BooleanField(default=True)  # Whether the competency is active

    class Meta:
        verbose_name_plural = "Core Competencies"

    def __str__(self):
        return f"{self.title} ({'Active' if self.is_active else 'Inactive'})"


class Theme(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)  # Connects each theme to a group
    color_palette = models.JSONField()  # Stores color values
    font_choices = models.CharField(max_length=100)  # Specify the font choice
    logo = models.ImageField(upload_to='logos/', null=True, blank=True)
    background_image = models.ImageField(upload_to='backgrounds/', null=True, blank=True)

    def __str__(self):
        return f"Theme for {self.group.name}"


class Pathways(models.Model):
    title = models.CharField(max_length=100, unique=True)  # Unique title for the pathway
    description = models.TextField(blank=True)  # Optional description
    core_competencies = models.ManyToManyField(CoreCompetency)  # Connects to core competencies
    groups = models.ManyToManyField(Group)  # Connects to groups
    is_active = models.BooleanField(default=True)  # Whether the pathway is active

    class Meta:
        verbose_name_plural = "Pathways"

    def __str__(self):
        return self.title

    def long_title(self):
        return f"{self.title} (is made of {', '.join(map(str, self.core_competencies.all()))})"

class Badges(models.Model):
    title = models.CharField(max_length=100, unique=True)  # Unique title for the badge
    description = models.TextField(blank=True)  # Optional description
    image = models.ImageField(upload_to='badges/', null=True, blank=True)
    core_competencies = models.ManyToManyField(CoreCompetency)  # Connects to core competencies
    is_active = models.BooleanField(default=True)  # Whether the badge is active

    class Meta:
        verbose_name_plural = "Badges"

    def __str__(self):
        return self.title

    def image_tag(self):
        return format_html('<img src="{}" style="max-width: 100px; max-height: 100px;" />', self.image.url)

class ModelVisibilitySettings(models.Model):
    MODEL_CHOICES = [
        ('person', 'People'),
        ('group', 'Activity Groups'),
        ('participation', 'Participations'),
        ('role', 'Roles'),
        ('pathways', 'Pathways'),
        ('badges', 'Badges'),
    ]

    ACCESS_LEVELS = [
        ('public', 'Public - Anyone can view'),
        ('authenticated', 'Authenticated - Any logged in user'),
        ('staff', 'Staff Only'),
        ('disabled', 'Disabled - No access (404)'),
    ]

    model_name = models.CharField(
        max_length=50, 
        choices=MODEL_CHOICES,
        unique=True,
        help_text="Select which model's visibility to control"
    )
    access_level = models.CharField(
        max_length=20,
        choices=ACCESS_LEVELS,
        default='staff',
        help_text="Who can access this model's views"
    )
    last_modified = models.DateTimeField(auto_now=True)
    modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        verbose_name = "Model Visibility Setting"
        verbose_name_plural = "Model Visibility Settings"
        ordering = ['model_name']

    def __str__(self):
        return f"{self.get_model_name_display()} - {self.get_access_level_display()}"

    