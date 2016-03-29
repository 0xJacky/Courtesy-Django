# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-03-29 08:54
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('qr_gift', '0022_auto_20160329_0851'),
    ]

    operations = [
        migrations.AlterField(
            model_name='daliynewsmodel',
            name='string',
            field=models.TextField(null=True),
        ),
        migrations.AlterField(
            model_name='daliynewsmodel',
            name='style',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='qr_gift.DaliyNewsStyleModel'),
        ),
    ]
