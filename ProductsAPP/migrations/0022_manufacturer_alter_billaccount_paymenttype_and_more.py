# Generated by Django 5.2.1 on 2025-05-26 10:45

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ProductsAPP', '0021_alter_combinationposition_ingredient_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Manufacturer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True, verbose_name='Name')),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.AlterField(
            model_name='billaccount',
            name='paymenttype',
            field=models.PositiveSmallIntegerField(choices=[(0, 'On cash'), (1, 'By credit card'), (2, 'By Bizum')], null=True, verbose_name='Payment'),
        ),
        migrations.AddField(
            model_name='consumible',
            name='manufacturer',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='consumibles', to='ProductsAPP.manufacturer', verbose_name='Manufacturer'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='product',
            name='manufacturer',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='products', to='ProductsAPP.manufacturer', verbose_name='Manufacturer'),
            preserve_default=False,
        ),
    ]
