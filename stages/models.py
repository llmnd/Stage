from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
import os
from datetime import date

# Rôles possibles
ROLES = (
    ('admin', 'Admin'),
    ('entreprise', 'Entreprise'),
    ('etudiant', 'Étudiant'),
    ('enseignant', 'Enseignant'),
)

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLES)
    is_validated = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} ({self.role})"

class Enseignant(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nom_complet = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    telephone = models.CharField(max_length=20, blank=True, null=True)
    specialite = models.CharField(max_length=100)
    departement = models.CharField(max_length=100)
    est_valide = models.BooleanField(default=False)

    def __str__(self):
        return self.nom_complet

class Entreprise(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nom_entreprise = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    secteur = models.CharField(max_length=255, blank=True)
    adresse = models.CharField(max_length=255, blank=True)
    logo_url = models.URLField(blank=True)
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
    enseignant_referent = models.ForeignKey(Enseignant, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.nom_complet

class OffreDeStage(models.Model):
    TYPE_STAGE_CHOICES = [
        ('obligatoire', 'Stage obligatoire'),
        ('facultatif', 'Stage facultatif'),
        ('alternance', 'Contrat d\'alternance'),
    ]
    
    titre = models.CharField(max_length=100)
    description = models.TextField()
    domaine = models.CharField(max_length=100)
    competences_requises = models.TextField(blank=True)
    entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE)
    date_publication = models.DateTimeField(auto_now_add=True)
    duree = models.PositiveIntegerField(help_text="Durée en mois", null=True, blank=True)
    date_debut = models.DateField(help_text="Date prévue de début", null=True, blank=True)
    type_stage = models.CharField(max_length=20, choices=TYPE_STAGE_CHOICES, default='obligatoire')
    gratification = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    nombre_places = models.PositiveIntegerField(default=1)
    est_valide = models.BooleanField(default=False)

    def __str__(self):
        return self.titre

class Candidature(models.Model):
    etudiant = models.ForeignKey('Etudiant', on_delete=models.CASCADE)
    offre = models.ForeignKey('OffreDeStage', on_delete=models.CASCADE)
    date_postulation = models.DateTimeField(auto_now_add=True)
    statut = models.CharField(
        max_length=20,
        choices=(
            ('en_attente', 'En attente'),
            ('acceptee', 'Acceptée'),
            ('refusee', 'Refusée'),
            ('en_entretien', 'En entretien')
        ),
        default='en_attente'
    )
    message = models.TextField(blank=True, null=True)
    cv = models.FileField(upload_to='candidatures_cvs/', blank=True, null=True)
    score_ia = models.FloatField(null=True, blank=True, help_text="Score de correspondance calculé par l'IA")
    feedback_ia = models.TextField(blank=True, null=True, help_text="Feedback généré par l'IA")

    class Meta:
        unique_together = ('etudiant', 'offre')
        ordering = ['-score_ia', '-date_postulation']

    def __str__(self):
        return f"{self.etudiant} → {self.offre} ({self.statut})"

class ConventionDeStage(models.Model):
    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('en_attente', 'En attente de validation'),
        ('validee', 'Validée'),
        ('refusee', 'Refusée'),
    ]
    
    etudiant = models.ForeignKey(Etudiant, on_delete=models.CASCADE)
    offre = models.ForeignKey(OffreDeStage, on_delete=models.CASCADE)
    entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE)
    date_debut = models.DateField()
    date_fin = models.DateField()
    heures_semaine = models.PositiveIntegerField()
    gratification = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    tuteur_entreprise = models.CharField(max_length=100)
    email_tuteur = models.EmailField()
    telephone_tuteur = models.CharField(max_length=20)
    enseignant_referent = models.ForeignKey(Enseignant, on_delete=models.SET_NULL, null=True, blank=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='brouillon')
    date_creation = models.DateTimeField(auto_now_add=True)
    date_validation = models.DateTimeField(null=True, blank=True)
    document = models.FileField(upload_to='conventions/', null=True, blank=True)
    commentaires = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Convention {self.etudiant} - {self.entreprise}"

    def est_valide(self):
        return self.statut == 'validee'

class SuiviStage(models.Model):
    convention = models.ForeignKey(ConventionDeStage, on_delete=models.CASCADE)
    date_rapport = models.DateField()
    type_rapport = models.CharField(max_length=50, choices=[
        ('intermediaire', 'Rapport intermédiaire'),
        ('final', 'Rapport final'),
        ('visite', 'Compte-rendu de visite'),
    ])
    document = models.FileField(upload_to='suivis_stage/')
    commentaires = models.TextField()
    note = models.PositiveIntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(20)]
    )
    auteur = models.ForeignKey(User, on_delete=models.CASCADE)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_rapport']

    def __str__(self):
        return f"Suivi {self.type_rapport} - {self.convention.etudiant}"

class Memoire(models.Model):
    etudiant = models.ForeignKey(Etudiant, on_delete=models.CASCADE)
    titre = models.CharField(max_length=200)
    resume = models.TextField()
    mots_cles = models.CharField(max_length=200)
    document = models.FileField(upload_to='memoires/')
    date_depot = models.DateTimeField(auto_now_add=True)
    date_soutenance = models.DateField(null=True, blank=True)
    note = models.PositiveIntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(20)]
    )
    jury = models.ManyToManyField(Enseignant, blank=True)
    est_public = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.titre} - {self.etudiant}"

    def extension(self):
        name, extension = os.path.splitext(self.document.name)
        return extension

class EvaluationStage(models.Model):
    convention = models.OneToOneField(ConventionDeStage, on_delete=models.CASCADE)
    date_evaluation = models.DateField(auto_now_add=True)
    satisfaction_globale = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="1 = Très insatisfait, 5 = Très satisfait"
    )
    acquis_professionnels = models.TextField()
    points_positifs = models.TextField()
    points_amelioration = models.TextField()
    recommandation_entreprise = models.BooleanField(default=True)
    commentaires = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Evaluation de {self.convention.etudiant}"