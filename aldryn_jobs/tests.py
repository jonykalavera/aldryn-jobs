from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase

from cms import api
from cms.utils import get_cms_setting
from cms.test_utils.testcases import BaseCMSTestCase

from .cms_plugins import JobList
from .models import JobCategory, JobOffer


class JobsAddTest(TestCase, BaseCMSTestCase):
    su_username = 'user'
    su_password = 'pass'

    def setUp(self):
        self.template = get_cms_setting('TEMPLATES')[0][0]
        self.language = settings.LANGUAGES[0][0]
        self.page = api.create_page('page', self.template, self.language, published=True)
        self.placeholder = self.page.placeholders.all()[0]
        self.superuser = self.create_superuser()
        self.category = self.create_category()

    def create_category(self, name='Administration'):
        return JobCategory.objects.create(name=name)

    def create_superuser(self):
         return User.objects.create_superuser(self.su_username, 'email@example.com', self.su_password)

    def test_create_job_category(self):
        """
        We can create a new job category
        """
        self.assertEqual(self.category.name, 'Administration')
        self.assertEqual(JobCategory.objects.all()[0], self.category)

    def test_create_job_offer(self):
        """
        We can create a new job offer
        """
        title = 'Programmer'
        offer = JobOffer.objects.create(title=title, category=self.category)
        self.assertEqual(offer.title, title)
        self.assertEqual(JobOffer.objects.all()[0], offer)

    def test_create_job_offer_with_category(self):
        """
        We can add a job offer with a category
        """
        title = 'Senior'
        offer = JobOffer.objects.create(title=title, category=self.category)
        offer.save()
        self.assertIn(offer, self.category.jobs.all())

    def test_add_offer_list_plugin_api(self):
        """
        We add an offer to the Plugin and look it up
        """
        title = 'Manager'
        JobOffer.objects.create(title=title, category=self.category)
        api.add_plugin(self.placeholder, JobList, self.language)
        self.page.publish(self.language)

        url = self.page.get_absolute_url()
        response = self.client.get(url)
        self.assertContains(response, title)
