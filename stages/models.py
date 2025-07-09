from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
import os
from datetime import date
from django.utils import timezone


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
    departement = models.ForeignKey('Departement', on_delete=models.SET_NULL, null=True, blank=True)


    def __str__(self):
        return f"{self.user.username} ({self.role})"

class Departement(models.Model):
    nom = models.CharField(max_length=100)

    def __str__(self):
        return self.nom    

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

    def is_active(self):
        return self.est_valide    

class Etudiant(models.Model):
    SEXE_CHOICES = [
        ('M', 'Masculin'),
        ('F', 'Féminin'),
    ]
    NIVEAU_ETUDE_CHOICES = [
        ('licence1', 'Licence 1'),
        ('licence2', 'Licence 2'),
        ('licence3', 'Licence 3'),
        ('master1', 'Master 1'),
        ('master2', 'Master 2'),
        ('ingenieur1', 'Cycle Ingénieur 1'),
        ('ingenieur2', 'Cycle Ingénieur 2'),
        ('ingenieur3', 'Cycle Ingénieur 3'),
    ]

    DOMAINE_ETUDE_CHOICES = [
        ('gc', 'Génie Civil'),
        ('geii', 'Génie Électrique et Informatique Industrielle'),
        ('gtr', 'Génie Télécom et Réseaux'),
        ('ginfo', 'Génie Informatique'),
        ('gindus', 'Génie Industriel'),
        ('chimie', 'Génie Chimique et Biologique'),
        ('gme', 'Génie Mécanique et Énergétique'),
        ('ges', 'Gestion'),
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
    departement = models.ForeignKey(Departement, on_delete=models.SET_NULL, null=True)
    last_annonce_vue = models.DateTimeField(default=timezone.now)
    annonces_masquees = models.ManyToManyField('Annonce', blank=True)
    linkedin = models.URLField(max_length=200, blank=True, null=True, verbose_name="Profil LinkedIn")
    portfolio = models.URLField(max_length=200, blank=True, null=True, verbose_name="Portfolio en ligne")
    sexe = models.CharField(max_length=1, choices=SEXE_CHOICES)
    date_naissance = models.DateField()
    lieu_naissance = models.CharField(max_length=100)
    nationalite = models.CharField(max_length=50, default='Sénégalaise')
    ville = models.CharField(max_length=50, default='Dakar')
    pays = models.CharField(max_length=50, default='Sénégal')
    code_postal = models.CharField(max_length=10, blank=True, null=True)

    def __str__(self):
        return self.nom_complet
    def is_active(self):
        return self.est_valide

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
    date_limite = models.DateField("Date limite de candidature", null=True, blank=True)

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
    lettre_motivation = models.FileField(upload_to='candidatures_lettres/', blank=True, null=True)

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
    
    # Informations de base
    etudiant = models.ForeignKey(Etudiant, on_delete=models.CASCADE)
    offre = models.ForeignKey(OffreDeStage, on_delete=models.CASCADE)
    entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE)
    
    # Dates et durée
    date_debut = models.DateField()
    date_fin = models.DateField()
    heures_semaine = models.PositiveIntegerField()
    annee_universitaire = models.CharField(max_length=20, default="2024-2025")
    
    # Rémunération
    gratification = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    frais_remboursement = models.TextField(blank=True, null=True)
    
    # Encadrement
    tuteur_entreprise = models.CharField(max_length=100)
    fonction_tuteur = models.CharField(max_length=100, blank=True, null=True)
    email_tuteur = models.EmailField()
    telephone_tuteur = models.CharField(max_length=20)
    enseignant_referent = models.ForeignKey(Enseignant, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Statut et validation
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='brouillon')
    date_creation = models.DateTimeField(auto_now_add=True)
    date_validation = models.DateTimeField(null=True, blank=True)
    
    # Documents
    document = models.FileField(upload_to='conventions/', null=True, blank=True)
    rapport_stage = models.FileField(upload_to='rapports/', null=True, blank=True)
    commentaires = models.TextField(blank=True, null=True)
    
    # Signatures
    signature_etudiant = models.ImageField(upload_to='signatures/', null=True, blank=True)
    signature_entreprise = models.ImageField(upload_to='signatures/', null=True, blank=True)
    signature_enseignant = models.ImageField(upload_to='signatures/', null=True, blank=True)
    
    # Informations complémentaires du modèle fourni
    confidentialite_rapport = models.BooleanField(default=False)
    avenant = models.FileField(upload_to='avenants/', null=True, blank=True)
    materiel_fourni = models.TextField(blank=True, null=True)
    assurance = models.TextField(blank=True, null=True, default="Couverture par l'assurance de l'établissement")
    
    def __str__(self):
        return f"Convention {self.etudiant} - {self.entreprise}"

    def est_valide(self):
        return self.statut == 'validee'
    
    def duree_stage_jours(self):
        return (self.date_fin - self.date_debut).days
    
    def save(self, *args, **kwargs):
        # Génération automatique de l'année universitaire si vide
        if not self.annee_universitaire:
            debut_year = self.date_debut.year
            fin_year = self.date_fin.year
            if self.date_debut.month >= 9:  # Si le stage commence après septembre
                self.annee_universitaire = f"{debut_year}-{debut_year+1}"
            else:
                self.annee_universitaire = f"{debut_year-1}-{debut_year}"
        super().save(*args, **kwargs)

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

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
import PyPDF2
import docx
from io import BytesIO

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
    contenu_textuel = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        # Extraction du contenu textuel
        if self.document:
            try:
                if self.document.name.lower().endswith('.pdf'):
                    pdf = PyPDF2.PdfReader(self.document)
                    self.contenu_textuel = "\n".join([page.extract_text() for page in pdf.pages])
                elif self.document.name.lower().endswith(('.docx', '.doc')):
                    doc = docx.Document(BytesIO(self.document.read()))
                    self.contenu_textuel = "\n".join([para.text for para in doc.paragraphs])
                elif self.document.name.lower().endswith(('.txt', '.md')):
                    self.contenu_textuel = self.document.read().decode('utf-8')
            except Exception as e:
                print(f"Erreur lors de l'extraction du texte: {e}")
                self.contenu_textuel = None
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.titre} - {self.etudiant}"

    class Meta:
        verbose_name = "Mémoire"
        verbose_name_plural = "Mémoires"

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
    
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.core.cache import cache

@receiver(post_delete, sender=OffreDeStage)
def supprimer_cache_offre(sender, instance, **kwargs):
    cache.delete(f"reco_candidats_{instance.id}")
    cache.delete(f"eval_candidatures_{instance.id}_v2")

@receiver(post_delete, sender=Etudiant)
def supprimer_cache_etudiant(sender, instance, **kwargs):
    cache.delete(f"reco_offres_{instance.id}_v2")

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

from django.db import models
from django.conf import settings
from django.utils import timezone

class Conversation(models.Model):
    participant1 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='conversations_initiated',
        on_delete=models.CASCADE,
        verbose_name="Premier participant"
    )
    participant2 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='conversations_received',
        on_delete=models.CASCADE,
        verbose_name="Second participant"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Dernière mise à jour"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['participant1', 'participant2'],
                name='unique_conversation_participants'
            )
        ]
        ordering = ['-updated_at']
        verbose_name = "Conversation"
        verbose_name_plural = "Conversations"

    def __str__(self):
        return f"Conversation #{self.id} entre {self.participant1} et {self.participant2}"

    def save(self, *args, **kwargs):
        # Force l'ordre des participants pour éviter les doublons
        if self.participant1_id > self.participant2_id:
            self.participant1, self.participant2 = self.participant2, self.participant1
        
        # Mise à jour automatique de updated_at si nécessaire
        if not self.pk:  # Si c'est une nouvelle conversation
            self.created_at = timezone.now()
        self.updated_at = timezone.now()
        
        super().save(*args, **kwargs)

    def get_other_participant(self, user):
        """Retourne l'autre participant de la conversation"""
        if user not in (self.participant1, self.participant2):
            raise ValueError("L'utilisateur n'est pas participant à cette conversation")
        return self.participant2 if user == self.participant1 else self.participant1

    @property
    def participants(self):
        """Retourne les deux participants sous forme de tuple"""
        return (self.participant1, self.participant2)

    @classmethod
    def get_conversation(cls, user1, user2):
        """Récupère ou crée une conversation entre deux utilisateurs"""
        participant1, participant2 = sorted([user1, user2], key=lambda u: u.id)
        conversation, created = cls.objects.get_or_create(
            participant1=participant1,
            participant2=participant2
        )
        return conversation
    


    class Meta:
        unique_together = ('participant1', 'participant2')

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, related_name='messages', on_delete=models.CASCADE)
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False) 


class Annonce(models.Model):
    titre = models.CharField(max_length=255)
    contenu = models.TextField()
    date_publication = models.DateTimeField(auto_now_add=True)
    modifie_le = models.DateTimeField(auto_now=True)  # ✅ Ajout ici
    departement = models.ForeignKey(Departement, on_delete=models.CASCADE, related_name='annonces')
    auteur = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    fichier = models.FileField(upload_to='annonces_fichiers/', blank=True, null=True)
    est_visible = models.BooleanField(default=True, help_text="Indique si l'annonce est visible par les étudiants")

    def __str__(self):
        return f"{self.titre} ({self.departement.nom})"



class ChefDepartement(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    departement = models.OneToOneField(Departement, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user.username} - {self.departement.nom}"

class Stage(models.Model):
    STATUT_STAGE_CHOICES = [
        ('entretien_passe', 'Entretien passé'),
        ('en_attente', 'En attente de démarrage'),
        ('en_cours', 'En cours'),
        ('termine', 'Terminé'),
        ('annule', 'Annulé'),
    ]
    
    etudiant = models.OneToOneField(Etudiant, on_delete=models.CASCADE)
    offre = models.ForeignKey(OffreDeStage, on_delete=models.CASCADE)
    entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE)
    convention = models.OneToOneField(ConventionDeStage, on_delete=models.SET_NULL, null=True, blank=True)
    statut = models.CharField(max_length=20, choices=STATUT_STAGE_CHOICES, default='en_attente')
    
    date_debut_reelle = models.DateField(null=True, blank=True)
    date_fin_reelle = models.DateField(null=True, blank=True)
    commentaire_entreprise = models.TextField(blank=True, null=True)
    commentaire_etudiant = models.TextField(blank=True, null=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.etudiant.nom_complet} - {self.statut}"



