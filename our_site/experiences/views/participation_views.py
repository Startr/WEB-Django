from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView
from ..models import Participation
from ..forms import ParticipationForm
from django.urls import reverse_lazy
from django.urls import reverse
from django.http import Http404


class ParticipationListView(ListView):
    model = Participation
    template_name = "experiences/participation_list.html"
    paginate_by = 20
    context_object_name = "participation_list"
    allow_empty = True
    page_kwarg = 'page'
    paginate_orphans = 0

    def __init__(self, **kwargs):
        return super(ParticipationListView, self).__init__(**kwargs)

    def dispatch(self, *args, **kwargs):
        return super(ParticipationListView, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        return super(ParticipationListView, self).get(request, *args, **kwargs)

    def get_queryset(self):
        return super(ParticipationListView, self).get_queryset()

    def get_allow_empty(self):
        return super(ParticipationListView, self).get_allow_empty()

    def get_context_data(self, *args, **kwargs):
        ret = super(ParticipationListView, self).get_context_data(*args, **kwargs)
        return ret

    def get_paginate_by(self, queryset):
        return super(ParticipationListView, self).get_paginate_by(queryset)

    def get_context_object_name(self, object_list):
        return super(ParticipationListView, self).get_context_object_name(object_list)

    def paginate_queryset(self, queryset, page_size):
        return super(ParticipationListView, self).paginate_queryset(queryset, page_size)

    def get_paginator(self, queryset, per_page, orphans=0, allow_empty_first_page=True):
        return super(ParticipationListView, self).get_paginator(queryset, per_page, orphans=0, allow_empty_first_page=True)

    def render_to_response(self, context, **response_kwargs):
        return super(ParticipationListView, self).render_to_response(context, **response_kwargs)

    def get_template_names(self):
        return super(ParticipationListView, self).get_template_names()


class ParticipationDetailView(DetailView):
    model = Participation
    template_name = "experiences/participation_detail.html"
    context_object_name = "participation"
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    pk_url_kwarg = 'pk'

    def __init__(self, **kwargs):
        return super(ParticipationDetailView, self).__init__(**kwargs)

    def dispatch(self, *args, **kwargs):
        return super(ParticipationDetailView, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        return super(ParticipationDetailView, self).get(request, *args, **kwargs)

    def get_object(self, queryset=None):
        return super(ParticipationDetailView, self).get_object(queryset)

    def get_queryset(self):
        return super(ParticipationDetailView, self).get_queryset()

    def get_slug_field(self):
        return super(ParticipationDetailView, self).get_slug_field()

    def get_context_data(self, **kwargs):
        ret = super(ParticipationDetailView, self).get_context_data(**kwargs)
        return ret

    def get_context_object_name(self, obj):
        return super(ParticipationDetailView, self).get_context_object_name(obj)

    def render_to_response(self, context, **response_kwargs):
        return super(ParticipationDetailView, self).render_to_response(context, **response_kwargs)

    def get_template_names(self):
        return super(ParticipationDetailView, self).get_template_names()


class ParticipationCreateView(CreateView):
    model = Participation
    form_class = ParticipationForm
    # fields = ['person', 'group', 'hours', 'special_recognition', 'years', 'elementary', 'high']
    template_name = "experiences/participation_create.html"
    success_url = reverse_lazy("participation_list")

    def __init__(self, **kwargs):
        return super(ParticipationCreateView, self).__init__(**kwargs)

    def dispatch(self, request, *args, **kwargs):
        return super(ParticipationCreateView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return super(ParticipationCreateView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return super(ParticipationCreateView, self).post(request, *args, **kwargs)

    def get_form_class(self):
        return super(ParticipationCreateView, self).get_form_class()

    def get_form(self, form_class=None):
        return super(ParticipationCreateView, self).get_form(form_class)

    def get_form_kwargs(self, **kwargs):
        return super(ParticipationCreateView, self).get_form_kwargs(**kwargs)

    def get_initial(self):
        return super(ParticipationCreateView, self).get_initial()

    def form_invalid(self, form):
        return super(ParticipationCreateView, self).form_invalid(form)

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.save()
        return super(ParticipationCreateView, self).form_valid(form)

    def get_context_data(self, **kwargs):
        ret = super(ParticipationCreateView, self).get_context_data(**kwargs)
        return ret

    def render_to_response(self, context, **response_kwargs):
        return super(ParticipationCreateView, self).render_to_response(context, **response_kwargs)

    def get_template_names(self):
        return super(ParticipationCreateView, self).get_template_names()

    def get_success_url(self):
        return reverse("experiences:participation_detail", args=(self.object.pk,))


class ParticipationUpdateView(UpdateView):
    model = Participation
    form_class = ParticipationForm
    # fields = ['person', 'group', 'hours', 'special_recognition', 'years', 'elementary', 'high']
    template_name = "experiences/participation_update.html"
    initial = {}
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    pk_url_kwarg = 'pk'
    context_object_name = "participation"

    def __init__(self, **kwargs):
        return super(ParticipationUpdateView, self).__init__(**kwargs)

    def dispatch(self, *args, **kwargs):
        return super(ParticipationUpdateView, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        return super(ParticipationUpdateView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return super(ParticipationUpdateView, self).post(request, *args, **kwargs)

    def get_object(self, queryset=None):
        return super(ParticipationUpdateView, self).get_object(queryset)

    def get_queryset(self):
        return super(ParticipationUpdateView, self).get_queryset()

    def get_slug_field(self):
        return super(ParticipationUpdateView, self).get_slug_field()

    def get_form_class(self):
        return super(ParticipationUpdateView, self).get_form_class()

    def get_form(self, form_class=None):
        return super(ParticipationUpdateView, self).get_form(form_class)

    def get_form_kwargs(self, **kwargs):
        return super(ParticipationUpdateView, self).get_form_kwargs(**kwargs)

    def get_initial(self):
        return super(ParticipationUpdateView, self).get_initial()

    def form_invalid(self, form):
        return super(ParticipationUpdateView, self).form_invalid(form)

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.save()
        return super(ParticipationUpdateView, self).form_valid(form)

    def get_context_data(self, **kwargs):
        ret = super(ParticipationUpdateView, self).get_context_data(**kwargs)
        return ret

    def get_context_object_name(self, obj):
        return super(ParticipationUpdateView, self).get_context_object_name(obj)

    def render_to_response(self, context, **response_kwargs):
        return super(ParticipationUpdateView, self).render_to_response(context, **response_kwargs)

    def get_template_names(self):
        return super(ParticipationUpdateView, self).get_template_names()

    def get_success_url(self):
        return reverse("experiences:participation_detail", args=(self.object.pk,))


class ParticipationDeleteView(DeleteView):
    model = Participation
    template_name = "experiences/participation_delete.html"
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    pk_url_kwarg = 'pk'
    context_object_name = "participation"

    def __init__(self, **kwargs):
        return super(ParticipationDeleteView, self).__init__(**kwargs)

    def dispatch(self, *args, **kwargs):
        return super(ParticipationDeleteView, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        raise Http404

    def post(self, request, *args, **kwargs):
        return super(ParticipationDeleteView, self).post(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return super(ParticipationDeleteView, self).delete(request, *args, **kwargs)

    def get_object(self, queryset=None):
        return super(ParticipationDeleteView, self).get_object(queryset)

    def get_queryset(self):
        return super(ParticipationDeleteView, self).get_queryset()

    def get_slug_field(self):
        return super(ParticipationDeleteView, self).get_slug_field()

    def get_context_data(self, **kwargs):
        ret = super(ParticipationDeleteView, self).get_context_data(**kwargs)
        return ret

    def get_context_object_name(self, obj):
        return super(ParticipationDeleteView, self).get_context_object_name(obj)

    def render_to_response(self, context, **response_kwargs):
        return super(ParticipationDeleteView, self).render_to_response(context, **response_kwargs)

    def get_template_names(self):
        return super(ParticipationDeleteView, self).get_template_names()

    def get_success_url(self):
        return reverse("experiences:participation_list")
