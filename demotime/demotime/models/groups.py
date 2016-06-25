from django.db import models

from demotime.models.base import BaseModel


class GroupType(BaseModel):

    name = models.CharField(max_length=128)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return '{}'.format(self.slug)

    @classmethod
    def create_group_type(cls, name, slug):
        return cls.objects.create(
            name=name, slug=slug
        )

    class Meta:
        ordering = ('name',)


class Group(BaseModel):

    name = models.CharField(max_length=128)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    group_type = models.ForeignKey('GroupType')
    members = models.ManyToManyField('auth.User', through='GroupMember')

    def __str__(self):
        return 'Group: {}'.format(self.slug)

    @classmethod
    def create_group(cls, name, slug, description, group_type, members=None):
        members = members or []
        obj = cls.objects.create(
            name=name,
            slug=slug,
            description=description,
            group_type=group_type,
        )
        for member in members:
            GroupMember.create_group_member(
                user=member['user'],
                group=obj,
                is_admin=member['is_admin']
            )
        return obj

    class Meta:
        ordering = ('name',)


class GroupMember(BaseModel):

    user = models.ForeignKey('auth.User')
    group = models.ForeignKey('Group')
    is_admin = models.BooleanField(default=False)

    def __str__(self):
        return 'GroupMember: {} - {}'.format(
            self.group.slug,
            self.user.userprofile.name
        )

    @classmethod
    def create_group_member(cls, user, group, is_admin=False):
        obj, created = cls.objects.get_or_create(
            user=user,
            group=group,
        )
        if not created:
            is_admin = obj.is_admin
        obj.is_admin = is_admin
        obj.save(update_fields=['is_admin'])
        return obj

    class Meta:
        unique_together = ('user', 'group')
        ordering = ('user__username',)
