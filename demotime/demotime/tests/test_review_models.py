from mock import patch

from django.core import mail
from django.contrib.auth.models import User
from django.core.files.uploadedfile import BytesIO, File

from demotime import constants, models
from demotime.tests import BaseTestCase


class TestReviewModels(BaseTestCase):

    def setUp(self):
        super(TestReviewModels, self).setUp()
        self.hook_patch = patch('demotime.models.reviews.Review.trigger_webhooks')
        self.hook_patch_run = self.hook_patch.start()
        self.addCleanup(self.hook_patch.stop)

    def test_create_review(self):
        self.assertEqual(len(mail.outbox), 0)
        obj = models.Review.create_review(**self.default_review_kwargs)
        assert obj.revision
        self.assertEqual(obj.creator_set.get().user, self.user)
        self.assertEqual(obj.title, 'Test Title')
        self.assertEqual(obj.description, 'Test Description')
        self.assertEqual(obj.case_link, 'http://example.org/')
        self.assertEqual(obj.reviewers.count(), 3)
        self.assertEqual(obj.reviewer_set.count(), 3)
        self.assertEqual(obj.revision.attachments.count(), 2)
        self.assertEqual(obj.follower_set.count(), 2)
        self.assertEqual(obj.last_action_by, self.user)
        attachment = obj.revision.attachments.all()[0]
        attachment.attachment.name = 'test/test_file'
        self.assertEqual(attachment.pretty_name, 'test_file')
        self.assertEqual(attachment.sort_order, 1)
        self.assertEqual(obj.revision.number, 1)
        self.assertEqual(obj.state, constants.OPEN)
        self.assertEqual(obj.reviewer_state, constants.REVIEWING)
        statuses = models.UserReviewStatus.objects.filter(review=obj)
        self.assertEqual(statuses.count(), 6)
        self.assertEqual(statuses.filter(read=True).count(), 1)
        self.assertEqual(statuses.filter(read=False).count(), 5)
        self.assertEqual(len(mail.outbox), 5)
        self.assertEqual(
            models.Reminder.objects.filter(review=obj, active=True).count(),
            4
        )
        self.hook_patch_run.assert_called_once_with(
            constants.CREATED
        )
        event = obj.event_set.get(
            event_type__code=models.EventType.DEMO_CREATED
        )
        self.assertEqual(event.event_type.code, event.event_type.DEMO_CREATED)
        self.assertEqual(event.related_object, obj)
        self.assertEqual(event.user, obj.creator_set.get().user)

    def test_create_review_with_review(self):
        self.assertEqual(len(mail.outbox), 0)
        self.default_review_kwargs['creators'] = [self.user, self.co_owner]
        obj = models.Review.create_review(**self.default_review_kwargs)
        assert obj.revision
        creators = obj.creator_set.active()
        self.assertTrue(creators.filter(user=self.user).exists())
        self.assertTrue(creators.filter(user=self.co_owner).exists())
        self.assertEqual(obj.title, 'Test Title')
        self.assertEqual(obj.description, 'Test Description')
        self.assertEqual(obj.case_link, 'http://example.org/')
        self.assertEqual(obj.reviewers.count(), 3)
        self.assertEqual(obj.reviewer_set.count(), 3)
        self.assertEqual(obj.revision.attachments.count(), 2)
        self.assertEqual(obj.follower_set.count(), 2)
        attachment = obj.revision.attachments.all()[0]
        attachment.attachment.name = 'test/test_file'
        self.assertEqual(attachment.pretty_name, 'test_file')
        self.assertEqual(attachment.sort_order, 1)
        self.assertEqual(obj.revision.number, 1)
        self.assertEqual(obj.state, constants.OPEN)
        self.assertEqual(obj.reviewer_state, constants.REVIEWING)
        statuses = models.UserReviewStatus.objects.filter(review=obj)
        self.assertEqual(statuses.count(), 7)
        self.assertEqual(statuses.filter(read=True).count(), 1)
        self.assertEqual(statuses.filter(read=False).count(), 6)
        self.assertEqual(len(mail.outbox), 6)
        self.assertEqual(
            models.Reminder.objects.filter(review=obj, active=True).count(),
            5
        )
        self.hook_patch_run.assert_called_once_with(
            constants.CREATED
        )
        event = obj.event_set.get(
            event_type__code=models.EventType.DEMO_CREATED
        )
        self.assertEqual(event.event_type.code, event.event_type.DEMO_CREATED)
        self.assertEqual(event.related_object, obj)
        self.assertEqual(event.user, self.user)

    def test_create_draft_review(self):
        self.assertEqual(len(mail.outbox), 0)
        self.default_review_kwargs['state'] = constants.DRAFT
        obj = models.Review.create_review(**self.default_review_kwargs)
        assert obj.revision
        self.assertEqual(obj.creator_set.get().user, self.user)
        self.assertEqual(obj.title, 'Test Title')
        self.assertEqual(obj.description, 'Test Description')
        self.assertEqual(obj.case_link, 'http://example.org/')
        self.assertEqual(obj.reviewers.count(), 3)
        self.assertEqual(obj.reviewer_set.count(), 3)
        self.assertEqual(obj.revision.attachments.count(), 2)
        self.assertEqual(obj.follower_set.count(), 2)
        self.assertEqual(obj.last_action_by, self.user)
        attachment = obj.revision.attachments.all()[0]
        attachment.attachment.name = 'test/test_file'
        self.assertEqual(attachment.pretty_name, 'test_file')
        self.assertEqual(attachment.sort_order, 1)
        self.assertEqual(obj.revision.number, 1)
        self.assertEqual(obj.state, constants.DRAFT)
        self.assertEqual(obj.reviewer_state, constants.REVIEWING)
        statuses = models.UserReviewStatus.objects.filter(review=obj)
        self.assertEqual(statuses.count(), 6)
        self.assertEqual(statuses.filter(read=True).count(), 1)
        self.assertEqual(statuses.filter(read=False).count(), 5)
        self.assertEqual(len(mail.outbox), 0)
        self.assertFalse(
            models.Reminder.objects.filter(review=obj, active=True).exists()
        )
        self.hook_patch_run.assert_not_called()
        self.assertFalse(
            obj.event_set.filter(
                event_type__code=models.EventType.DEMO_CREATED
            ).exists()
        )
        self.assertFalse(
            obj.event_set.filter(
                event_type__code=models.EventType.REVIEWER_ADDED
            ).exists()
        )
        self.assertFalse(
            obj.event_set.filter(
                event_type__code=models.EventType.FOLLOWER_ADDED
            ).exists()
        )

    def test_post_create_draft_review_with_coowner(self):
        self.assertEqual(len(mail.outbox), 0)
        self.default_review_kwargs['state'] = constants.DRAFT
        self.default_review_kwargs['creators'] = [self.user, self.co_owner]
        obj = models.Review.create_review(**self.default_review_kwargs)
        assert obj.revision
        creators = obj.creator_set.active()
        self.assertTrue(creators.filter(user=self.user).exists())
        self.assertTrue(creators.filter(user=self.co_owner).exists())
        self.assertEqual(obj.title, 'Test Title')
        self.assertEqual(obj.description, 'Test Description')
        self.assertEqual(obj.case_link, 'http://example.org/')
        self.assertEqual(obj.reviewers.count(), 3)
        self.assertEqual(obj.reviewer_set.count(), 3)
        self.assertEqual(obj.revision.attachments.count(), 2)
        self.assertEqual(obj.follower_set.count(), 2)
        self.assertEqual(obj.last_action_by, self.user)
        attachment = obj.revision.attachments.all()[0]
        attachment.attachment.name = 'test/test_file'
        self.assertEqual(attachment.pretty_name, 'test_file')
        self.assertEqual(attachment.sort_order, 1)
        self.assertEqual(obj.revision.number, 1)
        self.assertEqual(obj.state, constants.DRAFT)
        self.assertEqual(obj.reviewer_state, constants.REVIEWING)
        statuses = models.UserReviewStatus.objects.filter(review=obj)
        self.assertEqual(statuses.count(), 7)
        self.assertEqual(statuses.filter(read=True).count(), 1)
        self.assertEqual(statuses.filter(read=False).count(), 6)
        self.assertEqual(len(mail.outbox), 1)
        self.assertFalse(
            models.Reminder.objects.filter(review=obj, active=True).exists()
        )
        self.hook_patch_run.assert_not_called()
        self.assertFalse(
            obj.event_set.filter(
                event_type__code=models.EventType.DEMO_CREATED
            ).exists()
        )
        self.assertFalse(
            obj.event_set.filter(
                event_type__code=models.EventType.REVIEWER_ADDED
            ).exists()
        )
        self.assertFalse(
            obj.event_set.filter(
                event_type__code=models.EventType.FOLLOWER_ADDED
            ).exists()
        )

    def test_update_draft_review(self):
        self.default_review_kwargs['state'] = constants.DRAFT
        attachments = self.default_review_kwargs['attachments']
        self.default_review_kwargs['attachments'] = []
        obj = models.Review.create_review(**self.default_review_kwargs)
        self.assertEqual(obj.reviewers.count(), 3)
        self.assertEqual(obj.revision.attachments.count(), 0)
        self.assertEqual(obj.revision.number, 1)
        self.assertEqual(len(mail.outbox), 0)
        models.UserReviewStatus.objects.filter(review=obj).update(read=True)
        self.default_review_kwargs.update({
            'review': obj.pk,
            'title': 'New Title',
            'description': 'New Description',
            'case_link': 'http://badexample.org',
            'reviewers': self.test_users.exclude(username='test_user_0'),
            'attachments': attachments,
        })
        obj = models.Review.update_review(**self.default_review_kwargs)
        self.assertEqual(obj.state, constants.DRAFT)
        # Should still be the same, singular revision
        self.assertEqual(obj.reviewer_set.count(), 3)
        self.assertEqual(obj.reviewer_set.active().count(), 2)
        self.assertEqual(obj.revision.number, 1)
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(obj.revision.attachments.count(), 2)
        self.assertEqual(obj.description, 'New Description')
        self.assertEqual(obj.case_link, 'http://badexample.org')
        self.assertEqual(obj.last_action_by, self.user)
        self.assertFalse(
            models.Reminder.objects.filter(review=obj, active=True).exists()
        )
        self.hook_patch_run.assert_not_called()
        self.assertFalse(
            obj.event_set.filter(
                event_type__code=models.EventType.DEMO_CREATED
            ).exists()
        )
        self.assertFalse(
            obj.event_set.filter(
                event_type__code=models.EventType.REVIEWER_ADDED
            ).exists()
        )
        self.assertFalse(
            obj.event_set.filter(
                event_type__code=models.EventType.REVIEWER_REMOVED
            ).exists()
        )
        self.assertFalse(
            obj.event_set.filter(
                event_type__code=models.EventType.FOLLOWER_ADDED
            ).exists()
        )

    def test_draft_with_two_coowners_change_owners(self):
        self.assertEqual(len(mail.outbox), 0)
        self.default_review_kwargs['state'] = constants.DRAFT
        self.default_review_kwargs['followers'] = []
        self.default_review_kwargs['creators'] = [self.user, self.co_owner]
        obj = models.Review.create_review(**self.default_review_kwargs)
        creators = obj.creator_set.active()
        self.assertTrue(creators.filter(user=self.user).exists())
        self.assertTrue(creators.filter(user=self.co_owner).exists())
        self.assertEqual(obj.state, constants.DRAFT)
        assert obj.revision
        self.default_review_kwargs['creators'] = [self.user, self.followers[0]]
        self.default_review_kwargs['state'] = constants.DRAFT
        self.default_review_kwargs['review'] = obj.pk
        obj = models.Review.update_review(**self.default_review_kwargs)
        creators = obj.creator_set.active()
        self.assertTrue(creators.filter(user=self.user).exists())
        self.assertFalse(creators.filter(user=self.co_owner).exists())
        self.assertTrue(creators.filter(user=self.followers[0]).exists())
        self.assertEqual(obj.state, constants.DRAFT)
        self.default_review_kwargs['creators'] = [self.followers[0], self.followers[1]]
        self.default_review_kwargs['state'] = constants.OPEN
        obj = models.Review.update_review(**self.default_review_kwargs)
        creators = obj.creator_set.active()
        self.assertTrue(creators.filter(user=self.followers[0]).exists())
        self.assertTrue(creators.filter(user=self.followers[1]).exists())
        self.assertFalse(creators.filter(user=self.user).exists())
        self.assertFalse(creators.filter(user=self.co_owner).exists())
        self.assertEqual(obj.state, constants.OPEN)

    def test_draft_review_opened(self):
        self.default_review_kwargs['state'] = constants.DRAFT
        obj = models.Review.create_review(**self.default_review_kwargs)
        created_time = obj.created
        self.assertEqual(len(mail.outbox), 0)
        self.default_review_kwargs['state'] = constants.OPEN
        self.default_review_kwargs['review'] = obj.pk
        obj = models.Review.update_review(**self.default_review_kwargs)
        self.assertNotEqual(created_time, obj.created)
        self.assertEqual(obj.state, constants.OPEN)
        self.assertEqual(obj.revision.number, 1)
        self.assertEqual(len(mail.outbox), 5)
        self.assertTrue(
            obj.event_set.filter(
                event_type__code=models.EventType.DEMO_CREATED
            ).exists()
        )
        self.assertTrue(
            obj.event_set.filter(
                event_type__code=models.EventType.REVIEWER_ADDED
            ).exists()
        )
        self.assertTrue(
            obj.event_set.filter(
                event_type__code=models.EventType.FOLLOWER_ADDED
            ).exists()
        )
        self.hook_patch_run.assert_called_once_with(
            constants.CREATED
        )

    def test_create_review_duped_reviewer_follower(self):
        ''' Test creating a review with a user in both the Reviwers and the
        Followers list
        '''
        self.assertEqual(len(mail.outbox), 0)
        review_kwargs = self.default_review_kwargs.copy()
        user_pks = list(self.test_users.values_list('pk', flat=True))
        user_pks += list(self.followers.values_list('pk', flat=True))
        review_kwargs['followers'] = User.objects.filter(pk__in=user_pks)
        obj = models.Review.create_review(**review_kwargs)
        assert obj.revision
        self.assertEqual(obj.creator_set.get().user, self.user)
        self.assertEqual(obj.title, 'Test Title')
        self.assertEqual(obj.description, 'Test Description')
        self.assertEqual(obj.case_link, 'http://example.org/')
        self.assertEqual(obj.reviewers.count(), 3)
        self.assertEqual(obj.reviewer_set.count(), 3)
        self.assertEqual(obj.revision.attachments.count(), 2)
        self.assertEqual(obj.follower_set.count(), 2)
        attachment = obj.revision.attachments.all()[0]
        attachment.attachment.name = 'test/test_file'
        self.assertEqual(attachment.pretty_name, 'test_file')
        self.assertEqual(obj.revision.number, 1)
        self.assertEqual(obj.state, constants.OPEN)
        self.assertEqual(obj.reviewer_state, constants.REVIEWING)
        statuses = models.UserReviewStatus.objects.filter(review=obj)
        self.assertEqual(statuses.count(), 6)
        self.assertEqual(statuses.filter(read=True).count(), 1)
        self.assertEqual(statuses.filter(read=False).count(), 5)
        self.assertEqual(len(mail.outbox), 5)
        self.assertEqual(
            models.Reminder.objects.filter(review=obj, active=True).count(),
            4
        )

    def test_update_review(self):
        self.assertEqual(len(mail.outbox), 0)
        review_kwargs = self.default_review_kwargs.copy()
        # We had problems before where updating one review's reviewers updated
        # the reviewer's for alllllll reviews. Let's not let that happen again
        # (issue #55)
        second_review_kwargs = self.default_review_kwargs.copy()
        second_review_kwargs['title'] = 'Some Other Review'
        obj = models.Review.create_review(**self.default_review_kwargs)
        first_rev = obj.revision
        second_review = models.Review.create_review(**second_review_kwargs)
        self.assertEqual(obj.reviewers.count(), 3)
        approving_reviewer = obj.reviewer_set.active()[0]
        approving_reviewer.status = constants.APPROVED
        approving_reviewer.save()
        self.assertEqual(obj.revision.number, 1)
        self.assertEqual(second_review.reviewers.count(), 3)
        self.assertEqual(len(mail.outbox), 10)
        mail.outbox = []

        models.UserReviewStatus.objects.filter(review=obj).update(read=True)
        review_kwargs.update({
            'review': obj.pk,
            'title': 'New Title',
            'description': 'New Description',
            'case_link': 'http://badexample.org',
            'reviewers': self.test_users.exclude(username='test_user_0'),
            'delete_attachments': obj.revision.attachments.all(),
        })
        new_obj = models.Review.update_review(**review_kwargs)
        event = new_obj.event_set.get(
            event_type__code=models.EventType.DEMO_UPDATED
        )
        self.assertEqual(event.event_type.code, event.event_type.DEMO_UPDATED)
        self.assertEqual(event.related_object, obj)
        self.assertEqual(event.user, obj.creator_set.active().get().user)
        second_rev = new_obj.revision
        self.assertEqual(obj.pk, new_obj.pk)
        self.assertEqual(new_obj.title, 'New Title')
        self.assertEqual(new_obj.case_link, 'http://badexample.org')
        # Desc should be unchanged
        self.assertEqual(new_obj.description, 'Test Description')
        self.assertEqual(new_obj.revision.description, 'New Description')
        self.assertEqual(new_obj.reviewrevision_set.count(), 2)
        self.assertEqual(new_obj.revision.number, 2)
        self.assertTrue(new_obj.revision.is_max_revision)
        self.assertEqual(obj.reviewer_set.count(), 3)
        self.assertEqual(obj.reviewer_set.active().count(), 2)
        self.assertEqual(obj.follower_set.count(), 2)
        for reviewer in obj.reviewer_set.all():
            self.assertEqual(reviewer.status, constants.REVIEWING)
        self.assertEqual(second_review.reviewers.count(), 3)
        self.assertEqual(second_review.reviewer_set.count(), 3)
        self.assertEqual(second_review.follower_set.count(), 2)
        statuses = models.UserReviewStatus.objects.filter(review=obj)
        self.assertEqual(statuses.count(), 6)
        self.assertEqual(statuses.filter(read=True).count(), 1)
        self.assertEqual(statuses.filter(read=False).count(), 5)
        self.assertEqual(len(mail.outbox), 5)
        self.assertEqual(
            models.Reminder.objects.filter(review=obj, active=True).count(),
            3
        )
        # Since we didn't supply attachments in the update, they should be
        # copied over
        self.assertEqual(
            first_rev.attachments.count(),
            second_rev.attachments.count()
        )
        self.assertEqual(
            self.hook_patch_run.call_args_list[0][0][0],
            constants.CREATED
        )
        # Second demo
        self.assertEqual(
            self.hook_patch_run.call_args_list[1][0][0],
            constants.CREATED
        )
        self.assertEqual(
            self.hook_patch_run.call_args_list[2][0][0],
            constants.UPDATED,
        )

    def test_update_review_keep_some_attachments(self):
        obj = models.Review.create_review(**self.default_review_kwargs)
        self.assertEqual(obj.reviewers.count(), 3)
        self.assertEqual(obj.revision.attachments.count(), 2)
        self.assertEqual(obj.revision.number, 1)
        self.assertEqual(obj.state, constants.OPEN)
        self.assertEqual(obj.reviewer_state, constants.REVIEWING)
        first_attachment, second_attachment = obj.revision.attachments.all()

        self.default_review_kwargs.update({
            'review': obj.pk,
            'title': 'New Title',
            'description': 'New Description',
            'case_link': 'http://badexample.org',
            'delete_attachments': [first_attachment],
            'attachments': [
                {
                    'attachment': File(BytesIO(b'new_file'), name='new_file.jpeg'),
                    'description': 'Testing',
                    'sort_order': 0,
                },
            ],
        })
        obj = models.Review.update_review(**self.default_review_kwargs)
        self.assertEqual(obj.reviewers.count(), 3)
        self.assertEqual(obj.revision.number, 2)
        self.assertEqual(obj.revision.attachments.count(), 2)
        second_attach_content = second_attachment.attachment.file.read()
        updated_attach_content = obj.revision.attachments.all()[0].attachment.file.read()
        self.assertEqual(second_attach_content, updated_attach_content)
        new_first = obj.revision.attachments.first()
        new_last = obj.revision.attachments.last()
        self.assertEqual(new_first.sort_order, 0)
        self.assertEqual(new_last.sort_order, 1)
        self.assertEqual(new_last.attachment.file.read(), b'new_file')
        self.assertEqual(obj.state, constants.OPEN)
        self.assertEqual(obj.reviewer_state, constants.REVIEWING)
        self.assertEqual(obj.last_action_by, self.user)

    def test_update_review_with_existing_coowner(self):
        self.default_review_kwargs['creators'] = [self.user, self.co_owner]
        obj = models.Review.create_review(**self.default_review_kwargs)
        self.assertEqual(obj.reviewer_set.active().count(), 3)
        self.assertEqual(obj.revision.attachments.count(), 2)
        self.assertEqual(obj.revision.number, 1)
        self.assertEqual(obj.creator_set.active().count(), 2)
        self.assertEqual(obj.state, constants.OPEN)
        self.assertEqual(obj.reviewer_state, constants.REVIEWING)
        self.assertEqual(
            len(mail.outbox),
            6 # 3 reviewers, 2 followers, 1 co-owner
        )
        mail.outbox = []
        self.default_review_kwargs.update({
            'review': obj.pk,
            'title': 'New Title',
            'description': 'New Description',
            'case_link': 'http://badexample1.org',
        })
        obj = models.Review.update_review(**self.default_review_kwargs)
        self.assertEqual(obj.reviewer_set.active().count(), 3)
        self.assertEqual(obj.revision.number, 2)
        self.assertEqual(obj.revision.attachments.count(), 4)
        self.assertEqual(obj.state, constants.OPEN)
        self.assertEqual(obj.reviewer_state, constants.REVIEWING)
        self.assertEqual(
            len(mail.outbox),
            6 # 3 reviewers, 2 followers, 1 co-owner
        )
        self.assertEqual(obj.last_action_by, self.user)

    def test_update_review_add_coowner(self):
        obj = models.Review.create_review(**self.default_review_kwargs)
        self.assertEqual(obj.reviewers.count(), 3)
        self.assertEqual(obj.revision.attachments.count(), 2)
        self.assertEqual(obj.revision.number, 1)
        self.assertEqual(obj.state, constants.OPEN)
        self.assertEqual(obj.reviewer_state, constants.REVIEWING)
        self.default_review_kwargs.update({
            'review': obj.pk,
            'title': 'New Title',
            'description': 'New Description',
            'case_link': 'http://badexample.org',
            'creators': [self.user, self.co_owner],
        })
        obj = models.Review.update_review(**self.default_review_kwargs)
        self.assertEqual(obj.reviewers.count(), 3)
        self.assertEqual(obj.revision.number, 2)
        self.assertEqual(obj.revision.attachments.count(), 4)
        self.assertEqual(obj.state, constants.PAUSED)
        self.assertEqual(obj.reviewer_state, constants.REVIEWING)
        creators = obj.creator_set.active()
        self.assertTrue(creators.filter(user=self.user).exists())
        self.assertTrue(creators.filter(user=self.co_owner).exists())
        co_owner_msgs = [
            msg for msg in mail.outbox if msg.to == [self.co_owner.email]
        ]
        # 1 for Revision, 1 for being added
        self.assertEqual(len(co_owner_msgs), 2)
        self.assertEqual(
            models.Event.objects.filter(
                user=self.user,
                event_type__code=models.EventType.OWNER_ADDED
            ).count(),
            1
        )

    def test_update_review_remove_coowner(self):
        self.default_review_kwargs['creators'] = [self.user, self.co_owner]
        obj = models.Review.create_review(**self.default_review_kwargs)
        self.assertEqual(obj.creator_set.active().count(), 2)
        self.assertEqual(obj.reviewer_set.active().count(), 3)
        self.assertEqual(obj.revision.attachments.count(), 2)
        self.assertEqual(obj.revision.number, 1)
        self.assertEqual(obj.state, constants.OPEN)
        self.assertEqual(obj.reviewer_state, constants.REVIEWING)
        self.default_review_kwargs.update({
            'review': obj.pk,
            'title': 'New Title',
            'description': 'New Description',
            'case_link': 'http://badexample.org',
            'creators': [self.user]
        })
        obj = models.Review.update_review(**self.default_review_kwargs)
        self.assertEqual(obj.reviewers.count(), 3)
        self.assertEqual(obj.revision.number, 2)
        self.assertEqual(obj.revision.attachments.count(), 4)
        self.assertEqual(obj.state, constants.OPEN)
        self.assertEqual(obj.reviewer_state, constants.REVIEWING)
        creators = obj.creator_set.active()
        self.assertEqual(creators.count(), 1)
        self.assertTrue(creators.filter(user=self.user).exists())
        self.assertFalse(creators.filter(user=self.co_owner).exists())
        co_owner_msgs = [
            msg for msg in mail.outbox if msg.to == [self.co_owner.email]
        ]
        # 1 for adding, 1 for removing
        self.assertEqual(len(co_owner_msgs), 2)
        self.assertEqual(
            models.Event.objects.filter(
                user=self.user,
                event_type__code=models.EventType.OWNER_REMOVED
            ).count(),
            1
        )

    def test_update_review_publish_with_changed_coowners(self):
        self.default_review_kwargs['creators'] = [self.user, self.co_owner]
        self.default_review_kwargs['followers'] = []
        self.default_review_kwargs['state'] = constants.DRAFT
        obj = models.Review.create_review(**self.default_review_kwargs)
        self.assertEqual(obj.state, constants.DRAFT)
        self.assertEqual(obj.creator_set.active().count(), 2)
        self.assertEqual(obj.reviewer_set.active().count(), 3)
        self.assertEqual(obj.revision.attachments.count(), 2)
        self.assertEqual(obj.revision.number, 1)
        self.default_review_kwargs.update({
            'review': obj.pk,
            'title': 'New Title',
            'description': 'New Description',
            'case_link': 'http://badexample.org',
            'creators': [self.user, self.followers[0]],
            'state': constants.OPEN
        })
        obj = models.Review.update_review(**self.default_review_kwargs)
        self.assertEqual(obj.state, constants.OPEN)
        self.assertEqual(
            models.Event.objects.filter(
                event_type__code=models.EventType.OWNER_ADDED
            ).count(),
            0
        )

    def test_update_review_change_coowner(self):
        self.default_review_kwargs['creators'] = [self.user, self.co_owner]
        self.default_review_kwargs['followers'] = []
        obj = models.Review.create_review(**self.default_review_kwargs)
        self.assertEqual(obj.state, constants.OPEN)
        self.assertEqual(obj.reviewer_state, constants.REVIEWING)
        self.assertEqual(
            models.Event.objects.filter(
                user=self.user,
                event_type__code=models.EventType.OWNER_ADDED,
            ).count(),
            0
        )
        self.assertEqual(obj.creator_set.active().count(), 2)
        self.assertEqual(obj.reviewer_set.active().count(), 3)
        self.assertEqual(obj.revision.attachments.count(), 2)
        self.assertEqual(obj.revision.number, 1)
        self.default_review_kwargs.update({
            'review': obj.pk,
            'title': 'New Title',
            'description': 'New Description',
            'case_link': 'http://badexample.org',
            'creators': [self.user, self.followers[0]]
        })
        obj = models.Review.update_review(**self.default_review_kwargs)
        self.assertEqual(obj.reviewers.count(), 3)
        self.assertEqual(obj.revision.number, 2)
        self.assertEqual(obj.revision.attachments.count(), 4)
        self.assertEqual(obj.state, constants.PAUSED)
        self.assertEqual(obj.reviewer_state, constants.REVIEWING)
        creators = obj.creator_set.active()
        self.assertEqual(creators.count(), 2)
        self.assertTrue(creators.filter(user=self.user).exists())
        self.assertTrue(creators.filter(user=self.followers[0]).exists())
        self.assertFalse(creators.filter(user=self.co_owner).exists())
        co_owner_msgs = [
            msg for msg in mail.outbox if msg.to == [self.co_owner.email]
        ]
        follower_msgs = [
            msg for msg in mail.outbox if msg.to == [self.followers[0].email]
        ]
        # 1 for being added, 1 for removal
        self.assertEqual(len(co_owner_msgs), 2)
        # 1 for being added, 1 for revision
        self.assertEqual(len(follower_msgs), 2)
        self.assertEqual(
            models.Event.objects.filter(
                user=self.user,
                event_type__code=models.EventType.OWNER_REMOVED
            ).count(),
            1
        )
        self.assertEqual(
            models.Event.objects.filter(
                user=self.user,
                event_type__code=models.EventType.OWNER_ADDED,
            ).count(),
            1
        )

    def test_update_paused_review(self):
        ''' Updating a paused review should reopen it '''
        obj = models.Review.create_review(**self.default_review_kwargs)
        for reviewer in obj.reviewer_set.all():
            reviewer.set_status(constants.APPROVED)
        mail.outbox = []
        models.Event.objects.all().delete()
        obj.update_state(constants.PAUSED)
        obj.refresh_from_db()
        self.assertEqual(obj.reviewer_set.active().count(), 3)
        self.assertEqual(obj.revision.attachments.count(), 2)
        self.assertEqual(obj.revision.number, 1)
        self.assertEqual(obj.state, constants.PAUSED)
        self.assertEqual(obj.reviewer_state, constants.APPROVED)
        models.UserReviewStatus.objects.filter(review=obj).update(read=True)
        self.default_review_kwargs.update({
            'review': obj.pk,
            'title': 'New Title',
            'description': 'New Description',
            'case_link': 'http://badexample.org',
            'reviewers': self.test_users.exclude(username='test_user_0'),
            'delete_attachments': obj.revision.attachments.all(),
        })
        obj = models.Review.update_review(**self.default_review_kwargs)
        self.assertEqual(obj.reviewer_set.count(), 3)
        self.assertEqual(obj.reviewer_set.active().count(), 2)
        self.assertEqual(obj.revision.number, 2)
        self.assertEqual(obj.revision.attachments.count(), 2)
        self.assertEqual(obj.revision.description, 'New Description')
        self.assertEqual(obj.reviewrevision_set.count(), 2)
        self.assertEqual(obj.revision.number, 2)
        self.assertEqual(obj.state, constants.OPEN)
        self.assertEqual(obj.reviewer_state, constants.REVIEWING)

    def test_update_closed_review(self):
        ''' Updating a closed review should reopen it '''
        obj = models.Review.create_review(**self.default_review_kwargs)
        for reviewer in obj.reviewer_set.all():
            reviewer.set_status(constants.APPROVED)
        obj.update_state(constants.CLOSED)
        self.assertEqual(obj.reviewers.count(), 3)
        self.assertEqual(obj.revision.attachments.count(), 2)
        self.assertEqual(obj.revision.number, 1)
        self.assertEqual(obj.state, constants.CLOSED)
        self.assertEqual(obj.reviewer_state, constants.APPROVED)
        models.UserReviewStatus.objects.filter(review=obj).update(read=True)
        self.default_review_kwargs.update({
            'review': obj.pk,
            'title': 'New Title',
            'description': 'New Description',
            'case_link': 'http://badexample.org',
            'reviewers': self.test_users.exclude(username='test_user_0'),
            'delete_attachments': obj.revision.attachments.all(),
        })
        obj = models.Review.update_review(**self.default_review_kwargs)
        self.assertEqual(obj.reviewer_set.count(), 3)
        self.assertEqual(obj.reviewer_set.active().count(), 2)
        self.assertEqual(obj.revision.number, 2)
        self.assertEqual(obj.revision.attachments.count(), 2)
        self.assertEqual(obj.revision.description, 'New Description')
        self.assertEqual(obj.reviewrevision_set.count(), 2)
        self.assertEqual(obj.revision.number, 2)
        self.assertEqual(obj.state, constants.OPEN)
        self.assertEqual(obj.reviewer_state, constants.REVIEWING)

    def test_update_review_duped_reviewer_existing_follower(self):
        self.assertEqual(len(mail.outbox), 0)
        review = models.Review.create_review(**self.default_review_kwargs)
        self.assertEqual(review.reviewer_set.active().count(), 3)
        self.assertEqual(review.follower_set.active().count(), 2)
        approving_reviewer = review.reviewer_set.active()[0]
        approving_reviewer.status = constants.APPROVED
        approving_reviewer.save()
        self.assertEqual(review.revision.number, 1)
        self.assertEqual(len(mail.outbox), 5)
        existing_reviewer_pks = list(review.reviewer_set.active().values_list(
            'reviewer__pk', flat=True
        ))
        follower_pk = review.follower_set.active()[0].user.pk
        updated_reviewers = User.objects.filter(
            pk__in=existing_reviewer_pks + [follower_pk]
        )
        self.default_review_kwargs['reviewers'] = updated_reviewers
        self.default_review_kwargs['review'] = review.pk
        review = models.Review.update_review(**self.default_review_kwargs)
        self.assertEqual(review.reviewer_set.active().count(), 4)
        self.assertEqual(review.follower_set.active().count(), 1)


    def test_update_review_duped_reviewer_follower(self):
        self.assertEqual(len(mail.outbox), 0)
        review_kwargs = self.default_review_kwargs.copy()
        user_pks = list(self.test_users.values_list('pk', flat=True))
        user_pks += list(self.followers.values_list('pk', flat=True))
        review_kwargs['followers'] = User.objects.filter(pk__in=user_pks)
        obj = models.Review.create_review(**review_kwargs)
        first_rev = obj.revision
        self.assertEqual(obj.reviewer_set.active().count(), 3)
        self.assertEqual(obj.follower_set.active().count(), 2)
        approving_reviewer = obj.reviewer_set.active()[0]
        approving_reviewer.status = constants.APPROVED
        approving_reviewer.save()
        self.assertEqual(obj.revision.number, 1)
        self.assertEqual(len(mail.outbox), 5)
        mail.outbox = []

        models.UserReviewStatus.objects.filter(review=obj).update(read=True)
        review_kwargs.update({
            'review': obj.pk,
            'title': 'New Title',
            'description': 'New Description',
            'case_link': 'http://badexample.org',
            'reviewers': self.test_users.exclude(username='test_user_0'),
            'delete_attachments': obj.revision.attachments.all(),
        })
        new_obj = models.Review.update_review(**review_kwargs)
        second_rev = new_obj.revision
        self.assertEqual(obj.pk, new_obj.pk)
        self.assertEqual(new_obj.title, 'New Title')
        self.assertEqual(new_obj.case_link, 'http://badexample.org')
        # Desc should be unchanged
        self.assertEqual(new_obj.description, 'Test Description')
        self.assertEqual(new_obj.revision.description, 'New Description')
        self.assertEqual(new_obj.reviewrevision_set.count(), 2)
        self.assertEqual(new_obj.revision.number, 2)
        self.assertTrue(new_obj.revision.is_max_revision)
        self.assertEqual(obj.reviewer_set.active().count(), 2)
        self.assertEqual(obj.reviewer_set.count(), 3)
        self.assertEqual(obj.follower_set.count(), 2)
        for reviewer in obj.reviewer_set.all():
            self.assertEqual(reviewer.status, constants.REVIEWING)
        statuses = models.UserReviewStatus.objects.filter(review=obj)
        self.assertEqual(statuses.count(), 6)
        self.assertEqual(statuses.filter(read=True).count(), 1)
        self.assertEqual(statuses.filter(read=False).count(), 5)
        self.assertEqual(len(mail.outbox), 5)
        self.assertEqual(
            models.Reminder.objects.filter(review=obj, active=True).count(),
            3
        )
        # Since we didn't supply attachments in the update, they should be
        # copied over
        self.assertEqual(
            first_rev.attachments.count(),
            second_rev.attachments.count()
        )

    def test_update_reviewer_state_approved(self):
        self.assertEqual(len(mail.outbox), 0)
        obj = models.Review.create_review(**self.default_review_kwargs)
        self.assertEqual(len(mail.outbox), 5)
        mail.outbox = []

        obj.reviewer_set.update(status=constants.APPROVED)
        models.UserReviewStatus.objects.update(read=True)
        changed, new_state = obj.update_reviewer_state()
        obj = models.Review.objects.get(pk=obj.pk)
        self.assertEqual(obj.reviewer_state, constants.APPROVED)
        creator = obj.creator_set.active().get().user
        approved_msg = []
        for msg in mail.outbox:
            if msg.to == [creator.email] and 'approved' in msg.body:
                approved_msg.append(msg)

        self.assertEqual(len(approved_msg), 1)
        self.assertTrue(changed)
        self.assertEqual(new_state, constants.APPROVED)
        event = obj.event_set.get(event_type__code=models.EventType.DEMO_APPROVED)
        self.assertEqual(event.event_type.code, event.event_type.DEMO_APPROVED)
        self.assertEqual(event.related_object, obj)
        self.assertEqual(event.user, obj.creator_set.active().get().user)
        self.assertTrue(
            models.UserReviewStatus.objects.filter(
                review=obj,
                user=self.user,
                read=False
            ).exists()
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            self.hook_patch_run.call_args_list[0][0][0],
            constants.CREATED
        )
        self.assertEqual(
            self.hook_patch_run.call_args_list[1][0][0],
            constants.APPROVED
        )

    def test_update_reviewer_state_rejected(self):
        self.assertEqual(len(mail.outbox), 0)
        obj = models.Review.create_review(**self.default_review_kwargs)
        self.assertEqual(len(mail.outbox), 5)
        mail.outbox = []

        obj.reviewer_set.update(status=constants.REJECTED)
        models.UserReviewStatus.objects.update(read=True)
        changed, new_state = obj.update_reviewer_state()
        obj = models.Review.objects.get(pk=obj.pk)
        self.assertEqual(obj.reviewer_state, constants.REJECTED)
        event = obj.event_set.get(event_type__code=models.EventType.DEMO_REJECTED)
        self.assertEqual(event.event_type.code, event.event_type.DEMO_REJECTED)
        self.assertEqual(event.related_object, obj)
        self.assertEqual(event.user, obj.creator_set.active().get().user)
        rejected_msg = []
        creator = obj.creator_set.active().get().user
        for msg in mail.outbox:
            if msg.to == [creator.email] and 'rejected' in msg.body:
                rejected_msg.append(msg)

        self.assertEqual(len(rejected_msg), 1)
        self.assertTrue(changed)
        self.assertEqual(new_state, constants.REJECTED)
        self.assertTrue(
            models.UserReviewStatus.objects.filter(
                review=obj,
                user=self.user,
                read=False
            ).exists()
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            self.hook_patch_run.call_args_list[0][0][0],
            constants.CREATED
        )
        self.assertEqual(
            self.hook_patch_run.call_args_list[1][0][0],
            constants.REJECTED
        )

    def test_update_reviewer_state_reviewing(self):
        self.assertEqual(len(mail.outbox), 0)
        obj = models.Review.create_review(**self.default_review_kwargs)
        self.assertEqual(len(mail.outbox), 5)
        mail.outbox = []

        obj.reviewer_set.update(status=constants.REJECTED)
        obj.reviewer_state = constants.REJECTED
        obj.save(update_fields=['reviewer_state'])
        # We're mocking a state change, so let's purge the state machine
        obj._reviewer_state_machine = None
        undecided_person = obj.reviewer_set.all()[0]
        undecided_person.status = constants.REVIEWING
        undecided_person.save()
        models.UserReviewStatus.objects.update(read=True)
        changed, new_state = obj.update_reviewer_state()
        obj.refresh_from_db()
        self.assertEqual(obj.reviewer_state, constants.REVIEWING)
        review_msg = []
        creator = obj.creator_set.active().get().user
        for msg in mail.outbox:
            if msg.to == [creator.email] and 'Under Review' in msg.body:
                review_msg.append(msg)

        self.assertEqual(len(review_msg), 1)
        self.assertTrue(changed)
        self.assertEqual(new_state, constants.REVIEWING)
        event = obj.event_set.get(
            event_type__code=models.EventType.DEMO_REVIEWING
        )
        self.assertEqual(event.event_type.code, event.event_type.DEMO_REVIEWING)
        self.assertEqual(event.related_object, obj)
        self.assertEqual(event.user, obj.creator_set.active().get().user)
        self.assertTrue(
            models.UserReviewStatus.objects.filter(
                review=obj,
                user=self.user,
                read=False
            ).exists()
        )
        self.assertEqual(len(mail.outbox), 1)

    def test_update_reviewer_state_unchanged(self):
        obj = models.Review.create_review(**self.default_review_kwargs)
        changed, new_state = obj.update_reviewer_state()
        self.assertFalse(changed)
        self.assertEqual(new_state, '')

    def test_review_state_unchanged(self):
        obj = models.Review.create_review(**self.default_review_kwargs)
        self.assertFalse(obj.update_state(constants.OPEN))

    def test_review_state_change_paused(self):
        self.assertEqual(len(mail.outbox), 0)
        obj = models.Review.create_review(**self.default_review_kwargs)
        self.assertEqual(len(mail.outbox), 5)
        dropped_reviewer = obj.reviewer_set.all()[0]
        dropped_follower = obj.follower_set.all()[0]
        dropped_reviewer.drop_reviewer(obj.creator_set.active().get().user)
        dropped_follower.drop_follower(obj.creator_set.active().get().user)
        mail.outbox = []

        models.UserReviewStatus.objects.update(read=True)
        models.Reminder.objects.filter(review=obj).update(active=True)
        self.assertTrue(obj.update_state(constants.PAUSED))
        # refresh it
        obj = models.Review.objects.get(pk=obj.pk)
        self.assertEqual(obj.state, constants.PAUSED)
        event = obj.event_set.get(event_type__code=models.EventType.DEMO_PAUSED)
        self.assertEqual(event.event_type.code, event.event_type.DEMO_PAUSED)
        self.assertEqual(event.related_object, obj)
        self.assertEqual(event.user, obj.creator_set.active().get().user)
        self.assertEqual(
            models.UserReviewStatus.objects.filter(
                review=obj,
                read=False
            ).exclude(user=self.user).count(),
            5
        )
        self.assertEqual(len(mail.outbox), 3)
        self.assertEqual(
            models.Reminder.objects.filter(review=obj, active=False).count(),
            3
        )
        self.assertEqual(
            self.hook_patch_run.call_args_list[0][0][0],
            constants.CREATED
        )
        self.assertEqual(
            self.hook_patch_run.call_args_list[1][0][0],
            constants.PAUSED,
        )

    def test_review_state_change_closed(self):
        self.assertEqual(len(mail.outbox), 0)
        obj = models.Review.create_review(**self.default_review_kwargs)
        self.assertEqual(len(mail.outbox), 5)
        dropped_reviewer = obj.reviewer_set.all()[0]
        dropped_follower = obj.follower_set.all()[0]
        dropped_reviewer.drop_reviewer(obj.creator_set.active().get().user)
        dropped_follower.drop_follower(obj.creator_set.active().get().user)
        mail.outbox = []

        models.UserReviewStatus.objects.update(read=True)
        models.Reminder.objects.filter(review=obj).update(active=True)
        self.assertTrue(obj.update_state(constants.CLOSED))
        # refresh it
        obj = models.Review.objects.get(pk=obj.pk)
        self.assertEqual(obj.state, constants.CLOSED)
        event = obj.event_set.get(event_type__code=models.EventType.DEMO_CLOSED)
        self.assertEqual(event.event_type.code, event.event_type.DEMO_CLOSED)
        self.assertEqual(event.related_object, obj)
        self.assertEqual(event.user, obj.creator_set.get().user)
        self.assertEqual(
            models.UserReviewStatus.objects.filter(
                review=obj,
                read=False
            ).exclude(user=self.user).count(),
            5
        )
        self.assertEqual(len(mail.outbox), 3)
        self.assertEqual(
            models.Reminder.objects.filter(review=obj, active=False).count(),
            3
        )
        self.assertEqual(
            self.hook_patch_run.call_args_list[0][0][0],
            constants.CREATED
        )
        self.assertEqual(
            self.hook_patch_run.call_args_list[1][0][0],
            constants.CLOSED,
        )

    def test_review_state_change_aborted(self):
        self.assertEqual(len(mail.outbox), 0)
        obj = models.Review.create_review(**self.default_review_kwargs)
        self.assertEqual(len(mail.outbox), 5)
        mail.outbox = []
        models.UserReviewStatus.objects.update(read=True)
        models.Reminder.objects.filter(review=obj).update(active=True)
        self.assertTrue(obj.update_state(constants.ABORTED))
        # refresh it
        obj = models.Review.objects.get(pk=obj.pk)
        self.assertEqual(obj.state, constants.ABORTED)
        event = obj.event_set.get(event_type__code=models.EventType.DEMO_ABORTED)
        self.assertEqual(event.event_type.code, event.event_type.DEMO_ABORTED)
        self.assertEqual(event.related_object, obj)
        self.assertEqual(event.user, obj.creator_set.get().user)
        self.assertEqual(
            models.UserReviewStatus.objects.filter(
                review=obj,
                read=False
            ).exclude(user=self.user).count(),
            5
        )
        self.assertEqual(len(mail.outbox), 5)
        self.assertEqual(
            models.Reminder.objects.filter(review=obj, active=False).count(),
            4
        )
        self.assertEqual(
            self.hook_patch_run.call_args_list[0][0][0],
            constants.CREATED
        )
        self.assertEqual(
            self.hook_patch_run.call_args_list[1][0][0],
            constants.ABORTED
        )

    def test_review_state_change_paused_to_open(self):
        self.assertEqual(len(mail.outbox), 0)
        obj = models.Review.create_review(**self.default_review_kwargs)
        self.assertEqual(len(mail.outbox), 5)
        mail.outbox = []

        obj.update_state(constants.PAUSED)
        self.assertEqual(len(mail.outbox), 5)
        mail.outbox = []

        models.UserReviewStatus.objects.update(read=True)
        models.Reminder.objects.filter(review=obj).update(active=False)
        self.assertTrue(obj.update_state(constants.OPEN))
        # refresh it
        obj = models.Review.objects.get(pk=obj.pk)
        self.assertEqual(obj.state, constants.OPEN)
        event = obj.event_set.get(event_type__code=models.EventType.DEMO_OPENED)
        self.assertEqual(event.event_type.code, event.event_type.DEMO_OPENED)
        self.assertEqual(event.related_object, obj)
        self.assertEqual(event.user, obj.creator_set.get().user)
        self.assertEqual(
            models.UserReviewStatus.objects.filter(
                review=obj,
                read=False
            ).exclude(user=self.user).count(),
            5
        )
        self.assertEqual(len(mail.outbox), 5)
        self.assertEqual(
            models.Reminder.objects.filter(review=obj, active=True).count(),
            4
        )
        self.assertEqual(
            self.hook_patch_run.call_args_list[0][0][0],
            constants.CREATED
        )
        self.assertEqual(
            self.hook_patch_run.call_args_list[1][0][0],
            constants.PAUSED,
        )
        self.assertEqual(
            self.hook_patch_run.call_args_list[2][0][0],
            constants.REOPENED,
        )

    def test_review_state_change_closed_to_open(self):
        self.assertEqual(len(mail.outbox), 0)
        obj = models.Review.create_review(**self.default_review_kwargs)
        self.assertEqual(len(mail.outbox), 5)
        mail.outbox = []

        obj.update_state(constants.CLOSED)
        self.assertEqual(len(mail.outbox), 5)
        mail.outbox = []

        models.UserReviewStatus.objects.update(read=True)
        models.Reminder.objects.filter(review=obj).update(active=False)
        self.assertTrue(obj.update_state(constants.OPEN))
        # refresh it
        obj = models.Review.objects.get(pk=obj.pk)
        self.assertEqual(obj.state, constants.OPEN)
        event = obj.event_set.get(event_type__code=models.EventType.DEMO_OPENED)
        self.assertEqual(event.event_type.code, event.event_type.DEMO_OPENED)
        self.assertEqual(event.related_object, obj)
        self.assertEqual(event.user, obj.creator_set.get().user)
        self.assertEqual(
            models.UserReviewStatus.objects.filter(
                review=obj,
                read=False
            ).exclude(user=self.user).count(),
            5
        )
        self.assertEqual(len(mail.outbox), 5)
        self.assertEqual(
            models.Reminder.objects.filter(review=obj, active=True).count(),
            4
        )
        self.assertEqual(
            self.hook_patch_run.call_args_list[0][0][0],
            constants.CREATED
        )
        self.assertEqual(
            self.hook_patch_run.call_args_list[1][0][0],
            constants.CLOSED,
        )
        self.assertEqual(
            self.hook_patch_run.call_args_list[2][0][0],
            constants.REOPENED,
        )

    def test_review_state_change_aborted_to_open(self):
        self.assertEqual(len(mail.outbox), 0)
        obj = models.Review.create_review(**self.default_review_kwargs)
        self.assertEqual(len(mail.outbox), 5)
        mail.outbox = []
        obj.update_state(constants.ABORTED)
        self.assertEqual(len(mail.outbox), 5)
        mail.outbox = []

        models.UserReviewStatus.objects.update(read=True)
        models.Reminder.objects.filter(review=obj).update(active=False)
        self.assertTrue(obj.update_state(constants.OPEN))
        # refresh it
        obj = models.Review.objects.get(pk=obj.pk)
        self.assertEqual(obj.state, constants.OPEN)
        event = obj.event_set.get(event_type__code=models.EventType.DEMO_OPENED)
        self.assertEqual(event.event_type.code, event.event_type.DEMO_OPENED)
        self.assertEqual(event.related_object, obj)
        self.assertEqual(event.user, obj.creator_set.get().user)
        self.assertEqual(
            models.UserReviewStatus.objects.filter(
                review=obj,
                read=False
            ).exclude(user=self.user).count(),
            5
        )
        self.assertEqual(len(mail.outbox), 5)
        self.assertEqual(
            models.Reminder.objects.filter(review=obj, active=True).count(),
            4
        )
        self.assertEqual(
            self.hook_patch_run.call_args_list[0][0][0],
            constants.CREATED
        )
        self.assertEqual(
            self.hook_patch_run.call_args_list[1][0][0],
            constants.ABORTED
        )
        self.assertEqual(
            self.hook_patch_run.call_args_list[2][0][0],
            constants.REOPENED,
        )

    def test_reviewer_status_count_properties_reviewing(self):
        review = models.Review.create_review(**self.default_review_kwargs)
        self.assertEqual(review.reviewing_count, 3)
        self.assertEqual(review.approved_count, 0)
        self.assertEqual(review.rejected_count, 0)

    def test_reviewer_status_count_properties_approved(self):
        review = models.Review.create_review(**self.default_review_kwargs)
        review.reviewer_set.update(status=constants.APPROVED)
        self.assertEqual(review.reviewing_count, 0)
        self.assertEqual(review.approved_count, 3)
        self.assertEqual(review.rejected_count, 0)

    def test_reviewer_status_count_properties_rejected(self):
        review = models.Review.create_review(**self.default_review_kwargs)
        review.reviewer_set.update(status=constants.REJECTED)
        self.assertEqual(review.reviewing_count, 0)
        self.assertEqual(review.approved_count, 0)
        self.assertEqual(review.rejected_count, 3)

    def test_reviewer_status_count_properties_deleted(self):
        review = models.Review.create_review(**self.default_review_kwargs)
        reviewer = review.reviewer_set.all()[0]
        reviewer.drop_reviewer(review.creator_set.get().user)
        self.assertEqual(review.reviewing_count, 2)
        self.assertEqual(review.approved_count, 0)
        self.assertEqual(review.rejected_count, 0)

        review.reviewer_set.update(status=constants.REJECTED)
        self.assertEqual(review.reviewing_count, 0)
        self.assertEqual(review.approved_count, 0)
        self.assertEqual(review.rejected_count, 2)

        review.reviewer_set.update(status=constants.APPROVED)
        self.assertEqual(review.reviewing_count, 0)
        self.assertEqual(review.approved_count, 2)
        self.assertEqual(review.rejected_count, 0)

    def test_review_to_json(self):
        review = models.Review.create_review(**self.default_review_kwargs)
        review_json = review.to_json()
        self.assertEqual(review_json['title'], review.title)
        self.assertEqual(
            review_json['creators'],
            [review.creator_set.get().to_json()]
        )
        reviewers = []
        for reviewer in review.reviewer_set.active():
            reviewers.append(reviewer.to_json())

        followers = []
        for follower in review.follower_set.active():
            followers.append(follower.to_json())

        self.assertEqual(review_json['reviewers'], reviewers)
        self.assertEqual(review_json['followers'], followers)
        self.assertEqual(review_json['description'], review.description)
        self.assertEqual(review_json['case_link'], review.case_link)
        self.assertEqual(review_json['state'], review.state)
        self.assertEqual(review_json['reviewer_state'], review.reviewer_state)
        self.assertEqual(review_json['is_public'], review.is_public)
        self.assertEqual(review_json['project'], {
            'id': review.project.pk,
            'slug': review.project.slug,
            'name': review.project.name,
        })
        self.assertEqual(review_json['url'], review.get_absolute_url())
        self.assertEqual(review_json['reviewing_count'], review.reviewing_count)
        self.assertEqual(review_json['approved_count'], review.approved_count)
        self.assertEqual(review_json['rejected_count'], review.rejected_count)
        self.assertEqual(review_json['active_issues_count'], 0)
        self.assertEqual(review_json['resolved_issues_count'], 0)

    def test_review_to_json_hides_inactive_reviews_followers(self):
        review = models.Review.create_review(**self.default_review_kwargs)
        self.assertEqual(review.reviewer_set.count(), 3)
        self.assertEqual(review.follower_set.count(), 2)
        # Drop a reviewer and follower
        reviewer = review.reviewer_set.all()[0]
        follower = review.follower_set.all()[0]
        reviewer.drop_reviewer(review.creator_set.get().user)
        follower.drop_follower(review.creator_set.get().user)
        # Verify things are as they should be
        self.assertEqual(review.reviewer_set.count(), 3)
        self.assertEqual(review.follower_set.count(), 2)
        self.assertEqual(review.reviewer_set.active().count(), 2)
        self.assertEqual(review.follower_set.active().count(), 1)

        review_json = review.to_json()
        reviewers = []
        for reviewer in review.reviewer_set.active():
            reviewers.append(reviewer.to_json())

        followers = []
        for follower in review.follower_set.active():
            followers.append(follower.to_json())

        self.assertEqual(review_json['reviewers'], reviewers)
        self.assertEqual(review_json['followers'], followers)
        self.assertEqual(len(review_json['reviewers']), 2)
        self.assertEqual(len(review_json['followers']), 1)

    @patch('demotime.tasks.fire_webhook')
    def test_trigger_webhooks_fires(self, task_patch):
        review = models.Review.create_review(**self.default_review_kwargs)
        hook = models.WebHook.objects.create(
            project=review.project,
            trigger_event=constants.CREATED,
            target='http://www.example.com'
        )
        self.hook_patch.stop()

        review.trigger_webhooks(constants.CREATED)
        task_patch.delay.assert_called_once_with(
            review.pk,
            hook.pk,
            None
        )
        self.hook_patch.start()

    @patch('demotime.tasks.fire_webhook')
    def test_trigger_webhooks_skipped(self, task_patch):
        review = models.Review.create_review(**self.default_review_kwargs)
        models.WebHook.objects.create(
            project=review.project,
            trigger_event=constants.CLOSED,
            target='http://www.example.com'
        )
        self.hook_patch.stop()

        review.trigger_webhooks(constants.CREATED)
        self.assertFalse(task_patch.called)
        self.hook_patch.start()
