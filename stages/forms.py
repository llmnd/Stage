# stages/forms.py
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import OffreDeStage, Etudiant, UserProfile, Entreprise
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import (Entreprise, Etudiant, OffreDeStage, Candidature, 
                    ConventionDeStage, SuiviStage, Memoire, EvaluationStage)


class OffreDeStageForm(forms.ModelForm):
    class Meta:
        model = OffreDeStage
        fields = ['titre', 'description', 'domaine', 'competences_requises', 'duree', 'date_debut']
        widgets = {
            'description': forms.Textarea(attrs={
                'rows': 5,
                'class': 'form-control',
                'placeholder': _('Décrivez les missions du stage')
            }),
            'competences_requises': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': _('Listez les compétences requises, séparées par des virgules')
            }),
            'date_debut': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
        }
        labels = {
            'competences_requises': _('Compétences requises'),
            'domaine': _('Domaine principal'),
            'duree': _('Durée (mois)'),
            'date_debut': _('Date de début')
        }

    def clean_titre(self):
        titre = self.cleaned_data['titre']
        if len(titre) < 10:
            raise ValidationError(_("Le titre doit contenir au moins 10 caractères."))
        return titre


class EntrepriseSignupForm(UserCreationForm):
    email = forms.EmailField(
        max_length=254,
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': _('email@exemple.com')
        }),
        help_text=_('Une adresse email valide est requise.')
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _("Nom d'utilisateur")
            }),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            UserProfile.objects.create(
                user=user,
                role='entreprise',
                is_validated=False  # Correspond à la validation par admin, à confirmer selon ton modèle
            )
        return user

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(email=email).exists():
            raise ValidationError(_("Un compte existe déjà avec cette adresse email."))
        return email


class EntrepriseForm(forms.ModelForm):
    class Meta:
        model = Entreprise
        fields = [
            'nom_entreprise',
            'description',
            'secteur',
            'adresse',
            'logo_url',
            'site_web',
            'realisations',
            'telephone',
            'email_contact',
            'reseaux_sociaux',
            'taille',
            'nombre_employes',
            'ville',
            'pays',
            'date_creation',
            'statut_juridique',
        ]
        widgets = {
            'nom_entreprise': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={
                'rows': 5,
                'class': 'form-control',
                'placeholder': _('Présentez votre entreprise')
            }),
            'secteur': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _("Secteur d'activité")
            }),
            'adresse': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Adresse complète')
            }),
            'logo_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': _('URL du logo')
            }),
            'site_web': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://www.exemple.com'
            }),
            'realisations': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': _('Décrivez vos réalisations marquantes')
            }),
            'telephone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Numéro de téléphone')
            }),
            'email_contact': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': _('Email de contact')
            }),
            'reseaux_sociaux': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Lien(s) vers vos réseaux sociaux')
            }),
            'taille': forms.Select(attrs={'class': 'form-control'}),  # si taille est un choix (ex : Petite, Moyenne, Grande)
            'nombre_employes': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0
            }),
            'ville': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Ville')
            }),
            'pays': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Pays')
            }),
            'date_creation': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'statut_juridique': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Statut juridique')
            }),
        }
        help_texts = {
            'logo_url': _('URL du logo de votre entreprise (format carré recommandé)'),
            'email_contact': _('Adresse email de contact principale'),
            'telephone': _('Numéro de téléphone principal'),
            'reseaux_sociaux': _('Exemple : liens Facebook, LinkedIn, Twitter'),
            'taille': _('Taille de l\'entreprise (ex : Petite, Moyenne, Grande)'),
            'nombre_employes': _('Nombre total d\'employés'),
            'date_creation': _('Date de création de l\'entreprise'),
            'statut_juridique': _('Forme juridique de l\'entreprise'),
        }


class EtudiantForm(forms.ModelForm):
    class Meta:
        model = Etudiant
        fields = ['nom_complet', 'email', 'telephone', 'universite', 
                 'niveau_etude', 'domaine_etude', 'competences', 
                 'adresse', 'realisations', 'cv']
        
        widgets = {
            'nom_complet': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'universite': forms.TextInput(attrs={'class': 'form-control'}),
            'domaine_etude': forms.Select(attrs={'class': 'form-control'}),
            'niveau_etude': forms.Select(attrs={'class': 'form-control'}),
            'competences': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': _('Listez vos compétences, séparées par des virgules')
            }),
            'realisations': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': _('Décrivez vos réalisations académiques/professionnelles')
            }),
            'cv': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx'
            }),
            'adresse': forms.Textarea(attrs={
                'rows': 2,
                'class': 'form-control',
                'placeholder': _('Adresse complète')
            }),
        }
        
        help_texts = {
            'cv': _('Formats acceptés: PDF, DOC, DOCX (max. 5MB)'),
            'email': _('Votre email académique de préférence'),
        }

    def clean_cv(self):
        cv = self.cleaned_data.get('cv')
        if cv:
            if cv.size > 5*1024*1024:  # 5MB
                raise ValidationError(_("La taille du fichier ne doit pas dépasser 5MB."))
            ext = cv.name.split('.')[-1].lower()
            if ext not in ['pdf', 'doc', 'docx']:
                raise ValidationError(_("Format de fichier non supporté. Utilisez PDF, DOC ou DOCX."))
        return cv
class EtudiantSignupForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': _('email@exemple.com')
        })
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _("Nom d'utilisateur")
            }),
        }
        help_texts = {
            'username': _('150 caractères maximum. Lettres, chiffres et @/./+/-/_ seulement.'),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            UserProfile.objects.create(
                user=user,
                role='etudiant',
                is_validated=True  # Supposé validé dès la création
            )
        return user
from django import forms
from .models import Candidature

class CandidatureForm(forms.ModelForm):
    class Meta:
        model = Candidature
        fields = ['message', 'cv']
        widgets = {
            'message': forms.Textarea(attrs={
                'rows': 5,
                'class': 'form-control',
                'placeholder': "Rédigez un message pour accompagner votre candidature"
            }),
            'cv': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx'
            }),
        }
        labels = {
            'message': 'Message',
            'cv': 'Votre CV (optionnel)',
        }
        help_texts = {
            'cv': 'Formats acceptés: PDF, DOC, DOCX (max. 5MB)',
        }

    def clean_cv(self):
        cv = self.cleaned_data.get('cv', False)
        if cv:
            if cv.size > 5*1024*1024:
                raise forms.ValidationError("La taille du fichier ne doit pas dépasser 5MB.")
            ext = cv.name.split('.')[-1].lower()
            if ext not in ['pdf', 'doc', 'docx']:
                raise forms.ValidationError("Format de fichier non supporté.")
        return cv

class ConventionStageForm(forms.ModelForm):
    class Meta:
        model = ConventionDeStage
        fields = [
            'date_debut', 'date_fin', 'heures_semaine', 'gratification',
            'tuteur_entreprise', 'email_tuteur', 'telephone_tuteur',
            'enseignant_referent', 'document', 'commentaires'
        ]
        widgets = {
            'date_debut': forms.DateInput(attrs={'type': 'date'}),
            'date_fin': forms.DateInput(attrs={'type': 'date'}),
            'commentaires': forms.Textarea(attrs={'rows': 3}),
        }
        signature_etudiant = forms.ImageField(required=False)
        signature_entreprise = forms.ImageField(required=False)


class SuiviStageForm(forms.ModelForm):
    class Meta:
        model = SuiviStage
        fields = ['date_rapport', 'type_rapport', 'document', 'commentaires', 'note']
        widgets = {
            'date_rapport': forms.DateInput(attrs={'type': 'date'}),
            'commentaires': forms.Textarea(attrs={'rows': 4}),
        }

class MemoireForm(forms.ModelForm):
    class Meta:
        model = Memoire
        fields = ['titre', 'resume', 'mots_cles', 'document', 'date_soutenance', 'jury', 'est_public']
        widgets = {
            'resume': forms.Textarea(attrs={'rows': 5}),
            'date_soutenance': forms.DateInput(attrs={'type': 'date'}),
            'jury': forms.CheckboxSelectMultiple(),
        }

class EvaluationStageForm(forms.ModelForm):
    class Meta:
        model = EvaluationStage
        fields = ['satisfaction_globale', 'acquis_professionnels', 
                 'points_positifs', 'points_amelioration', 
                 'recommandation_entreprise', 'commentaires']
        widgets = {
            'acquis_professionnels': forms.Textarea(attrs={'rows': 3}),
            'points_positifs': forms.Textarea(attrs={'rows': 3}),
            'points_amelioration': forms.Textarea(attrs={'rows': 3}),
            'commentaires': forms.Textarea(attrs={'rows': 3}),
        }

class EnseignantSignupForm(UserCreationForm):
    nom_complet = forms.CharField(max_length=100)
    email = forms.EmailField()
    telephone = forms.CharField(max_length=20, required=False)
    specialite = forms.CharField(max_length=100)
    departement = forms.CharField(max_length=100)

    class Meta:
        model = User
        fields = ('username', 'nom_complet', 'email', 'telephone', 
                 'specialite', 'departement', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            enseignant = Enseignant.objects.create(
                user=user,
                nom_complet=self.cleaned_data['nom_complet'],
                email=self.cleaned_data['email'],
                telephone=self.cleaned_data['telephone'],
                specialite=self.cleaned_data['specialite'],
                departement=self.cleaned_data['departement']
            )
            # Créer le profil utilisateur
            UserProfile.objects.create(
                user=user,
                role='enseignant',
                is_validated=False
            )
        return user