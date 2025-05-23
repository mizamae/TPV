# Generated by Django 5.2.1 on 2025-05-21 14:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('UsersAPP', '0004_alter_user_options_alter_user_identifier'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customer',
            name='email',
            field=models.EmailField(blank=True, max_length=254, null=True, verbose_name='Email address'),
        ),
        migrations.AlterField(
            model_name='user',
            name='identifier',
            field=models.CharField(max_length=20, unique=True),
        ),
    ]
