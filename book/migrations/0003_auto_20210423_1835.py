# Generated by Django 3.1.7 on 2021-04-23 17:35

from django.db import migrations
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('book', '0002_category'),
    ]

    operations = [
        migrations.AlterField(
            model_name='book',
            name='cleanData',
            field=jsonfield.fields.JSONField(),
        ),
        migrations.AlterField(
            model_name='book',
            name='unCleanData',
            field=jsonfield.fields.JSONField(),
        ),
    ]
