from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from experiences.models import Person, GuardianStudent
from django.contrib.auth.models import User
from django.contrib import messages
from .forms import ProfilePictureForm, UserRegistrationForm

class AccountDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        try:
            # Get the user's person profile
            person = user.person
            context['person'] = person
            context['profile_exists'] = True
            
            # Get the user's students if they're a guardian
            context['students'] = person.students.all()
            
            # Get relationship information for each student
            student_relationships = {}
            for student in context['students']:
                relationship = GuardianStudent.objects.get(guardian=person, student=student)
                student_relationships[student.id] = relationship.relationship
                
            context['student_relationships'] = student_relationships
            
            # Get guardian information if the user is a student
            context['guardians'] = person.guardians.all()
            
            # Get relationship information for each guardian
            guardian_relationships = {}
            for guardian in context['guardians']:
                relationship = GuardianStudent.objects.get(guardian=guardian, student=person)
                guardian_relationships[guardian.id] = relationship.relationship
                
            context['guardian_relationships'] = guardian_relationships
            
            # Get participation data
            context['participations'] = person.participation_set.all()
            
        except Person.DoesNotExist:
            context['profile_exists'] = False
            
        return context

def register_view(request):
    """View for registering a new user"""
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
        
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, "Your account has been created successfully! You can now log in.")
            return redirect('login')
    else:
        form = UserRegistrationForm()
        
    return render(request, 'registration/register.html', {'form': form})

@login_required
def profile_view(request):
    """View for displaying and updating the user's profile"""
    try:
        person = request.user.person
        
        if request.method == 'POST':
            form = ProfilePictureForm(request.POST, request.FILES, instance=person)
            if form.is_valid():
                form.save()
                messages.success(request, "Profile picture updated successfully!")
                return redirect('accounts:profile')
        else:
            form = ProfilePictureForm(instance=person)
            
        return render(request, 'accounts/profile.html', {
            'person': person,
            'form': form
        })
        
    except Person.DoesNotExist:
        # User doesn't have a person profile yet
        return redirect('accounts:create_profile')

@login_required
def create_profile_view(request):
    """View for creating a new profile if one doesn't exist"""
    # This is a placeholder for now
    return render(request, 'accounts/create_profile.html')
