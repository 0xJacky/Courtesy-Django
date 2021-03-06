# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-02-27 13:22
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('qr_gift', '0016_auto_20160226_1859'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='usermodel',
            name='last_login_at',
        ),
        migrations.AddField(
            model_name='cardmodel',
            name='local_template',
            field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name='commonresourcemodel',
            name='kind',
            field=models.CharField(default='', max_length=4),
        ),
        migrations.AlterField(
            model_name='cardmodel',
            name='banned',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='cardmodel',
            name='edited_count',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='cardmodel',
            name='first_read_at',
            field=models.DateTimeField(null=True),
        ),
        migrations.AlterField(
            model_name='cardmodel',
            name='id',
            field=models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='cardmodel',
            name='read_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='read_by_usermodel', to='qr_gift.UserModel'),
        ),
        migrations.AlterField(
            model_name='cardmodel',
            name='stars',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='cardmodel',
            name='template',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='qr_gift.TemplateModel'),
        ),
        migrations.AlterField(
            model_name='cardmodel',
            name='token',
            field=models.CharField(max_length=32, unique=True),
        ),
        migrations.AlterField(
            model_name='cardmodel',
            name='view_count',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='qrcodemodel',
            name='unique_id',
            field=models.CharField(max_length=32, unique=True),
        ),
    ]
