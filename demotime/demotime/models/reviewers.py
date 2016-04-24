from django.db import models

from demotime.models.base import BaseModel
from demotime.constants import (
    REVIEWING,
    APPROVED,
    REJECTED
)
from .messages import Message
from .reminders import Reminder


class Reviewer(BaseModel):

    STATUS_CHOICES = (
        (REVIEWING, REVIEWING.capitalize()),
        (REJECTED, REJECTED.capitalize()),
        (APPROVED, APPROVED.capitalize())
    )

    review = models.ForeignKey('Review')
    reviewer = models.ForeignKey('auth.User')
    status = models.CharField(
        max_length=128, choices=STATUS_CHOICES,
        default='reviewing', db_index=True
    )

    def __unicode__(self):
        return u'{} Follower on {}'.format(
            self.reviewer_display_name,
            self.review.title,
        )

    @property
    def reviewer_display_name(self):
        return self.reviewer.userprofile.display_name or self.reviewer.username

    @classmethod
    def create_reviewer(cls, review, reviewer, notify_reviewer=False, notify_creator=False):
        obj = cls.objects.create(
            review=review,
            reviewer=reviewer,
            status=REVIEWING
        )

        if notify_reviewer:
            obj._send_reviewer_message(notify_reviewer=True, notify_creator=False)

        if notify_creator:
            obj._send_reviewer_message(notify_reviewer=False, notify_creator=True)

        return obj

    def _send_reviewer_message(self, deleted=False, notify_reviewer=False, notify_creator=False):
        if deleted:
            title = 'Deleted as reviewer on: {}'.format(self.review.title)
            receipient = self.reviewer
        elif notify_reviewer:
            title = 'You have been added as a reviewer on: {}'.format(
                self.review.title
            )
            receipient = self.reviewer
        elif notify_creator:
            title = '{} has been added as a reviewer on: {}'.format(
                self.reviewer_display_name,
                self.review.title
            )
            receipient = self.review.creator
        else:
            raise Exception('No receipient for message in reviewer message')

        context = {
            'receipient': receipient,
            'url': self.review.get_absolute_url(),
            'title': self.review.title,
            'deleted': deleted,
            'creator': notify_creator,
            'reviewer': self,
        }
        Message.send_system_message(
            title,
            'demotime/messages/reviewer.html',
            context,
            receipient,
            revision=self.review.revision,
        )

    def set_status(self, status):
        old_status = self.status
        self.status = status
        self.save(update_fields=['status', 'modified'])

        reminder_active = status == REVIEWING
        Reminder.set_activity(self.review, self.reviewer, reminder_active)

        # Send a message if this isn't the last person to approve/reject
        all_statuses = self.review.reviewer_set.values_list('status', flat=True)
        consensus = all(x == APPROVED for x in all_statuses) or all(
            x == REJECTED for x in all_statuses)
        if status != old_status and not consensus:
            status_display = '{} {}'.format(
                'resumed' if status == REVIEWING else 'has',
                self.status,
            )
            title = '{} {} your review: {}'.format(
                self.reviewer_display_name,
                status_display,
                self.review.title
            )
            context = {
                'reviewer': self,
                'creator': self.review.creator,
                'url': self.review.get_absolute_url(),
                'title': self.review.title,
            }
            Message.send_system_message(
                title,
                'demotime/messages/reviewer_status_change.html',
                context,
                self.review.creator,
                revision=self.review.revision
            )
        return self.review.update_reviewer_state()
