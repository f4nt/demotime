from django.core import mail

from demotime import models
from demotime.tests import BaseTestCase


class TestFollowerModels(BaseTestCase):

    def setUp(self):
        super(TestFollowerModels, self).setUp()
        review_kwargs = self.default_review_kwargs.copy()
        review_kwargs['followers'] = []
        self.review = models.Review.create_review(**review_kwargs)

    def test_create_follower(self):
        self.assertEqual(self.review.follower_set.count(), 0)
        self.assertEqual(self.review.reviewer_set.count(), 3)
        mail.outbox = []
        follower = self.followers[0]
        follower_obj = models.Follower.create_follower(
            self.review, follower, self.user, True
        )

        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(self.review.follower_set.count(), 1)
        self.assertEqual(follower_obj.review, self.review)
        self.assertEqual(follower_obj.user, follower)
        self.assertTrue(follower_obj.is_active)
        self.assertEqual(
            follower_obj.__str__(),
            '{} Follower on {}'.format(follower_obj.display_name, self.review.title)
        )
        event = follower_obj.events.get(
            event_type__code=models.EventType.FOLLOWER_ADDED
        )
        self.assertEqual(
            event.event_type.code, models.EventType.FOLLOWER_ADDED
        )
        self.assertEqual(event.user, self.user)
        self.assertEqual(event.related_object, follower_obj)

    def test_create_follower_draft(self):
        self.assertEqual(self.review.follower_set.count(), 0)
        self.assertEqual(self.review.reviewer_set.count(), 3)
        mail.outbox = []
        follower = self.followers[0]
        follower_obj = models.Follower.create_follower(
            self.review, follower, self.user, False, True
        )

        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(self.review.follower_set.count(), 1)
        self.assertEqual(follower_obj.review, self.review)
        self.assertEqual(follower_obj.user, follower)
        self.assertEqual(
            follower_obj.__str__(),
            '{} Follower on {}'.format(follower_obj.display_name, self.review.title)
        )
        event = follower_obj.events.filter(
            event_type__code=models.EventType.FOLLOWER_ADDED
        )
        self.assertFalse(event.exists())

    def test_create_follower_notify_follower(self):
        self.assertEqual(self.review.follower_set.count(), 0)
        self.assertEqual(self.review.reviewer_set.count(), 3)
        mail.outbox = []
        follower = self.followers[0]
        follower_obj = models.Follower.create_follower(
            self.review, follower, self.user
        )

        # We email on non-revision
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(self.review.follower_set.count(), 1)
        self.assertEqual(follower_obj.review, self.review)
        self.assertEqual(follower_obj.user, follower)
        event = follower_obj.events.get(
            event_type__code=models.EventType.FOLLOWER_ADDED
        )
        self.assertEqual(
            event.event_type.code, models.EventType.FOLLOWER_ADDED
        )
        self.assertEqual(event.user, self.user)
        self.assertEqual(event.related_object, follower_obj)

    def test_create_follower_notify_creator(self):
        self.assertEqual(self.review.follower_set.count(), 0)
        self.assertEqual(self.review.reviewer_set.count(), 3)
        mail.outbox = []
        follower = self.followers[0]
        follower_obj = models.Follower.create_follower(
            self.review, follower, follower
        )

        # We email on non-revision
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(self.review.follower_set.count(), 1)
        self.assertEqual(follower_obj.review, self.review)
        self.assertEqual(follower_obj.user, follower)
        event = follower_obj.events.get(
            event_type__code=models.EventType.FOLLOWER_ADDED
        )
        self.assertEqual(
            event.event_type.code, models.EventType.FOLLOWER_ADDED
        )
        self.assertEqual(event.user, follower_obj.user)
        self.assertEqual(event.related_object, follower_obj)

    def test_create_follower_with_reviewer(self):
        self.assertEqual(self.review.follower_set.count(), 0)
        self.assertEqual(self.review.reviewer_set.count(), 3)
        mail.outbox = []
        follower = self.test_users[0]
        follower_obj = models.Follower.create_follower(
            self.review, follower,
            self.review.creator_set.active().get().user, True
        )

        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(self.review.follower_set.count(), 0)
        self.assertTrue(isinstance(follower_obj, models.Reviewer))

    def test_create_follower_with_inactive_reviewer(self):
        self.assertEqual(self.review.follower_set.count(), 0)
        follower = self.test_users[0]
        reviewer = models.Reviewer.objects.get(review=self.review, reviewer=follower)
        reviewer.drop_reviewer(self.review.creator_set.active().get().user)
        follower_obj = models.Follower.create_follower(
            self.review, follower,
            self.review.creator_set.active().get().user, True
        )
        self.assertEqual(self.review.follower_set.count(), 1)

    def test_follower_to_json(self):
        review = models.Review.create_review(**self.default_review_kwargs)
        follower = review.follower_set.all()[0]
        follower_json = follower.to_json()
        self.assertEqual(follower_json['name'], follower.user.userprofile.name)
        self.assertEqual(follower_json['user_pk'], follower.user.pk)
        self.assertEqual(follower_json['follower_pk'], follower.pk)
        self.assertEqual(follower_json['review_pk'], follower.review.pk)
        self.assertEqual(
            follower_json['user_profile_url'],
            follower.user.userprofile.get_absolute_url()
        )

    def test_drop_follower(self):
        follower = self.followers[0]
        follower_obj = models.Follower.create_follower(
            self.review, follower, self.user, True
        )
        follower_obj.drop_follower(self.review.creator_set.active().get().user)
        follower_obj.refresh_from_db()
        self.assertFalse(follower_obj.is_active)
        self.assertEqual(
            models.Event.objects.filter(
                event_type__code=models.EventType.FOLLOWER_REMOVED
            ).count(),
            1
        )
        event = models.Event.objects.get(
            event_type__code=models.EventType.FOLLOWER_REMOVED
        )
        self.assertEqual(event.user, self.review.creator_set.active().get().user)
        self.assertEqual(event.related_object, follower_obj)

    def test_readd_follower(self):
        follower = self.followers[0]
        follower_obj = models.Follower.create_follower(
            self.review, follower, self.user, True
        )
        follower_obj.drop_follower(self.review.creator_set.active().get().user)
        follower_obj.refresh_from_db()
        self.assertFalse(follower_obj.is_active)

        readded_follower = models.Follower.create_follower(
            self.review, follower, self.user, True
        )
        self.assertEqual(follower_obj.pk, readded_follower.pk)
        self.assertTrue(readded_follower.is_active)

    def test_drop_follower_draft(self):
        follower = self.followers[0]
        follower_obj = models.Follower.create_follower(
            self.review, follower, self.user, False, True
        )
        follower_obj.drop_follower(
            self.review.creator_set.active().get().user, True)
        self.assertEqual(
            models.Event.objects.filter(
                event_type__code=models.EventType.FOLLOWER_REMOVED
            ).count(),
            0
        )
