import bdateutil

from django.db import models
from django.utils import timezone

from demotime import helpers
from demotime.models.base import BaseModel
from demotime.models import Setting


def get_reminder_days(project):
    days = Setting.objects.get_value(
        project=project,
        key=Setting.REMINDER_DAYS
    )
    return timezone.now() + bdateutil.relativedelta(
        bdays=days,
    )


class Reminder(BaseModel):

    CREATOR = 'creator'
    REVIEWER = 'reviewer'

    REMINDER_TYPES = (
        (CREATOR, CREATOR.capitalize()),
        (REVIEWER, REVIEWER.capitalize()),
    )

    review = models.ForeignKey('Review')
    user = models.ForeignKey('auth.User')
    reminder_type = models.CharField(
        max_length=256,
        choices=REMINDER_TYPES,
        db_index=True,
    )
    remind_at = models.DateTimeField()
    active = models.BooleanField(default=True)

    def __unicode__(self):
        return '{} Reminder for {} on {}'.format(
            self.reminder_type,
            self.user.username,
            self.review.title
        )

    @classmethod
    def create_reminder(cls, review, user, reminder_type, remind_at=None):
        if not remind_at:
            remind_at = get_reminder_days(review.project)
        obj, _ = cls.objects.get_or_create(
            review=review,
            user=user,
            defaults={
                'reminder_type': reminder_type,
                'remind_at': remind_at,
            }
        )
        obj.active = True
        obj.save()
        return obj

    @classmethod
    def create_reminders_for_review(cls, review):
        for creator in review.creator_set.active():
            cls.create_reminder(
                review=review,
                user=creator.user,
                reminder_type=cls.CREATOR
            )
        for reviewer in review.reviewer_set.active():
            cls.create_reminder(
                review=review,
                user=reviewer.reviewer,
                reminder_type=cls.REVIEWER
            )

    @classmethod
    def update_reminders_for_review(cls, review):
        remind_at = get_reminder_days(review.project)
        reviewer_pks = review.reviewer_set.active().values_list(
            'reviewer__pk', flat=True)
        creator_pks = review.creator_set.active().values_list(
            'user__pk', flat=True)
        reminder_user_pks = tuple(reviewer_pks) + tuple(creator_pks)
        cls.objects.filter(
            review=review, user__pk__in=reminder_user_pks
        ).update(
            remind_at=remind_at,
            active=True
        )
        cls.objects.filter(review=review).exclude(
            user__pk__in=reminder_user_pks
        ).delete()

    @classmethod
    def update_reminder_activity_for_review(cls, review, active=False):
        if active:
            cls.objects.filter(review=review).update(
                active=active,
                remind_at=get_reminder_days(review.project),
            )
        else:
            cls.objects.filter(review=review).update(active=active)

    @classmethod
    def set_activity(cls, review, user, active=False):
        if active:
            cls.objects.filter(review=review, user=user).update(
                active=active,
                remind_at=get_reminder_days(review.project),
            )
        else:
            cls.objects.filter(review=review, user=user).update(active=active)

    def send_reminder(self):
        context = {
            'reminder': self,
            'url': self.review.get_absolute_url(),
        }
        title = 'Reminder: {}'.format(self.review.title)
        helpers.send_system_message(
            title,
            'demotime/messages/reminder.html',
            context,
            self.user,
            revision=self.review.revision,
        )
        self.remind_at = get_reminder_days(self.review.project)
        self.save(update_fields=['remind_at'])

    class Meta:
        unique_together = (
            ('review', 'user')
        )
