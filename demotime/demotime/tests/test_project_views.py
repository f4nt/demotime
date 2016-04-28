from django.core.urlresolvers import reverse

from demotime import constants, models
from demotime.tests import BaseTestCase


class TestProjectViews(BaseTestCase):

    def setUp(self):
        super(TestProjectViews, self).setUp()
        assert self.client.login(
            username=self.user.username,
            password='testing'
        )

    def test_project_index(self):
        for x in range(0, 5):
            models.Review.create_review(**self.default_review_kwargs)

        review = models.Review.objects.last()
        review.state = constants.CLOSED
        review.save()

        response = self.client.get(reverse('project', args=[self.project.slug]))
        self.assertStatusCode(response, 200)
        context = response.context
        self.assertEqual(context['open_demos'].count(), 4)
        self.assertEqual(context['user_updated_demos'].count(), 5)
        self.assertEqual(context['updated_demos'].count(), 5)
        self.assertEqual(context['object'], self.project)

    def test_project_admin_requires_admin(self):
        models.ProjectMember.objects.all().delete()
        models.ProjectGroup.objects.all().delete()
        pm, _ = models.ProjectMember.objects.get_or_create(
            project=self.project, user=self.user
        )
        response = self.client.get(
            reverse('project-admin', args=[self.project.slug])
        )
        self.assertStatusCode(response, 302)

        pm.is_admin = True
        pm.save()
        response = self.client.get(
            reverse('project-admin', args=[self.project.slug])
        )
        self.assertStatusCode(response, 200)
