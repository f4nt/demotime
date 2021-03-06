# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-07-01 20:39
from __future__ import unicode_literals

import django.contrib.auth.models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0007_alter_validators_add_error_messages'),
        ('demotime', '0029_auto_20160424_2233'),
    ]

    operations = [
        migrations.CreateModel(
            name='WebHook',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('target', models.CharField(max_length=1024)),
                ('trigger_event', models.CharField(choices=[('created', 'Demo Created'), ('closed', 'Demo Closed'), ('aborted', 'Demo Aborted'), ('comment', 'Comment Added'), ('updated', 'Demo Updated')], db_index=True, max_length=64)),
            ],
            options={
                'abstract': False,
                'ordering': ['-created'],
            },
        ),
        migrations.CreateModel(
            name='UserProxy',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('auth.user',),
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.AlterModelOptions(
            name='group',
            options={'ordering': ('name',)},
        ),
        migrations.AlterModelOptions(
            name='groupmember',
            options={'ordering': ('user__username',)},
        ),
        migrations.AlterModelOptions(
            name='grouptype',
            options={'ordering': ('name',)},
        ),
        migrations.RemoveField(
            model_name='project',
            name='members',
        ),
        migrations.AddField(
            model_name='project',
            name='token',
            field=models.CharField(blank=True, max_length=256),
        ),
        migrations.AlterField(
            model_name='attachment',
            name='attachment_type',
            field=models.CharField(choices=[('', '-----'), ('image', 'Image'), ('document', 'Document'), ('movie', 'Movie/Screencast'), ('audio', 'Audio'), ('other', 'Other')], db_index=True, max_length=128),
        ),
        migrations.AlterField(
            model_name='reminder',
            name='reminder_type',
            field=models.CharField(choices=[('creator', 'Creator'), ('reviewer', 'Reviewer')], db_index=True, max_length=256),
        ),
        migrations.AlterField(
            model_name='review',
            name='case_link',
            field=models.CharField(blank=True, max_length=2048, verbose_name='Case URL'),
        ),
        migrations.AlterField(
            model_name='review',
            name='reviewer_state',
            field=models.CharField(choices=[('reviewing', 'Reviewing'), ('approved', 'Approved'), ('rejected', 'Rejected')], db_index=True, default='reviewing', max_length=128),
        ),
        migrations.AlterField(
            model_name='review',
            name='state',
            field=models.CharField(choices=[('open', 'Open'), ('closed', 'Closed'), ('aborted', 'Aborted')], db_index=True, default='open', max_length=128),
        ),
        migrations.AlterField(
            model_name='reviewer',
            name='status',
            field=models.CharField(choices=[('reviewing', 'Reviewing'), ('rejected', 'Rejected'), ('approved', 'Approved')], db_index=True, default='reviewing', max_length=128),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='user_type',
            field=models.CharField(choices=[('user', 'User'), ('system', 'System')], default='user', max_length=1024),
        ),
        migrations.AlterUniqueTogether(
            name='groupmember',
            unique_together=set([('user', 'group')]),
        ),
        migrations.AddField(
            model_name='webhook',
            name='project',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='demotime.Project'),
        ),
    ]
