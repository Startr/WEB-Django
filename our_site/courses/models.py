from django.db import models
from django.contrib.auth.models import User

class Person(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)  # Connects to the Django user model
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    role = models.CharField(max_length=20, choices=[('participant', 'Participant'), ('facilitator', 'Facilitator')])

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.role})"

    def is_active(self):
        """Returns True if the user is active based on their last login time."""
        return self.user.last_login >= timezone.now() - timezone.timedelta(days=30)


class Group(models.Model):
    name = models.CharField(max_length=100)
    members = models.ManyToManyField(Person)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Theme(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)  # Connects each theme to a group
    color_palette = models.JSONField()  # Stores color values
    font_choices = models.CharField(max_length=100)  # Specify the font choice
    logo = models.ImageField(upload_to='logos/', null=True, blank=True)
    background_image = models.ImageField(upload_to='backgrounds/', null=True, blank=True)

    def __str__(self):
        return f"Theme for {self.group.name}"
