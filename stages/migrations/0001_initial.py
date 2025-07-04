# Generated by Django 5.2.2 on 2025-06-14 16:52

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Entreprise',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom_entreprise', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True)),
                ('secteur', models.CharField(blank=True, max_length=255)),
                ('adresse', models.CharField(blank=True, max_length=255)),
                ('logo_url', models.URLField(blank=True)),
                ('site_web', models.URLField(blank=True)),
                ('telephone', models.CharField(blank=True, max_length=20)),
                ('email_contact', models.EmailField(blank=True, max_length=254)),
                ('reseaux_sociaux', models.TextField(blank=True, help_text='Liens vers LinkedIn, Facebook, etc.')),
                ('taille', models.CharField(blank=True, help_text='Ex: PME, grande entreprise, startup', max_length=100)),
                ('nombre_employes', models.PositiveIntegerField(blank=True, null=True)),
                ('ville', models.CharField(blank=True, max_length=100)),
                ('pays', models.CharField(blank=True, max_length=100)),
                ('date_creation', models.DateField(blank=True, null=True)),
                ('statut_juridique', models.CharField(blank=True, help_text='Ex: SARL, SAS, SA, etc.', max_length=100)),
                ('est_valide', models.BooleanField(default=False)),
                ('realisations', models.TextField(blank=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Etudiant',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom_complet', models.CharField(max_length=100)),
                ('email', models.EmailField(default='temp@example.com', max_length=254, unique=True)),
                ('telephone', models.CharField(blank=True, max_length=20, null=True)),
                ('universite', models.CharField(max_length=100)),
                ('niveau_etude', models.CharField(choices=[('bac', 'Baccalauréat'), ('bac+2', 'Bac+2 (BTS, DUT)'), ('bac+3', 'Licence'), ('bac+5', 'Master'), ('bac+8', 'Doctorat')], max_length=20)),
                ('domaine_etude', models.CharField(choices=[('info', 'Informatique'), ('gestion', 'Gestion'), ('droit', 'Droit'), ('sante', 'Santé'), ('ingenieur', 'Ingénierie'), ('autre', 'Autre')], max_length=20)),
                ('competences', models.TextField(blank=True, null=True)),
                ('adresse', models.TextField(blank=True, null=True)),
                ('realisations', models.TextField(blank=True, null=True)),
                ('cv', models.FileField(blank=True, null=True, upload_to='cvs/')),
                ('est_valide', models.BooleanField(default=False)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='OffreDeStage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titre', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('domaine', models.CharField(max_length=100)),
                ('competences_requises', models.TextField(blank=True)),
                ('date_publication', models.DateTimeField(auto_now_add=True)),
                ('duree', models.PositiveIntegerField(blank=True, help_text='Durée en mois', null=True)),
                ('date_debut', models.DateField(blank=True, help_text='Date prévue de début', null=True)),
                ('entreprise', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='stages.entreprise')),
            ],
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('admin', 'Admin'), ('entreprise', 'Entreprise'), ('etudiant', 'Étudiant')], max_length=20)),
                ('is_validated', models.BooleanField(default=False)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Candidature',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_postulation', models.DateTimeField(auto_now_add=True)),
                ('statut', models.CharField(choices=[('en_attente', 'En attente'), ('acceptee', 'Acceptée'), ('refusee', 'Refusée')], default='en_attente', max_length=20)),
                ('message', models.TextField(blank=True, null=True)),
                ('cv', models.FileField(blank=True, null=True, upload_to='candidatures_cvs/')),
                ('etudiant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='stages.etudiant')),
                ('offre', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='stages.offredestage')),
            ],
            options={
                'unique_together': {('etudiant', 'offre')},
            },
        ),
    ]
