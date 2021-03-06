from django.db import models
from django.contrib.contenttypes.fields import GenericRelation

from demotime import helpers
from demotime.models.base import BaseModel
from demotime.models import Event, EventType


class FollowerManager(models.Manager):

    def active(self):
        return self.filter(is_active=True)


class Follower(BaseModel):

    review = models.ForeignKey('Review')
    user = models.ForeignKey('auth.User')
    events = GenericRelation('Event')
    is_active = models.BooleanField(default=True, db_index=True)

    objects = FollowerManager()

    @property
    def display_name(self):
        return '{}'.format(self.user.userprofile.display_name or self.user.username)

    def __str__(self):
        return '{} Follower on {}'.format(
            self.display_name,
            self.review.title,
        )

    def to_json(self):
        return {
            'name': self.user.userprofile.name,
            'user_pk': self.user.pk,
            'user_profile_url': self.user.userprofile.get_absolute_url(),
            'follower_pk': self.pk,
            'review_pk': self.review.pk,
            'created': self.created.isoformat(),
            'modified': self.modified.isoformat(),
        }

    def create_follower_event(self, user):
        Event.create_event(
            project=self.review.project,
            event_type_code=EventType.FOLLOWER_ADDED,
            related_object=self,
            user=user
        )

    @classmethod
    def create_follower(cls, review, user, creator,
                        skip_notifications=False, draft=False):
        existing_reviewer = review.reviewer_set.active().filter(
            reviewer=user
        )
        if existing_reviewer.exists():
            return existing_reviewer.get()

        obj, _ = cls.objects.get_or_create(
            review=review,
            user=user
        )
        obj.is_active = True
        obj.save()
        if not draft:
            obj.create_follower_event(creator)

            if skip_notifications or draft:
                notify_follower = notify_creator = False
            else:
                notify_follower = creator != user
                notify_creator = not review.creator_set.active().filter(
                    user=creator
                ).exists()
            if notify_follower:
                # pylint: disable=protected-access
                obj._send_follower_message(notify_follower=True)

            if notify_creator:
                # pylint: disable=protected-access
                obj._send_follower_message(notify_creator=True)

        return obj

    def drop_follower(self, dropper, draft=False):  # pylint: disable=unused-argument
        if draft:
            self.delete()
        else:
            Event.create_event(
                project=self.review.project,
                event_type_code=EventType.FOLLOWER_REMOVED,
                related_object=self,
                user=dropper
            )
        self.is_active = False
        self.save()

    def _send_follower_message(self, notify_follower=False, notify_creator=False):
        if not notify_follower and not notify_creator:
            raise Exception('No receipient for message in follower message')

        title_template = '{} {} now following {}'
        title = title_template.format(
            self.display_name,
            'is',
            self.review.title
        )

        receipients = [
            creator.user for creator in self.review.creator_set.active()
        ]
        if notify_follower:
            receipients = [self.user]
            title = title_template.format(
                'You',
                'are',
                self.review.title
            )

        for receipient in receipients:
            context = {
                'receipient': receipient,
                'url': self.review.get_absolute_url(),
                'title': self.review.title,
                'follower': self,
                'is_follower': notify_follower,
            }
            helpers.send_system_message(
                title,
                'demotime/messages/follower.html',
                context,
                receipient,
                revision=self.review.revision,
            )

    class Meta:
        unique_together = (
            ('review', 'user')
        )
