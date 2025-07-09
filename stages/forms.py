# stages/forms.py
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import os
from .models import (
    OffreDeStage, Etudiant, UserProfile, Entreprise, 
    Candidature, ConventionDeStage, SuiviStage, 
    Memoire, EvaluationStage, Enseignant, Annonce
)

class OffreDeStageForm(forms.ModelForm):
    class Meta:
        model = OffreDeStage
        fields = ['titre', 'description', 'domaine', 'competences_requises', 
                 'duree', 'date_debut', 'gratification', 'type_stage', 'nombre_places', 'date_limite']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
            'competences_requises': forms.Textarea(attrs={'rows': 3}),
            'date_debut': forms.DateInput(attrs={'type': 'date'}),
            'date_limite': forms.DateInput(attrs={'type': 'date'}),
        }

class BaseUserForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Adresse e-mail")
    username = forms.CharField(max_length=30, required=True, label="Nom d'utilisateur")
    nom_complet = forms.CharField(max_length=30, required=True, label="Nom complet")
    password1 = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput
    )
    password2 = forms.CharField(
        label="Confirmer le mot de passe",
        widget=forms.PasswordInput
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'nom_complet', 'password1', 'password2')

class EntrepriseSignupForm(BaseUserForm):
    nom_entreprise = forms.CharField(max_length=100, required=True)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_active = False
        if commit:
            user.save()
            Entreprise.objects.create(
                user=user,
                nom_entreprise=self.cleaned_data['nom_entreprise'],
                est_valide=False
            )
            UserProfile.objects.create(
                user=user,
                role='entreprise',
                is_validated=False
            )
        return user

class EtudiantSignupForm(BaseUserForm):
    universite = forms.CharField(max_length=100, required=True)
    niveau_etude = forms.ChoiceField(choices=Etudiant.NIVEAU_ETUDE_CHOICES)
    domaine_etude = forms.ChoiceField(choices=Etudiant.DOMAINE_ETUDE_CHOICES)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_active = True
        if commit:
            user.save()
            Etudiant.objects.create(
    user=user,
    email=user.email,  # ⚠️ Ajout crucial
    universite=self.cleaned_data['universite'],
    niveau_etude=self.cleaned_data['niveau_etude'],
    domaine_etude=self.cleaned_data['domaine_etude'],
    est_valide=True
)

            UserProfile.objects.create(
                user=user,
                role='etudiant',
                is_validated=True
            )
        return user

class EnseignantSignupForm(BaseUserForm):
    specialite = forms.CharField(max_length=100, required=True)
    departement = forms.CharField(max_length=100, required=True)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_active = False
        if commit:
            user.save()
            Enseignant.objects.create(
                user=user,
                specialite=self.cleaned_data['specialite'],
                departement=self.cleaned_data['departement'],
                est_valide=False
            )
            UserProfile.objects.create(
                user=user,
                role='enseignant',
                is_validated=False
            )
        return user

class EntrepriseForm(forms.ModelForm):
    class Meta:
        model = Entreprise
        exclude = ['user', 'est_valide']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
            'date_creation': forms.DateInput(attrs={'type': 'date'}),
        }

class EtudiantForm(forms.ModelForm):
    class Meta:
        model = Etudiant
        fields = ['universite', 'niveau_etude', 'domaine_etude', 'competences', 
                  'cv', 'linkedin', 'portfolio', 'enseignant_referent', 'departement', 'nom_complet', 'telephone', 'competences']
        widgets = {
            'competences': forms.Textarea(attrs={'rows': 3, 'placeholder': "Langages, outils, frameworks..."}),
        }

    def clean_cv(self):
        cv = self.cleaned_data.get('cv')
        if cv:
            if cv.size > 5*1024*1024:
                raise ValidationError("Le fichier est trop volumineux (max 5MB)")
            ext = os.path.splitext(cv.name)[1].lower()
            if ext not in ['.pdf', '.doc', '.docx']:
                raise ValidationError("Format non supporté (PDF, DOC, DOCX uniquement)")
        return cv

class CandidatureForm(forms.ModelForm):
    class Meta:
        model = Candidature
        fields = ['message', 'cv', 'lettre_motivation']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        cv = cleaned_data.get('cv')
        lettre = cleaned_data.get('lettre_motivation')
        
        if not cv and not lettre:
            raise ValidationError("Vous devez fournir au moins un CV ou une lettre de motivation.")
        
        return cleaned_data

class ConventionStageForm(forms.ModelForm):
    class Meta:
        model = ConventionDeStage
        exclude = ['statut', 'date_creation', 'date_validation']
        widgets = {
            'date_debut': forms.DateInput(attrs={'type': 'date'}),
            'date_fin': forms.DateInput(attrs={'type': 'date'}),
        }

class SuiviStageForm(forms.ModelForm):
    class Meta:
        model = SuiviStage
        fields = ['date_rapport', 'type_rapport', 'document', 'commentaires', 'note']
        widgets = {
            'date_rapport': forms.DateInput(attrs={'type': 'date'}),
        }

class MemoireForm(forms.ModelForm):
    class Meta:
        model = Memoire
        fields = ['titre', 'resume', 'document', 'date_soutenance', 'jury', 'est_public']
        widgets = {
            'date_soutenance': forms.DateInput(attrs={'type': 'date'}),
        }

class EvaluationStageForm(forms.ModelForm):
    class Meta:
        model = EvaluationStage
        fields = ['satisfaction_globale', 'acquis_professionnels', 
                 'points_positifs', 'points_amelioration', 'recommandation_entreprise', 'commentaires']

class AnnonceForm(forms.ModelForm):
    class Meta:
        model = Annonce
        fields = ['titre', 'contenu', 'departement', 'fichier']