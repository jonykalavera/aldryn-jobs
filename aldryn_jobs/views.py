# -*- coding: utf-8 -*-
from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect
from django.utils.translation import pgettext_lazy as _, get_language_from_request
from django.views.generic import DetailView, ListView

from aldryn_jobs import request_job_offer_identifier
from aldryn_jobs.forms import JobApplicationForm
from aldryn_jobs.models import JobCategory, JobOffer
from menus.utils import set_language_changer


class JobOfferList(ListView):

    template_name = 'aldryn_jobs/jobs_list.html'

    def get_queryset(self):
        # have to be a method, so the language isn't cached
        language = get_language_from_request(self.request)
        return (
            JobOffer.active.language(language)
                           .translated(language)
                           .select_related('category')
                           .order_by('category__id')
        )


class CategoryJobOfferList(JobOfferList):

    def get_queryset(self):
        qs = super(CategoryJobOfferList, self).get_queryset()
        language = get_language_from_request(self.request)

        category_slug = self.kwargs['category_slug']
        try:
            category = (
                JobCategory.objects.language(language)
                                   .translated(language, slug=category_slug)
                                   .get()
            )
        except JobCategory.DoesNotExist:
            raise Http404

        self.set_language_changer(category=category)
        return qs.filter(category=category)

    def set_language_changer(self, category):
        """Translate the slug while changing the language."""
        set_language_changer(self.request, category.get_absolute_url)


class JobOfferDetail(DetailView):
    form_class = JobApplicationForm
    template_name = 'aldryn_jobs/jobs_detail.html'
    slug_url_kwarg = 'job_offer_slug'

    def dispatch(self, request, *args, **kwargs):
        self.request = request
        self.object = self.get_object()
        return super(JobOfferDetail, self).dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()
        slug = self.kwargs.get(self.slug_url_kwarg, None)
        slug_field = self.get_slug_field()
        language = get_language_from_request(self.request)
        queryset = (
            queryset.language(language)
                    .translated(language, **{slug_field: slug})
        )

        job_offer = queryset.get()
        if not job_offer and not job_offer.get_active() and not self.request.user.is_staff:
            raise Http404(_(
                'aldryn-jobs', 'Offer is not longer valid.'
            ))
        setattr(self.request, request_job_offer_identifier, job_offer)
        self.set_language_changer(job_offer=job_offer)
        return job_offer

    def get_form_class(self):
        return self.form_class

    def get_form_kwargs(self):
        """
        Returns the keyword arguments for instantiating the form.
        """
        kwargs = {'job_offer': self.object}

        if self.request.method in ('POST', 'PUT'):
            kwargs.update({
                'data': self.request.POST,
                'files': self.request.FILES,
            })
        return kwargs

    def get_form(self, form_class):
        """
        Returns an instance of the form to be used in this view.
        """
        return form_class(**self.get_form_kwargs())

    def get_queryset(self):
        # not active as well, see `get_object` for more detail
        language = get_language_from_request(self.request)
        return (
            JobOffer.objects.language(language)
                            .translated(language)
                            .select_related('category')
        )

    def set_language_changer(self, job_offer):
        """Translate the slug while changing the language."""
        set_language_changer(self.request, job_offer.get_absolute_url)

    def get(self, *args, **kwargs):
        form_class = self.get_form_class()
        self.form = self.get_form(form_class)
        return super(JobOfferDetail, self).get(*args, **kwargs)

    def post(self, *args, **kwargs):
        """Handles application for the job."""

        if not self.object.can_apply:
            messages.success(
                self.request,
                _('aldryn-jobs', 'You can\'t apply for this job.')
            )
            return redirect(self.object.get_absolute_url())

        form_class = self.get_form_class()
        self.form = self.get_form(form_class)

        if self.form.is_valid():
            self.form.save()
            msg = (
                _('aldryn-jobs', 'You have successfully applied for %(job)s.')
                % {'job': self.object.title}
            )
            messages.success(self.request, msg)
            return redirect(self.object.get_absolute_url())
        else:
            return super(JobOfferDetail, self).get(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(JobOfferDetail, self).get_context_data(**kwargs)
        context['form'] = self.form
        return context
