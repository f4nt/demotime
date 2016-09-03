from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

from demotime.models.base import BaseModel


class EventType(BaseModel):

    DEMO_CREATED = 'demo-created'
    REVISION_ADDED = 'revision-added'
    COMMENT_ADDED = 'comment-added'
    REVIEWER_APPROVED = 'reviewer-approved'
    REVIEWER_REJECTED = 'reviewer-rejected'
    REVIEWER_RESET = 'reviewer-reset'
    DEMO_OPENED = 'demo-opened'
    DEMO_CLOSED = 'demo-closed'
    DEMO_ABORTED = 'demo-aborted'
    REVIEWER_ADDED = 'reviewer-added'
    REVIEWER_REMOVED = 'reviewer-removed'
    FOLLOWER_ADDED = 'follower-added'
    FOLLOWER_REMOVED = 'follower-removed'

    name = models.CharField(max_length=128)
    code = models.SlugField(unique=True)

    def __str__(self):
        return 'EventType: {}'.format(self.name)

    @classmethod
    def create_event_type(cls, name, code):
        return cls.objects.create(
            name=name,
            code=code
        )

    def to_json(self):
        return {
            'id': self.pk,
            'name': self.name,
            'code': self.code,
        }


class Event(BaseModel):

    COMMENT = 'comment'
    FOLLOWER = 'follower'
    REVIEW = 'review'
    REVIEWER = 'reviewer'
    REVISION = 'revision'

    RELATED_TYPES = [
        COMMENT, FOLLOWER, REVIEW, REVIEWER, REVISION
    ]

    RELATED_TYPE_CHOICES = (
        (COMMENT, 'Comment'),
        (FOLLOWER, 'Follower'),
        (REVIEW, 'Review'),
        (REVIEWER, 'Reviewer'),
        (REVISION, 'Revision')
    )

    project = models.ForeignKey('Project')
    event_type = models.ForeignKey('EventType')
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    related_object = GenericForeignKey('content_type', 'object_id')
    related_type = models.CharField(max_length=64, choices=RELATED_TYPE_CHOICES)
    user = models.ForeignKey('auth.User')

    def __str__(self):
        return 'Event {} on {}'.format(self.event_type.name, self.related_object)

    @classmethod
    def create_event(cls, project, event_type_code, related_object, user):
        event_type = EventType.objects.get(code=event_type_code)
        related_type = related_object._meta.model_name  # pylint: disable=protected-access
        if related_type not in cls.RELATED_TYPES:
            raise RuntimeError('Invalid related object passed to Event creation')

        return cls.objects.create(
            project=project,
            event_type=event_type,
            related_object=related_object,
            related_type=related_type,
            user=user,
        )

    def to_json(self):
        return {
            'project': {
                'id': self.project.pk,
                'slug': self.project.slug,
                'name': self.project.name,
            },
            'event_type': self.event_type.to_json(),
            'related_type': self.related_type,
            'related_type_pretty': self.get_related_type_display(),
            'related_object': self.related_object.to_json(),
        }

    class Meta:
        index_together = [
            ('content_type', 'object_id'),
        ]
        get_latest_by = 'created'
        ordering = ('-created',)
