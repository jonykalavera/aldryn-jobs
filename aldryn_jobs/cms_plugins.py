# -*- coding: utf-8 -*-
from django.utils.translation import ugettext_lazy as _

from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool

from .models import (
    JobListPlugin, JobNewsletterRegistrationPlugin, JobCategoriesPlugin
)
from .forms import NewsletterSignupForm, JobListPluginForm


class JobCategoriesList(CMSPluginBase):
    model = JobCategoriesPlugin
    module = 'Jobs'
    name = _('Categories list')
    render_template = 'aldryn_jobs/plugins/categories_list.html'


class JobList(CMSPluginBase):
    form = JobListPluginForm
    model = JobListPlugin
    module = "Jobs"
    name = _('Job List')
    render_template = 'aldryn_jobs/plugins/latest_entries.html'


class JobNewsletter(CMSPluginBase):
    module = 'Jobs'
    render_template = 'aldryn_jobs/plugins/newsletter_registration.html'
    name = _('Form for Newsletter')
    model = JobNewsletterRegistrationPlugin

    def render(self, context, instance, placeholder):
        context = super(JobNewsletter, self).render(context, instance,
                                                    placeholder)
        # if there is data for form (i.e validation errors) render that
        # form with data. explicitly check that request POST has the right
        # data.
        request = context.get('request')
        if request is not None and request.POST.get('recipient'):
            context['form'] = NewsletterSignupForm(request.POST)
        else:
            context['form'] = NewsletterSignupForm()
        return context


plugin_pool.register_plugin(JobCategoriesList)
plugin_pool.register_plugin(JobList)
plugin_pool.register_plugin(JobNewsletter)
