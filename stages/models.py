from django.db import models
from django.contrib.auth.models import User

# Rôles possibles
ROLES = (
    ('admin', 'Admin'),
    ('entreprise', 'Entreprise'),
    ('etudiant', 'Étudiant'),
)

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLES)
    is_validated = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} ({self.role})"


class Entreprise(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nom_entreprise = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    secteur = models.CharField(max_length=255, blank=True)
    adresse = models.CharField(max_length=255, blank=True)
    logo_url = models.URLField(blank=True)  # Utilise une URL au lieu d'une image
    site_web = models.URLField(blank=True)
    telephone = models.CharField(max_length=20, blank=True)
    email_contact = models.EmailField(blank=True)
    reseaux_sociaux = models.TextField(blank=True, help_text="Liens vers LinkedIn, Facebook, etc.")
    taille = models.CharField(max_length=100, blank=True, help_text="Ex: PME, grande entreprise, startup")
    nombre_employes = models.PositiveIntegerField(blank=True, null=True)
    ville = models.CharField(max_length=100, blank=True)
    pays = models.CharField(max_length=100, blank=True)
    date_creation = models.DateField(blank=True, null=True)
    statut_juridique = models.CharField(max_length=100, blank=True, help_text="Ex: SARL, SAS, SA, etc.")
    est_valide = models.BooleanField(default=False)
    realisations = models.TextField(blank=True)

    def __str__(self):
        return self.nom_entreprise


from django.db import models
from django.contrib.auth.models import User

from django.db import models

class Etudiant(models.Model):
    NIVEAU_ETUDE_CHOICES = [
        ('bac', 'Baccalauréat'),
        ('bac+2', 'Bac+2 (BTS, DUT)'),
        ('bac+3', 'Licence'),
        ('bac+5', 'Master'),
        ('bac+8', 'Doctorat'),
    ]
    
    DOMAINE_ETUDE_CHOICES = [
        ('info', 'Informatique'),
        ('gestion', 'Gestion'),
        ('droit', 'Droit'),
        ('sante', 'Santé'),
        ('ingenieur', 'Ingénierie'),
        ('autre', 'Autre'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nom_complet = models.CharField(max_length=100)
    email = models.EmailField(unique=True, default='temp@example.com')
    telephone = models.CharField(max_length=20, blank=True, null=True)
    universite = models.CharField(max_length=100)
    niveau_etude = models.CharField(max_length=20, choices=NIVEAU_ETUDE_CHOICES)
    domaine_etude = models.CharField(max_length=20, choices=DOMAINE_ETUDE_CHOICES)
    competences = models.TextField(blank=True, null=True)
    adresse = models.TextField(blank=True, null=True)
    realisations = models.TextField(blank=True, null=True)
    cv = models.FileField(upload_to='cvs/', blank=True, null=True)
    est_valide = models.BooleanField(default=False)

    def __str__(self):
        return self.nom_complet


class OffreDeStage(models.Model):
    titre = models.CharField(max_length=100)
    description = models.TextField()
    domaine = models.CharField(max_length=100)
    competences_requises = models.TextField(blank=True)
    entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE)
    date_publication = models.DateTimeField(auto_now_add=True)
    duree = models.PositiveIntegerField(help_text="Durée en mois", null=True, blank=True)
    date_debut = models.DateField(help_text="Date prévue de début", null=True, blank=True)

    def __str__(self):
        return self.titre

class Candidature(models.Model):
    etudiant = models.ForeignKey('Etudiant', on_delete=models.CASCADE)
    offre = models.ForeignKey('OffreDeStage', on_delete=models.CASCADE)
    date_postulation = models.DateTimeField(auto_now_add=True)
    cv = models.FileField(upload_to='cvs/')
    statut = models.CharField(
        max_length=20,
        choices=(
            ('en_attente', 'En attente'),
            ('acceptee', 'Acceptée'),
            ('refusee', 'Refusée')
        ),
        default='en_attente'
    )
    message = models.TextField(blank=True, null=True)
    cv = models.FileField(upload_to='candidatures_cvs/', blank=True, null=True)

    class Meta:
        unique_together = ('etudiant', 'offre')

    def __str__(self):
        return f"{self.etudiant} → {self.offre} ({self.statut})"
