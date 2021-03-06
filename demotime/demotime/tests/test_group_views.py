from django.core.urlresolvers import reverse

from demotime import forms, models
from demotime.tests import BaseTestCase


class TestGroupListView(BaseTestCase):

    def setUp(self):
        super(TestGroupListView, self).setUp()
        self.user.is_superuser = True
        self.user.save()
        assert self.client.login(
            username=self.user.username,
            password='testing'
        )
        self.group_type = models.GroupType.objects.get()

    def _create_groups(self, count=5, members=None):
        groups = []
        for x in range(0, count):
            groups.append(
                models.Group.create_group(
                    name='test_group_{}'.format(x),
                    slug='test-group-{}'.format(x),
                    description='',
                    group_type=self.group_type,
                    members=members,
                )
            )

        return groups

    def test_group_list(self):
        self._create_groups()
        response = self.client.get(reverse('group-list'))
        self.assertStatusCode(response, 200)
        self.assertEqual(
            response.context['object_list'].count(),
            models.Group.objects.count()
        )

    def test_group_list_login_required(self):
        self.client.logout()
        response = self.client.get(reverse('group-list'))
        self.assertStatusCode(response, 302)

    def test_group_list_superuser_required(self):
        self.user.is_superuser = False
        self.user.save()
        response = self.client.get(reverse('group-list'))
        self.assertStatusCode(response, 403)


class TestGroupManageViews(BaseTestCase):

    def setUp(self):
        super(TestGroupManageViews, self).setUp()
        self.user.is_superuser = True
        self.user.save()
        assert self.client.login(
            username=self.user.username,
            password='testing'
        )
        self.group_type = models.GroupType.objects.get()

    def test_create_group_get(self):
        response = self.client.get(reverse('group-manage'))
        self.assertStatusCode(response, 200)
        self.assertIn('form', response.context)

    def test_create_group(self):
        response = self.client.post(reverse('group-manage'), {
            'name': 'salty dogs',
            'slug': 'salty-dogs',
            'group_type': self.group_type.pk,
            'description': 'description',
            'members': self.test_users.values_list('pk', flat=True)
        })
        self.assertStatusCode(response, 302)
        group = models.Group.objects.get(slug='salty-dogs')
        self.assertEqual(group.name, 'salty dogs')
        self.assertEqual(group.description, 'description')
        self.assertEqual(group.group_type, self.group_type)
        self.assertTrue(models.GroupMember.objects.filter(
            group=group, user__in=self.test_users
        ).exists())

    def test_edit_group_get(self):
        response = self.client.get(reverse('group-manage'), args=[self.group.slug])
        self.assertStatusCode(response, 200)
        self.assertIn('form', response.context)
        self.assertIn('group', response.context)

    def test_edit_group(self):
        self.group.groupmember_set.filter(user__in=self.test_users).delete()
        self.assertEqual(self.group.groupmember_set.count(), 4)
        self.group.groupmember_set.update(is_admin=True)
        response = self.client.post(reverse('group-manage', args=[self.group.slug]), {
            'name': 'Swansons',
            'slug': 'swansons',
            'group_type': self.group_type.pk,
            'description': 'this will be no fun at all',
            'members': models.UserProxy.objects.exclude(
                username='demotime_sys'
            ).values_list('pk', flat=True),
        })
        self.assertStatusCode(response, 302)
        self.group.refresh_from_db()
        self.assertEqual(
            self.group.groupmember_set.filter(
                user__in=self.followers,
                is_admin=True
            ).count(),
            2
        )
        self.assertTrue(
            self.group.groupmember_set.filter(
                user=self.user, is_admin=True
            ).exists()
        )
        self.assertEqual(
            self.group.groupmember_set.filter(
                user__in=self.test_users,
                is_admin=False
            ).count(),
            3
        )
        self.assertEqual(self.group.groupmember_set.count(), 7)
        self.assertEqual(self.group.name, 'Swansons')
        self.assertEqual(self.group.slug, 'swansons')
        self.assertEqual(self.group.description, 'this will be no fun at all')

    def test_edit_admins_get(self):
        response = self.client.get(
            reverse('group-manage-admins', args=[self.group.slug])
        )
        self.assertStatusCode(response, 200)
        self.assertEqual(
            response.context['group'],
            self.group
        )
        self.assertIn('member_formset', response.context)

    def test_edit_admins_make_admins(self):
        models.GroupMember.objects.filter(group=self.group).update(is_admin=False)
        post_data = {
            'form-TOTAL_FORMS': self.group.groupmember_set.count(),
            'form-INITIAL_FORMS': self.group.groupmember_set.count(),
            'form-MIN_NUM_FORMS': 0,
            'form-MAX_NUM_FORMS': self.group.groupmember_set.count(),
        }
        for count, gm in enumerate(models.GroupMember.objects.filter(group=self.group)):
            post_data.update({
                'form-{}-user'.format(count): gm.user.pk,
                'form-{}-group'.format(count): gm.group.pk,
                'form-{}-is_admin'.format(count): True,
                'form-{}-id'.format(count): gm.pk,
            })

        response = self.client.post(
            reverse('group-manage-admins', args=[self.group.slug]),
            post_data
        )
        self.assertStatusCode(response, 302)
        gms = models.GroupMember.objects.filter(group=self.group)
        for gm in gms:
            self.assertTrue(gm.is_admin)

    def test_edit_admins_demote_admins(self):
        models.GroupMember.objects.filter(group=self.group).update(is_admin=True)
        post_data = {
            'form-TOTAL_FORMS': self.group.groupmember_set.count(),
            'form-INITIAL_FORMS': self.group.groupmember_set.count(),
            'form-MIN_NUM_FORMS': 0,
            'form-MAX_NUM_FORMS': self.group.groupmember_set.count(),
        }
        for count, gm in enumerate(models.GroupMember.objects.filter(group=self.group)):
            post_data.update({
                'form-{}-user'.format(count): gm.user.pk,
                'form-{}-group'.format(count): gm.group.pk,
                'form-{}-is_admin'.format(count): False,
                'form-{}-id'.format(count): gm.pk,
            })

        response = self.client.post(
            reverse('group-manage-admins', args=[self.group.slug]),
            post_data
        )
        self.assertStatusCode(response, 302)
        gms = models.GroupMember.objects.filter(group=self.group)
        for gm in gms:
            self.assertFalse(gm.is_admin)

    def test_create_group_type_get(self):
        response = self.client.get(reverse('group-type-manage'))
        self.assertStatusCode(response, 200)
        self.assertTrue(
            isinstance(response.context['form'], forms.GroupTypeForm)
        )

    def test_create_group_type(self):
        response = self.client.post(reverse('group-type-manage'), {
            'name': 'Test Type',
            'slug': 'test-type',
        })
        self.assertStatusCode(response, 302)
        gt = models.GroupType.objects.get(slug='test-type')
        self.assertEqual(gt.name, 'Test Type')

    def test_edit_group_type_get(self):
        response = self.client.get(
            reverse('group-type-manage', args=[self.group_type.slug])
        )
        self.assertStatusCode(response, 200)
        self.assertEqual(
            response.context['group_type'],
            models.GroupType.objects.get(slug=self.group_type.slug)
        )
        self.assertTrue(
            isinstance(response.context['form'], forms.GroupTypeForm)
        )

    def test_edit_group_type(self):
        response = self.client.post(
            reverse('group-type-manage', args=[self.group_type.slug]),
            {'name': 'Test Type', 'slug': 'test-type'}
        )
        self.assertStatusCode(response, 302)
        self.group_type.refresh_from_db()
        self.assertEqual(self.group_type.name, 'Test Type')
        self.assertEqual(self.group_type.slug, 'test-type')

    def test_manage_group_type_errors(self):
        self.assertEqual(models.GroupType.objects.count(), 1)
        response = self.client.post(reverse('group-type-manage'), {})
        self.assertStatusCode(response, 200)
        form = response.context['form']
        self.assertEqual(models.GroupType.objects.count(), 1)
        self.assertIn('name', form.errors)
        self.assertIn('slug', form.errors)
