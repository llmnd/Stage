# Generated by Django 5.2.3 on 2025-06-20 06:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stages', '0002_alter_candidature_options_candidature_feedback_ia_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='conventiondestage',
            name='signature_entreprise',
            field=models.ImageField(blank=True, null=True, upload_to='signatures/'),
        ),
        migrations.AddField(
            model_name='conventiondestage',
            name='signature_etudiant',
            field=models.ImageField(blank=True, null=True, upload_to='signatures/'),
        ),
    ]
