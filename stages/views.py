from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views import View
from django.views.generic import TemplateView
from .forms import EtudiantSignupForm, EntrepriseSignupForm, EntrepriseForm, OffreDeStageForm
from .models import OffreDeStage, Entreprise, Candidature, Etudiant
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from django.http import Http404, FileResponse
from .models import ConventionDeStage, SuiviStage, Memoire, EvaluationStage
from django.contrib import messages
from django.core.cache import cache
from django.db.models import Q
from .models import Conversation, Message
from django.contrib import messages as django_messages
from django.db import models
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .models import Conversation, Message  # adapte selon tes modèles
from .models import Annonce


from .forms import (ConventionStageForm, SuiviStageForm, MemoireForm, 
                   EvaluationStageForm, EnseignantSignupForm)
from .ia.recommendation import RecommandationIA
from django.conf import settings
import os
from django.http import JsonResponse




# --- Authentification et inscriptions ---

from django.shortcuts import render, redirect
from django.contrib.auth import login   
from django.contrib import messages    

from django.views import View
from .forms import EtudiantSignupForm, EntrepriseSignupForm

# ✅ Vue de type classe (au cas où tu l'utilises ailleurs)
class RegisterView(View):
    def get(self, request):
        form = EtudiantSignupForm()
        return render(request, 'registration/register.html', {'form': form})

    def post(self, request):
        form = EtudiantSignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
        return render(request, 'registration/register.html', {'form': form})
   

# ✅ Nouvelles vues fonctionnelles pour les rôles
def register_choice(request):
    return render(request, 'registration/register_choice.html')

def register_etudiant(request):
    if request.method == 'POST':
        form = EtudiantSignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, "Votre compte a été créé avec succès. Il doit être validé par un administrateur.")
            return redirect('login')
    else:
        form = EtudiantSignupForm()
    return render(request, 'registration/register_etudiant.html', {'form': form})

def register_entreprise(request):
    if request.method == 'POST':
        form = EntrepriseSignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, "Votre compte a été créé avec succès. Il doit être validé par un administrateur.")
            return redirect('login')
    else:
        form = EntrepriseSignupForm()
    return render(request, 'registration/register_entreprise.html', {'form': form})

@login_required
def dashboard(request):
    return render(request, 'dashboard.html')

# --- Offres de stage ---

from django.core.paginator import Paginator  # Assure-toi d'importer ça aussi si pas déjà fait

def liste_offres(request):
    # Filtrer les offres qui ont une entreprise associée
    offres_qs = OffreDeStage.objects.filter(entreprise__isnull=False).order_by('-date_publication')

    # Recherche et filtre domaine (exemple)
    recherche = request.GET.get('recherche', '')
    domaine = request.GET.get('domaine', '')
    if recherche:
        offres_qs = offres_qs.filter(titre__icontains=recherche)
    if domaine:
        offres_qs = offres_qs.filter(domaine=domaine)

    # Pagination
    paginator = Paginator(offres_qs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Extraire domaines distincts pour filtre
    domaines = OffreDeStage.objects.values_list('domaine', flat=True).distinct()

    context = {
        'offres': page_obj,
        'page_obj': page_obj,
        'domaines': domaines,
        'request': request,
    }
    return render(request, 'stages/liste.html', context)


@login_required
def ajouter_offre(request):
    if not hasattr(request.user, 'entreprise'):
        return redirect('login')

    if request.method == 'POST':
        form = OffreDeStageForm(request.POST)
        if form.is_valid():
            offre = form.save(commit=False)
            offre.entreprise = request.user.entreprise
            offre.save()
            return redirect('liste_offres')
    else:
        form = OffreDeStageForm()
    return render(request, 'stages/ajouter.html', {'form': form})

@login_required
def modifier_offre(request, offre_id):
    offre = get_object_or_404(OffreDeStage, id=offre_id)

    if not hasattr(request.user, 'entreprise') or offre.entreprise != request.user.entreprise:
        return redirect('profil_entreprise', id=request.user.entreprise.id)

    if request.method == 'POST':
        form = OffreDeStageForm(request.POST, instance=offre)
        if form.is_valid():
            form.save()
            return redirect('profil_entreprise', id=request.user.entreprise.id)
    else:
        form = OffreDeStageForm(instance=offre)

    return render(request, 'stages/modifier_offre.html', {
        'form': form,
        'offre': offre,
    })

@login_required
def supprimer_offre(request, offre_id):
    offre = get_object_or_404(OffreDeStage, id=offre_id)

    if not hasattr(request.user, 'entreprise') or offre.entreprise != request.user.entreprise:
        return redirect('profil_entreprise', id=request.user.entreprise.id)

    if request.method == "POST":
        offre.delete()
        return redirect('profil_entreprise', id=request.user.entreprise.id)

    return render(request, 'stages/supprimer_offre.html', {'offre': offre})

from django.shortcuts import render, get_object_or_404
from .models import OffreDeStage

@login_required
def detail_offre(request, offre_id):
    offre = get_object_or_404(OffreDeStage, id=offre_id)
    etudiant = getattr(request.user, 'etudiant', None)

    candidature_existante = None
    if etudiant:
        candidature_existante = Candidature.objects.filter(offre=offre, etudiant=etudiant).first()

    if request.method == 'POST' and etudiant and not candidature_existante:
        form = CandidatureForm(request.POST, request.FILES)
        if form.is_valid():
            candidature = form.save(commit=False)
            candidature.offre = offre
            candidature.etudiant = etudiant
            candidature.statut = 'en_attente'  # ou autre statut par défaut
            candidature.save()
            return redirect('offre_detail', pk=offre_id)
    else:
        form = CandidatureForm()

    return render(request, 'stages/detail_offre.html', {
        'offre': offre,
        'etudiant': etudiant,
        'candidature_existante': candidature_existante,
        'form': form,
    })


@login_required
def postuler_offre(request, offre_id):
    offre = get_object_or_404(OffreDeStage, id=offre_id)
    try:
        etudiant = request.user.etudiant
    except Etudiant.DoesNotExist:
        return redirect('dashboard')

    candidature, created = Candidature.objects.get_or_create(etudiant=etudiant, offre=offre)
    return redirect('liste_offres')

# --- Entreprises ---

def signup_entreprise(request):
    if request.method == 'POST':
        form = EntrepriseSignupForm(request.POST)
        if form.is_valid():
            entreprise = form.save()
            return redirect('login')
    else:
        form = EntrepriseSignupForm()
    return render(request, 'registration/signup_entreprise.html', {'form': form})

@user_passes_test(lambda u: u.is_superuser)
def valider_entreprises(request):
    entreprises = Entreprise.objects.filter(est_valide=False)
    if request.method == 'POST':
        for entreprise in entreprises:
            if str(entreprise.id) in request.POST:
                entreprise.est_valide = True
                entreprise.save()
        return redirect('valider_entreprises')
    return render(request, 'admin/valider_entreprises.html', {'entreprises': entreprises})

@login_required
def mon_profil_entreprise(request):
    entreprise = getattr(request.user, 'entreprise', None)
    return render(request, 'stages/mon_profil.html', {'entreprise': entreprise})


def voir_profil_entreprise(request, id):
    entreprise = get_object_or_404(Entreprise, id=id)
    offres = OffreDeStage.objects.filter(entreprise=entreprise)

    # Convertir reseaux_sociaux string en liste
    if entreprise.reseaux_sociaux:
        reseaux = [lien.strip() for lien in entreprise.reseaux_sociaux.split(',')]
    else:
        reseaux = []

    context = {
        'entreprise': entreprise,
        'offres': offres,
        'reseaux_sociaux': reseaux,
    }
    return render(request, 'stages/voir_profil_entreprise.html', context)

@login_required
def profil_entreprise(request, id):
    entreprise = get_object_or_404(Entreprise, id=id)
    
    if not hasattr(request.user, 'entreprise') or request.user.entreprise.id != entreprise.id:
        return redirect('voir_profil_entreprise', id=entreprise.id)

    offres = OffreDeStage.objects.filter(entreprise=entreprise)
    candidatures = Candidature.objects.filter(offre__entreprise=entreprise)
    
    # Récupérer les offres actives
    offres_actives = OffreDeStage.objects.filter(
        entreprise=entreprise,
        date_debut__gte=timezone.now()
    )
    
    # Regrouper les candidatures par offre
    candidatures_grouped = {}
    for offre in offres:
        candidatures_grouped[offre] = list(candidatures.filter(offre=offre))

    # Récupérer les conventions de stage de l'entreprise
    conventions = ConventionDeStage.objects.filter(entreprise=entreprise).order_by('-date_creation')

    # Obtenir les meilleures recommandations
    top_recommandations = []
    ia = RecommandationIA()
    
    for offre in offres_actives:
        recommandations = ia.recommander_candidats(offre.id)
        if recommandations:
            top_recommandations.extend(recommandations[:2])  # Prendre les 2 meilleurs par offre
    
    # Trier toutes les recommandations par score
    top_recommandations.sort(key=lambda x: x['score'], reverse=True)
    top_recommandations = top_recommandations[:5]  # Limiter à 5 meilleures au total

    context = {
        'entreprise': entreprise,
        'offres': offres,
        'candidatures': candidatures,
        'offres_actives': offres_actives,
        'top_recommandations': top_recommandations,
        'candidatures_grouped': candidatures_grouped,
        'conventions': conventions,  # <-- Ajouté ici
    }
    
    return render(request, 'stages/profil_entreprise.html', context)

# --- Étudiants ---

@login_required
@login_required
def etudiant_dashboard(request):
    try:
        etudiant = request.user.etudiant
    except Etudiant.DoesNotExist:
        return redirect('dashboard')

    # Récupérer les candidatures récentes
    candidatures_recentes = Candidature.objects.filter(etudiant=etudiant).order_by('-date_postulation')[:3]
    conventions = ConventionDeStage.objects.filter(etudiant=etudiant).order_by('-date_creation')
    memoires = Memoire.objects.filter(etudiant=etudiant).order_by('-date_depot')  # Ajouté

    # Obtenir les recommandations IA
    ia = RecommandationIA()
    offres_recommandees = ia.recommander_offres(etudiant.id)

    context = {
        'etudiant': etudiant,
        'candidatures_recentes': candidatures_recentes,
        'offres_recommandees': offres_recommandees,
        'conventions': conventions,
        'memoires': memoires,  # Ajouté
    }

    return render(request, 'etudiant/dashboard.html', context)
def page_etudiant(request):
    return render(request, 'registration/login_etudiant.html')

# --- Candidatures ---

@login_required
@login_required
def detail_candidature(request, candidature_id):
    candidature = get_object_or_404(Candidature, id=candidature_id)
    user = request.user
    
    # Vérification des permissions
    if hasattr(user, 'etudiant'):
        if candidature.etudiant != user.etudiant:
            raise PermissionDenied("Vous n'avez pas accès à cette candidature.")
    elif hasattr(user, 'entreprise'):
        if candidature.offre.entreprise != user.entreprise:
            raise PermissionDenied("Cette candidature ne concerne pas votre entreprise.")
    else:
        return redirect('dashboard')

    # Récupération des informations de l'étudiant
    etudiant = candidature.etudiant
    context = {
        'candidature': candidature,
        'etudiant': {
            'nom_complet': etudiant.nom_complet,
            'email': etudiant.email,
            'telephone': etudiant.telephone,
            'universite': etudiant.universite,
            'niveau_etude': etudiant.get_niveau_etude_display(),
            'domaine_etude': etudiant.get_domaine_etude_display(),
            'competences': etudiant.competences,
            'adresse': etudiant.adresse,
            'realisations': etudiant.realisations,
        },
        'offre': {
            'titre': candidature.offre.titre,
            'domaine': candidature.offre.domaine,
            'duree': candidature.offre.duree,
            'entreprise': candidature.offre.entreprise.nom_entreprise,
        },
        'documents': [
            {
                'type': 'CV',
                'url': candidature.cv.url,
                'nom_fichier': candidature.cv.name.split('/')[-1],
                'taille': candidature.cv.size,
            } if candidature.cv else None,
        ],
        'is_entreprise': hasattr(user, 'entreprise'),
    }
    
    # Nettoyage des documents None
    context['documents'] = [doc for doc in context['documents'] if doc is not None]
    
    return render(request, 'stages/detail_candidature.html', context)

def post_login_redirect(request):
    if request.user.is_superuser:
        return redirect('/admin/')
    elif hasattr(request.user, 'entreprise'):
        return redirect('profil_entreprise', id=request.user.entreprise.id)
    elif hasattr(request.user, 'etudiant'):
        return redirect('etudiant_dashboard')
    else:
        return redirect('dashboard')

# --- Vues statiques ---

class PrivacyPolicyView(TemplateView):
    template_name = "privacy.html"

class TermsView(TemplateView):
    template_name = "terms.html"

class ContactView(TemplateView):
    template_name = "contact.html"

    from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import OffreDeStage, Etudiant, Candidature
from .forms import CandidatureForm
from django.contrib import messages

@login_required
def postuler_offre(request, offre_id):
    # On récupère l'offre ciblée
    offre = get_object_or_404(OffreDeStage, id=offre_id)
    
    # On récupère l'étudiant lié à l'utilisateur connecté
    try:
        etudiant = request.user.etudiant
    except Etudiant.DoesNotExist:
        messages.error(request, "Vous devez être étudiant pour postuler à une offre.")
        return redirect('offres_list')  # Ou une page d'accueil/offres
    
    # Vérifier si l'étudiant a déjà postulé
    if Candidature.objects.filter(etudiant=etudiant, offre=offre).exists():
        messages.warning(request, "Vous avez déjà postulé pour cette offre.")
        return redirect('offre_detail', offre_id=offre.id)

    if request.method == 'POST':
        form = CandidatureForm(request.POST, request.FILES)
        if form.is_valid():
            candidature = form.save(commit=False)
            candidature.etudiant = etudiant
            candidature.offre = offre
            candidature.save()
            messages.success(request, "Votre candidature a été envoyée avec succès.")
            return redirect('offre_detail', offre_id=offre.id)
    else:
        form = CandidatureForm()

    return render(request, 'stages/postuler_offre.html', {
        'form': form,
        'offre': offre,
    })
# stages/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import OffreDeStage, Etudiant, Candidature
from django.contrib.auth.decorators import login_required

@login_required
def offre_detail(request, offre_id):
    offre = get_object_or_404(OffreDeStage, id=offre_id)
    user = request.user

    # Vérifier que l'utilisateur est un étudiant valide
    try:
        etudiant = user.etudiant
    except Etudiant.DoesNotExist:
        etudiant = None

    # Vérifier si l'étudiant a déjà postulé
    candidature_existante = None
    if etudiant:
        candidature_existante = Candidature.objects.filter(etudiant=etudiant, offre=offre).first()

    if request.method == 'POST' and etudiant and not candidature_existante:
        # Créer une candidature
        Candidature.objects.create(etudiant=etudiant, offre=offre)
        messages.success(request, "Votre candidature a bien été enregistrée.")
        return redirect('offre_detail', offre_id=offre.id)

    context = {
        'offre': offre,
        'etudiant': etudiant,
        'candidature_existante': candidature_existante,
    }
    return render(request, 'stages/offre_detail.html', context)
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from .models import Candidature

# views.py
def telecharger_cv(request, candidature_id):
    candidature = get_object_or_404(Candidature, id=candidature_id)
    
    # Vérifie que l'utilisateur est bien l'entreprise propriétaire de l'offre
    if request.user != candidature.offre.entreprise.user:
        raise PermissionDenied
    
    if candidature.cv:
        return FileResponse(candidature.cv.open(), 
                          as_attachment=True,
                          filename=f"CV_{candidature.etudiant.nom}_{candidature.etudiant.prenom}.pdf")
    raise Http404("CV non disponible")

from django.contrib.auth import logout
from django.shortcuts import redirect

def deconnexion(request):
    logout(request)
    return redirect('login')  # Redirige vers la page de connexion
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from .models import Candidature

from django.urls import reverse

@login_required
def modifier_statut_candidature(request, candidature_id, nouveau_statut):
    candidature = get_object_or_404(Candidature, id=candidature_id)
    
    # Vérification que l'utilisateur est bien l'entreprise propriétaire de l'offre
    if request.user != candidature.offre.entreprise.user:
        messages.error(request, "Vous n'avez pas la permission de modifier cette candidature.")
        return redirect('detail_candidature', candidature_id=candidature_id)
    
    # Liste des statuts valides
    statuts_valides = ['en_attente', 'accepte', 'refuse']
    
    if nouveau_statut in statuts_valides:
        candidature.statut = nouveau_statut
        candidature.save()
        messages.success(request, f"La candidature a été marquée comme {candidature.get_statut_display().lower()}.")

        # 🚨 Redirection vers la création de convention si statut = accepte
        if nouveau_statut == 'accepte':
            return redirect(reverse('creer_convention', kwargs={'candidature_id': candidature.id}))
    else:
        messages.error(request, "Statut invalide.")
    
    return redirect('detail_candidature', candidature_id=candidature_id)

# views.py
from django.views.decorators.http import require_GET
from django.http import FileResponse, HttpResponseForbidden

@require_GET
def secure_pdf_view(request, path):
    if not request.user.is_authenticated:  # ← Adaptez à vos besoins
        return HttpResponseForbidden()
    
    file_path = os.path.join(settings.MEDIA_ROOT, 'candidatures_cvs', path)
    
    if not file_path.startswith(settings.MEDIA_ROOT):
        return HttpResponseForbidden()  # Anti path traversal
    
    return FileResponse(open(file_path, 'rb'), content_type='application/pdf')

# stages/views.py
def mes_candidatures(request):
    candidatures = Candidature.objects.filter(etudiant=request.user.etudiant)
    return render(request, 'etudiant/mes_candidatures.html', {'candidatures': candidatures})

from django.views.decorators.http import require_http_methods

@login_required
@require_http_methods(["GET", "POST"])
@login_required
def recommander_candidats(request, offre_id):
    if not hasattr(request.user, 'entreprise'):
        raise PermissionDenied

    offre = get_object_or_404(OffreDeStage, id=offre_id, entreprise=request.user.entreprise)
    ia = RecommandationIA()

    if request.method == "POST" and request.POST.get("reset_cache") == "1":
        cache.delete(f"reco_candidats_{offre_id}")
        cache.delete(f"eval_candidatures_{offre_id}_v2")
        recommandations = ia.recommander_candidats(offre_id, force_recompute=True)
        messages.success(request, "Cache IA vidé et recommandations recalculées.")
    else:
        recommandations = ia.recommander_candidats(offre_id)

    return render(request, 'entreprise/recommandations_ia.html', {
        'offre': offre,
        'recommandations': recommandations,
    })



@login_required
def evaluer_candidatures_ia(request, offre_id):
    if not hasattr(request.user, 'entreprise'):
        raise PermissionDenied
    
    offre = get_object_or_404(OffreDeStage, id=offre_id, entreprise=request.user.entreprise)
    
    ia = RecommandationIA()
    nb_evaluees = ia.evaluer_candidatures(offre_id)
    
    messages.success(request, f"{nb_evaluees} candidatures ont été évaluées par l'IA.")
    return redirect('candidatures_offre', offre_id=offre.id)

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from .models import *
from .forms import *
from django.contrib.auth import login

# --- Conventions de stage ---
@login_required
def mes_conventions(request):
    user = request.user
    if hasattr(user, 'etudiant'):
        conventions = ConventionDeStage.objects.filter(etudiant=user.etudiant).order_by('-date_creation')
    elif hasattr(user, 'entreprise'):
        conventions = ConventionDeStage.objects.filter(entreprise=user.entreprise).order_by('-date_creation')
    else:
        conventions = ConventionDeStage.objects.none()
    return render(request, 'dashboard.html', {'conventions': conventions})


@login_required
def creer_convention(request, candidature_id):
    candidature = get_object_or_404(Candidature, id=candidature_id)

    # Vérification des permissions
    if not (hasattr(request.user, 'entreprise') and candidature.offre.entreprise.user == request.user):
     raise PermissionDenied


    if request.method == 'POST':
        form = ConventionStageForm(request.POST, request.FILES)
        if form.is_valid():
            convention = form.save(commit=False)
            convention.etudiant = candidature.etudiant
            convention.offre = candidature.offre
            convention.entreprise = candidature.offre.entreprise

            # Gestion des statuts selon bouton
            if 'soumettre' in request.POST:
                convention.statut = 'en_attente'
            else:
                convention.statut = 'brouillon'

            if 'signature_etudiant' in request.FILES:
                convention.signature_etudiant = request.FILES['signature_etudiant']
            if 'signature_entreprise' in request.FILES:
                convention.signature_entreprise = request.FILES['signature_entreprise']

            convention.save()

            candidature.statut = 'acceptee'
            candidature.save()

            messages.success(request, "La convention a été créée avec succès.")
            return redirect('detail_convention', convention_id=convention.id)
    else:
        initial = {
            'date_debut': candidature.offre.date_debut,
            'date_fin': candidature.offre.date_debut + timedelta(days=30 * candidature.offre.duree) if candidature.offre.date_debut and candidature.offre.duree else None,
            'gratification': candidature.offre.gratification,
            'tuteur_entreprise': request.user.entreprise.nom_entreprise if hasattr(request.user, 'entreprise') else "",
            'email_tuteur': request.user.email,
            'telephone_tuteur': request.user.entreprise.telephone if hasattr(request.user, 'entreprise') else "",
            'enseignant_referent': candidature.etudiant.enseignant_referent,
        }
        form = ConventionStageForm(initial=initial)

    return render(request, 'conventions/creer.html', {
        'form': form,
        'candidature': candidature,
    })


@login_required
def detail_convention(request, convention_id):
    convention = get_object_or_404(ConventionDeStage, id=convention_id)

    # Vérification des permissions
    if not (request.user == convention.entreprise.user or 
            request.user == convention.etudiant.user or
            (hasattr(request.user, 'enseignant') and 
             request.user.enseignant == convention.enseignant_referent)):
        raise PermissionDenied

    suivis = SuiviStage.objects.filter(convention=convention).order_by('-date_rapport')

    return render(request, 'conventions/detail.html', {
        'convention': convention,
        'suivis': suivis,
        'can_validate': hasattr(request.user, 'enseignant') and request.user.enseignant == convention.enseignant_referent,
    })


@login_required
def valider_convention(request, convention_id):
    convention = get_object_or_404(ConventionDeStage, id=convention_id)

    # Seul l'enseignant référent peut valider
    if not hasattr(request.user, 'enseignant') or request.user.enseignant != convention.enseignant_referent:
        raise PermissionDenied

    if convention.statut != 'en_attente':
        messages.error(request, "Cette convention n'est pas en attente de validation.")
        return redirect('detail_convention', convention_id=convention.id)

    convention.statut = 'validee'
    convention.date_validation = timezone.now()
    convention.save()

    messages.success(request, "La convention a été validée avec succès.")
    return redirect('detail_convention', convention_id=convention.id)

# --- Suivi de stage ---
@login_required
def ajouter_suivi(request, convention_id):
    convention = get_object_or_404(ConventionDeStage, id=convention_id)

    if not (request.user == convention.entreprise.user or 
            request.user == convention.etudiant.user or
            (hasattr(request.user, 'enseignant') and 
             request.user.enseignant == convention.enseignant_referent)):
        raise PermissionDenied

    if request.method == 'POST':
        form = SuiviStageForm(request.POST, request.FILES)
        if form.is_valid():
            suivi = form.save(commit=False)
            suivi.convention = convention
            suivi.auteur = request.user
            suivi.save()

            messages.success(request, "Le suivi a été ajouté avec succès.")
            return redirect('detail_convention', convention_id=convention.id)
    else:
        form = SuiviStageForm()

    return render(request, 'suivis/ajouter.html', {
        'form': form,
        'convention': convention,
    })


# --- Mémoires ---
@login_required
def deposer_memoire(request):
    if not hasattr(request.user, 'etudiant'):
        raise PermissionDenied

    etudiant = request.user.etudiant

    if request.method == 'POST':
        form = MemoireForm(request.POST, request.FILES)
        if form.is_valid():
            memoire = form.save(commit=False)
            memoire.etudiant = etudiant
            memoire.save()

            messages.success(request, "Votre mémoire a été déposé avec succès.")
            return redirect('detail_memoire', memoire_id=memoire.id)
    else:
        form = MemoireForm()

    return render(request, 'memoires/deposer.html', {'form': form})


@login_required
def mes_memoires(request):
    if not hasattr(request.user, 'etudiant'):
        raise PermissionDenied

    memoires = Memoire.objects.filter(etudiant=request.user.etudiant).order_by('-date_depot')
    return render(request, 'memoires/liste.html', {'memoires': memoires})


@login_required
def detail_memoire(request, memoire_id):
    memoire = get_object_or_404(Memoire, id=memoire_id)

    if not (hasattr(request.user, 'etudiant') and memoire.etudiant == request.user.etudiant) \
       and not (hasattr(request.user, 'enseignant') and request.user.enseignant in memoire.jury.all()):
        raise PermissionDenied

    return render(request, 'memoires/detail.html', {'memoire': memoire})


@login_required
def evaluer_memoire(request, memoire_id):
    memoire = get_object_or_404(Memoire, id=memoire_id)

    if not hasattr(request.user, 'enseignant') or request.user.enseignant not in memoire.jury.all():
        raise PermissionDenied

    if request.method == 'POST':
        form = EvaluationMemoireForm(request.POST, instance=memoire)
        if form.is_valid():
            form.save()
            messages.success(request, "Votre évaluation a été enregistrée.")
            return redirect('detail_memoire', memoire_id=memoire.id)
    else:
        form = EvaluationMemoireForm(instance=memoire)

    return render(request, 'memoires/evaluer.html', {
        'form': form,
        'memoire': memoire,
    })


# --- Inscription enseignant ---
def register_enseignant(request):
    if request.method == 'POST':
        form = EnseignantSignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = EnseignantSignupForm()
    return render(request, 'registration/register_enseignant.html', {'form': form})


# --- Dashboard enseignant ---
@login_required
def enseignant_dashboard(request):
    if not hasattr(request.user, 'enseignant'):
        return redirect('dashboard')

    enseignant = request.user.enseignant
    etudiants = Etudiant.objects.filter(enseignant_referent=enseignant)
    conventions = ConventionDeStage.objects.filter(enseignant_referent=enseignant)
    memoires = Memoire.objects.filter(jury=enseignant)

    conventions_attente = conventions.filter(statut='en_attente')

    return render(request, 'enseignant/dashboard.html', {
        'enseignant': enseignant,
        'etudiants': etudiants,
        'conventions_attente': conventions_attente,
        'conventions_count': conventions.count(),
        'memoires_count': memoires.count(),
    })

# --- API pour l'IA ---
@login_required
def api_candidatures_analyse(request, offre_id):
    if not request.user.is_authenticated or not hasattr(request.user, 'entreprise'):
        return JsonResponse({'error': 'Accès non autorisé'}, status=403)
    
    offre = get_object_or_404(OffreDeStage, id=offre_id, entreprise=request.user.entreprise)
    
    ia = RecommandationIA()
    nb_evaluees = ia.evaluer_candidatures(offre_id)
    
    return JsonResponse({
        'status': 'success',
        'offre_id': offre_id,
        'candidatures_evaluees': nb_evaluees
    })
@login_required
def voir_recommandations(request, offre_id):
    if not hasattr(request.user, 'entreprise'):
        raise PermissionDenied
    
    offre = get_object_or_404(OffreDeStage, id=offre_id, entreprise=request.user.entreprise)
    
    # Initialiser l'IA
    ia = RecommandationIA()
    
    # Obtenir les recommandations
    recommandations = ia.recommander_candidats(offre_id)
    
    # Évaluer les candidatures existantes (optionnel)
    ia.evaluer_candidatures(offre_id)
    
    # Récupérer les candidatures existantes avec leurs scores
    candidatures = Candidature.objects.filter(offre=offre).order_by('-score_ia')
    
    return render(request, 'stages/recommandations_ia.html', {
        'offre': offre,
        'recommandations': recommandations,
        'candidatures': candidatures,
    })
from django.shortcuts import redirect

def post_login_redirect(request):
    """
    Redirige l'utilisateur vers la page appropriée après connexion
    """
    if request.user.is_superuser:
        return redirect('/admin/')
    elif hasattr(request.user, 'entreprise'):
        return redirect('profil_entreprise', id=request.user.entreprise.id)
    elif hasattr(request.user, 'etudiant'):
        return redirect('etudiant_dashboard')
    else:
        return redirect('dashboard')
    
@login_required
def candidatures_offre(request, offre_id):
    if not hasattr(request.user, 'entreprise'):
        raise PermissionDenied
    
    offre = get_object_or_404(OffreDeStage, id=offre_id, entreprise=request.user.entreprise)
    candidatures = Candidature.objects.filter(offre=offre).order_by('-score_ia')
    
    return render(request, 'entreprise/candidatures_offre.html', {  # Chemin corrigé
        'offre': offre,
        'candidatures': candidatures
    })

@login_required
def evaluer_candidatures_ia(request, offre_id):
    if not hasattr(request.user, 'entreprise'):
        raise PermissionDenied
    
    offre = get_object_or_404(OffreDeStage, id=offre_id, entreprise=request.user.entreprise)
    
    ia = RecommandationIA()
    nb_evaluees = ia.evaluer_candidatures(offre_id)
    
    if nb_evaluees > 0:
        messages.success(request, f"{nb_evaluees} candidatures ont été évaluées par l'IA.")
    else:
        messages.info(request, "Aucune nouvelle candidature à évaluer.")
    
    return redirect('candidatures_offre', offre_id=offre.id)        

def liste_candidatures_offre(request, offre_id):
    offre = OffreDeStage.objects.get(id=offre_id)
    
    # Évaluer les nouvelles candidatures
  
    RecommandationIA().evaluer_candidatures(offre_id)
    
    # Récupérer les candidatures
    candidatures = Candidature.objects.filter(offre=offre).order_by('-score_ia')
    
    context = {
        'offre': offre,
        'candidatures': candidatures,
        # ... autres variables de contexte
    }
    return render(request, 'candidatures_offre.html', context)

from django.shortcuts import redirect
from stages.ia.recommendation import RecommandationIA


def reevaluer_candidatures(request, offre_id):
    if request.method == 'POST':
        ia = RecommandationIA()
        nombre = ia.evaluer_candidatures(offre_id)
        messages.success(request, f"Réévaluation IA terminée ✅ ({nombre} candidature(s) mise(s) à jour)")
    return redirect('candidature_', offre_id=offre_id)

@login_required
def mes_conventions(request):
    user = request.user
    if hasattr(user, 'etudiant'):
        conventions = ConventionDeStage.objects.filter(etudiant=user.etudiant).order_by('-date_creation')
    else:
        raise PermissionDenied

    return render(request, 'conventions/liste.html', {'conventions': conventions})


from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from django.utils import timezone
import os
from django.conf import settings
from django.contrib.staticfiles import finders
from reportlab.platypus import Image

@login_required
def generer_pdf_convention(request, convention_id):
    convention = get_object_or_404(ConventionDeStage, id=convention_id)

    if not (request.user == convention.etudiant.user or request.user == convention.entreprise.user or request.user.is_staff):
        raise PermissionDenied

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Convention_{convention.etudiant.nom_complet.replace(" ", "_")}.pdf"'

    doc = SimpleDocTemplate(response, pagesize=A4,
                          leftMargin=1*cm, rightMargin=1*cm,
                          topMargin=1.5*cm, bottomMargin=2*cm)
    elements = []
    styles = getSampleStyleSheet()

    # === Styles ===
    header_style = ParagraphStyle(
        name="Header",
        fontSize=10,
        alignment=1,
        fontName="Helvetica"
    )
    
    title_style = ParagraphStyle(
        name="Title",
        fontSize=14,
        alignment=1,
        spaceAfter=12,
        fontName="Helvetica-Bold"
    )
    
    section_title_style = ParagraphStyle(
        name="SectionTitle",
        fontSize=11,
        alignment=0,
        spaceAfter=6,
        fontName="Helvetica-Bold"
    )
    
    normal_style = ParagraphStyle(
        name="Normal",
        fontSize=10,
        alignment=4,  # Justifié
        leading=14,
        spaceAfter=8,
        fontName="Helvetica"
    )
    
    article_title_style = ParagraphStyle(
        name="ArticleTitle",
        fontSize=10,
        alignment=0,
        spaceAfter=4,
        fontName="Helvetica-Bold"
    )
    
    article_content_style = ParagraphStyle(
        name="ArticleContent",
        fontSize=10,
        alignment=4,  # Justifié
        leading=14,
        spaceAfter=12,
        fontName="Helvetica"
    )

    # === En-tête ===
    logo_path = finders.find('img/logo.png')
    if logo_path:
        logo = Image(logo_path, width=2*cm, height=2*cm)
        logo.hAlign = 'CENTER'
        elements.append(logo)
    elements.append(Paragraph("UNIVERSITE CHEIKH ANTA DIOP", header_style))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph("ECOLE SUPERIEURE POLYTECHNIQUE", header_style))
    elements.append(Paragraph("Département Génie Informatique", header_style))
    elements.append(Paragraph("B.P. : 5085 Dakar-Fann (Sénégal)", header_style))
    elements.append(Paragraph("Tél : (221) 33 825 75 28", header_style))
    elements.append(Paragraph("Fax : (221) 33 825 37 24", header_style))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"Année universitaire : {convention.annee_universitaire}", header_style))
    elements.append(Spacer(1, 15))
    
    # === Titre Convention ===
    elements.append(Paragraph("CONVENTION DE STAGE", title_style))
    elements.append(Paragraph("ENTRE", title_style))
    elements.append(Spacer(1, 15))

    # === Partie 1: Etablissement ===
    elements.append(Paragraph("1- L'ETABLISSEMENT D'ENSEIGNEMENT OU DE FORMATION", section_title_style))
    
    etab_data = [
        ["Nom :", "Département Génie Informatique de l'Ecole Supérieure Polytechnique (ESP) de Dakar"],
        ["Adresse :", "UCAD, Dakar, SENEGAL"],
        ["Tél. :", "33 825 75 28"],
        ["Représenté par (signataire de la convention) :", "Professeur Ibrahima FALL"],
        ["Qualité du représentant :", "Chef du Département Génie Informatique"],
        ["Composante/Département :", ""],
        ["Tél. :", ""],
        ["Email :", "secretariat-dgi@esp.sn"],
        ["Adresse (si différente de celle de l'établissement) :", ""]
    ]
    

    etab_table = Table(etab_data, colWidths=[7*cm, 10*cm])
    etab_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4), # Espace sous chaque cellule
        ('TOPPADDING', (0, 0), (-1, -1), 4), 
    ]))
    elements.append(etab_table)
    elements.append(Spacer(1, 15))

    # === Partie 2: Organisme ===
    elements.append(Paragraph("2- L'ORGANISME D'ACCUEIL", section_title_style))
    
    org_data = [
        ["Nom :", convention.entreprise.nom_entreprise],
        ["Adresse :", convention.entreprise.adresse],
        ["Tél. :", convention.entreprise.telephone],
        ["Représenté par (signataire de la convention) :", convention.tuteur_entreprise],
        ["Qualité du représentant :", convention.fonction_tuteur if hasattr(convention, 'fonction_tuteur') else ""],
        ["Composante/Département :", ""],
        ["Tél. :", ""],
        ["Email :", convention.email_tuteur],
        ["Adresse (si différente de celle de l'organisme) :", ""]
    ]
    
    org_table = Table(org_data, colWidths=[6*cm, 10*cm])
    org_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(org_table)
    elements.append(Spacer(1, 15))

    # === Partie 3: Stagiaire ===
    elements.append(Paragraph("3- LE STAGIAIRE", section_title_style))
    
    etudiant = convention.etudiant
    sexe = "M" if etudiant.sexe == 'M' else "F"
    
    stagiaire_data = [
        ["Nom et prénom :", etudiant.nom_complet],
        ["Sexe:", f"{sexe} ☑"],
        ["Né(e) le :", f"{etudiant.date_naissance.strftime('%d/%m/%Y') if etudiant.date_naissance else ''} à {etudiant.lieu_naissance if etudiant.lieu_naissance else ''}"],
        ["Adresse :", etudiant.adresse],
        ["Tél. :", etudiant.telephone],
        ["Email :", etudiant.email],
        ["", ""],
        ["Intitulé de la formation ou du cursus suivi à l'ESP-UCAD :", 
         f"{etudiant.niveau_etude}, option {etudiant.domaine_etude}"]
    ]
    
    stagiaire_table = Table(stagiaire_data, colWidths=[6*cm, 10*cm])
    stagiaire_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(stagiaire_table)
    elements.append(Spacer(1, 15))

    # === Texte introductif ===
    elements.append(Paragraph("Il est convenu ce qui suit :", normal_style))
    elements.append(Spacer(1, 15))

    # === Articles ===
    articles = [
        ("Article 1 :", 
         f"L'étudiant(e) sera accueilli(e) comme stagiaire dans l'établissement susnommé pour réaliser un travail sur un projet en informatique ou en télécoms."),
         
        ("Article 2 :", 
         f"Pendant la durée du stage, le(la) stagiaire sera placé(e) sous l'autorité scientifique de l'encadrant désigné par l'établissement de formation et du maître de stage désigné par l'organisme d'accueil."),
         
        ("Article 3 :", 
         f"Le stage est prévu du {convention.date_debut.strftime('%d %B %Y')} au {convention.date_fin.strftime('%d %B %Y')}."),
         
        ("Article 4 :", 
         "Durant son séjour dans l'organisme, le(la) stagiaire conservera son statut d'étudiant(e) de l'ESP et sera couvert par une assurance."),
         
        ("Article 5 :", 
         "Au cours de ce stage, il appartient à l'organisme de décider s'il y a lieu, de l'opportunité de remboursements de frais à accorder au stagiaire. La rémunération n'étant pas due expressément au titre du stage, l'organisme pourra accorder une indemnité forfaitaire."),
         
        ("Article 6 :", 
         "Pendant son séjour dans l'organisme, le(la) stagiaire est soumis(e) au règlement intérieur de celui-ci, notamment en ce qui concerne l'organisation du travail, les règlements d'hygiène et de sécurité."),
         
        ("Article 7 :", 
         "En cas de dérogation à ce règlement, le Directeur de l'organisme d'accueil peut interrompre le stage après en avoir dûment informé le Chef du Département Génie Informatique."),
         
        ("Article 8 :", 
         "Le(la) stagiaire pourra bénéficier, dans le cadre de son travail de l'infrastructure et du matériel nécessaire."),
         
        ("Article 9 :", 
         "Le(la) stagiaire est tenu par le secret professionnel le plus strict durant la réalisation des procédés de fabrication exploités ou étudiés par l'organisme ainsi que les recherches poursuivies et les renseignements recueillis lors des travaux."),
         
        ("Article 10 :", 
         "En fin de stage, le(la) stagiaire présentera un rapport destiné aux signataires de la présente convention, qui fera l'objet d'une présentation orale en présence des enseignants du département et des représentants de l'organisme. En cas de confidentialité des travaux du(de la) stagiaire, mention en sera faite sur ledit rapport, qui fera l'objet d'une diffusion restreinte précisée par un avenant à ladite convention.")
    ]

    for article_num, article_content in articles:
        elements.append(Paragraph(article_num, article_title_style))
        elements.append(Paragraph(article_content, article_content_style))

    elements.append(Spacer(1, 20))

    # === Signatures ===
    elements.append(Paragraph("LE(LA) STAGIAIRE (signature)", normal_style))
    elements.append(Spacer(1, 30))
    elements.append(Paragraph(f"Dakar, le ......... {timezone.now().strftime('%d/%m/%Y')}", normal_style))
    elements.append(Spacer(1, 30))

    elements.append(Paragraph("POUR L'ORGANISME D'ACCUEIL (nom, prénom, signature et cachet)", normal_style))
    elements.append(Spacer(1, 30))
    elements.append(Paragraph(f"Dakar, le ......... {timezone.now().strftime('%d/%m/%Y')}", normal_style))
    elements.append(Spacer(1, 30))

    elements.append(Paragraph("POUR LE DEPARTEMENT GENIE INFORMATIQUE (nom, prénom, signature et cachet)", normal_style))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph("Professeur Ibrahima FALL", normal_style))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(f"Dakar, le ......... {timezone.now().strftime('%d/%m/%Y')}", normal_style))
    elements.append(Spacer(1, 15))

    elements.append(Paragraph("Document établi en trois (03) exemplaires", normal_style))

    doc.build(elements)
    return response

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Etudiant
from .ia.recommendation import RecommandationIA


@login_required
@login_required
def offres_recommandees(request):
    etudiant = get_object_or_404(Etudiant, user=request.user)
    ia = RecommandationIA()
    
    if request.method == 'POST':
        # Force le recalcul des recommandations
        offres_recommandees = ia.recommander_offres(etudiant.id, force_recompute=True)
        messages.success(request, "Recommandations actualisées avec succès !")
    else:
        # Utilise le cache existant
        offres_recommandees = ia.recommander_offres(etudiant.id)
    
    context = {
        'offres_recommandees': offres_recommandees,
        'etudiant': etudiant
    }
    return render(request, 'etudiant/offres_recommandees.html', context)

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from stages.models import OffreDeStage
from stages.ia.recommendation import RecommandationIA


@login_required
def tableau_de_bord_entreprise(request):
    entreprise = request.user.entreprise
    offres_actives = OffreDeStage.objects.filter(entreprise=entreprise, est_valide=True)

    ia = RecommandationIA()
    top_recommandations = []
    if offres_actives:
        top_recommandations = ia.recommander_candidats(offres_actives[0].id)

    return render(request, "entreprise/tableau_de_bord.html", {
        "offres_actives": offres_actives,
        "top_recommandations": top_recommandations,
    })
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Conversation, Message

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from .models import Conversation, Message

User = get_user_model()

@login_required
def start_conversation(request, user_id):
    other_user = get_object_or_404(User, id=user_id)

    conversation = Conversation.objects.filter(
        (Q(participant1=request.user) & Q(participant2=other_user)) |
        (Q(participant1=other_user) & Q(participant2=request.user))
    ).first()

    if not conversation:
        conversation = Conversation.objects.create(
            participant1=request.user,
            participant2=other_user
        )

    return redirect('view_conversation', conversation_id=conversation.id)



@login_required
def view_conversation(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id)

    # Vérifier que l'utilisateur est participant
    if request.user != conversation.participant1 and request.user != conversation.participant2:
        return redirect('liste_conversations')

    # Identifier l'autre participant
    other_user = conversation.participant2 if conversation.participant1 == request.user else conversation.participant1

    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            Message.objects.create(
                conversation=conversation,
                sender=request.user,
                content=content
            )
        return redirect('view_conversation', conversation_id=conversation_id)

    messages = conversation.messages.order_by('timestamp')

    context = {
        'conversation': conversation,
        'messages': messages,
        'other_user': other_user,
    }
    return render(request, 'messaging/conversation.html', context)


@login_required
def liste_conversations(request):
    # Récupérer toutes les conversations où l'utilisateur est participant
    conversations = Conversation.objects.filter(
        Q(participant1=request.user) | Q(participant2=request.user)
    ).order_by('-updated_at')

    context = {
        'conversations': conversations
    }
    return render(request, 'messaging/liste_conversations.html', context)



def liste_conversations(request):
    # Récupérer les conversations de l’utilisateur connecté
    conversations = []  # À remplacer par ta logique réelle
    return render(request, 'messaging/liste_conversations.html', {'conversations': conversations})


@login_required
def liste_conversations(request):
    conversations = Conversation.objects.filter(
        Q(participant1=request.user) | Q(participant2=request.user)
    ).order_by('-updated_at')

    return render(request, 'messaging/liste_conversations.html', {'conversations': conversations})

from .models import Annonce, Etudiant

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.http import HttpResponseForbidden
from .models import Annonce, Etudiant

@login_required
@login_required
def ajouter_annonce(request):
    # Vérifier si l'utilisateur est admin ou chef de département
    is_admin = request.user.is_superuser
    is_chef = hasattr(request.user, 'chefdepartement')  # Utilise la relation OneToOne
    
    if not (is_admin or is_chef):
        messages.error(request, "Seuls les administrateurs et chefs de département peuvent publier des annonces.")
        return redirect('dashboard')

    if request.method == 'POST':
        try:
            titre = request.POST['titre']
            contenu = request.POST['contenu']
            fichier = request.FILES.get('fichier')
            
            # Déterminer le département
            if is_chef:
                departement = request.user.chefdepartement.departement
            else:  # Cas admin
                # Vous pourriez avoir besoin d'un sélecteur de département dans le formulaire
                # Pour l'instant, nous retournons une erreur
                messages.error(request, "Les administrateurs doivent spécifier un département.")
                return redirect('ajouter_annonce')

            # Créer l'annonce
            Annonce.objects.create(
                titre=titre,
                contenu=contenu,
                fichier=fichier,
                departement=departement,
                auteur=request.user
            )
            messages.success(request, "Annonce publiée avec succès!")
            
        except Exception as e:
            messages.error(request, f"Erreur lors de la publication: {str(e)}")
            return redirect('ajouter_annonce')

    return render(request, 'messaging/ajouter_annonce.html')
@login_required
def annonces_etudiant(request):
    try:
        etudiant = Etudiant.objects.get(user=request.user)
        # Exclure les annonces que l'étudiant a masquées
        annonces = Annonce.objects.filter(
            departement=etudiant.departement
        ).exclude(
            id__in=etudiant.annonces_masquees.values_list('id', flat=True)
        ).order_by('-date_publication')
        
        etudiant.last_annonce_vue = timezone.now()
        etudiant.save()
        return render(request, 'messaging/annonces_etudiant.html', {
            'annonces': annonces,
            'can_delete': True  # Maintenant cela signifie "masquer" plutôt que supprimer
        })
    except Etudiant.DoesNotExist:
        return HttpResponseForbidden("Profil étudiant non trouvé.")

@login_required
def dashboard_etudiant(request):
    try:
        etudiant = Etudiant.objects.get(user=request.user)
        # Compter seulement les annonces non masquées et nouvelles
        nouvelles_annonces = Annonce.objects.filter(
            departement=etudiant.departement,
            date_publication__gt=etudiant.last_annonce_vue
        ).exclude(
            id__in=etudiant.annonces_masquees.values_list('id', flat=True)
        ).count()
        return render(request, 'etudiant/dashboard.html', {
            'nouvelles_annonces': nouvelles_annonces
        })
    except Etudiant.DoesNotExist:
        return HttpResponseForbidden("Profil étudiant non trouvé.")

@login_required
def supprimer_annonce(request, annonce_id):
    annonce = get_object_or_404(Annonce, id=annonce_id)
    try:
        etudiant = Etudiant.objects.get(user=request.user)
        if etudiant.departement == annonce.departement:
            # Au lieu de supprimer, on ajoute à la liste des annonces masquées
            etudiant.annonces_masquees.add(annonce)
            messages.success(request, "L'annonce a été masquée avec succès.")
        else:
            messages.error(request, "Cette annonce ne concerne pas votre département.")
    except Etudiant.DoesNotExist:
        messages.error(request, "Profil étudiant non trouvé.")
    
    return redirect('liste_annonces')

from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User

@staff_member_required
def admin_validation(request):
    users = User.objects.filter(is_active=False)
    return render(request, 'admin_validation.html', {'users': users})

@staff_member_required
def valider_utilisateur(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.is_active = True
    user.save()
    return redirect('admin_validation')

# stages/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .forms import EtudiantForm

@login_required
def modifier_profil_etudiant(request):
    etudiant = request.user.etudiant
    if request.method == 'POST':
        form = EtudiantForm(request.POST, request.FILES, instance=etudiant)
        if form.is_valid():
            form.save()
            messages.success(request, "Profil mis à jour avec succès.")
            return redirect('etudiant_dashboard')  # ✅ Redirige proprement
    else:
        form = EtudiantForm(instance=etudiant)
    
    return render(request, 'etudiant/modifier_profil.html', {'form': form})

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from .forms import EntrepriseForm

@login_required
def modifier_profil_entreprise(request,):
    entreprise = request.user.entreprise
    if request.method == 'POST':
        form = EntrepriseForm(request.POST, request.FILES, instance=entreprise)
        if form.is_valid():
            form.save()
            messages.success(request, "Profil mis à jour avec succès.")
            
    else:
        form = EntrepriseForm(instance=entreprise)

    return render(request, 'stages/modifier_profil_entreprise.html', {'form': form})

import logging
from django.contrib import messages
from django.core.mail import send_mail
from smtplib import SMTPException
import socket

logger = logging.getLogger(__name__)

def register_entreprise(request):
    if request.method == "POST":
        form = EntrepriseForm(request.POST)
        if form.is_valid():
            entreprise = form.save(commit=False)
            entreprise.est_valide = False  # Par exemple, en attente de validation admin
            entreprise.save()

            # Essayer d’envoyer un mail de confirmation
            try:
                send_mail(
                    subject="Confirmation de votre inscription",
                    message="Merci pour votre inscription. Votre compte est en attente de validation.",
                    from_email="noreply@tonsite.com",
                    recipient_list=[entreprise.email_contact],
                    fail_silently=False,
                )
                messages.success(request, "Votre compte a été créé. Un email de confirmation a été envoyé.")
            except (SMTPException, socket.gaierror) as e:
                logger.error(f"Erreur lors de l'envoi de l'email d'inscription: {e}")
                messages.warning(request, "Compte créé, mais l'email de confirmation n'a pas pu être envoyé.")

            return redirect('login')  # Ou autre page
    else:
        form = EntrepriseForm()

    return render(request, 'entreprise/register.html', {'form': form})

@login_required
def modifier_memoire(request, memoire_id):
    memoire = get_object_or_404(Memoire, id=memoire_id, etudiant=request.user.etudiant)
    if request.method == 'POST':
        form = MemoireForm(request.POST, request.FILES, instance=memoire)
        if form.is_valid():
            form.save()
            messages.success(request, "Mémoire/rapport modifié avec succès.")
            return redirect('detail_memoire', memoire_id=memoire.id)
    else:
        form = MemoireForm(instance=memoire)
    return render(request, 'memoires/modifier.html', {'form': form, 'memoire': memoire})

from django.views.generic import DeleteView
from django.urls import reverse_lazy
from .models import Memoire

class SupprimerMemoireView(DeleteView):
    model = Memoire
    template_name = 'memoires/confirmation_suppression.html'  # Créez ce template si nécessaire
    success_url = reverse_lazy('mes_memoire')  # Redirection après suppression
    
    # Si vous voulez utiliser le même template que detail.html pour la confirmation
    def get_template_names(self):
        if 'delete' in self.request.GET:
            return ['memoires/detail.html']
        return super().get_template_names()

from .models import (Annonce, Etudiant, OffreDeStage, Entreprise, 
                    ConventionDeStage, Memoire, ChefDepartement)

from django.shortcuts import render
from django.http import HttpResponseForbidden
from datetime import date
from .models import (
    Annonce, ChefDepartement, Etudiant, ConventionDeStage, Entreprise,
    OffreDeStage, Memoire, Stage
)

def liste_annonces(request):
    # Détection du rôle
    try:
        chef = ChefDepartement.objects.get(user=request.user)
        departement = chef.departement
        is_etudiant = False
    except ChefDepartement.DoesNotExist:
        if request.user.is_superuser:
            departement = None
            is_etudiant = False
        else:
            try:
                etudiant = Etudiant.objects.get(user=request.user)
                departement = etudiant.departement
                is_etudiant = True
            except Etudiant.DoesNotExist:
                return HttpResponseForbidden("Accès non autorisé")

    # Date du jour
    today = date.today()

    # Contexte général
    context = {
        # Annonces du département
        'annonces': Annonce.objects.filter(departement=departement).order_by('-date_publication') if departement else Annonce.objects.all().order_by('-date_publication'),

        # Étudiants du département (seulement pour chefs/admin)
        'etudiants': Etudiant.objects.filter(departement=departement, est_valide=True) if departement and not is_etudiant else None,

        # Conventions validées
        'etudiants_avec_stage': ConventionDeStage.objects.filter(
            etudiant__departement=departement,
            statut='validee'
        ).select_related('etudiant', 'entreprise') if departement and not is_etudiant else None,

        # 🔵 Stages en cours
        'stages_en_cours': Stage.objects.filter(
            etudiant__departement=departement,
            statut='en_cours',
            date_debut_reelle__lte=today,
            date_fin_reelle__gte=today
        ) if departement and not is_etudiant else None,

        # 🟡 Stages en attente (optionnel)
        'stages_en_attente': Stage.objects.filter(
            etudiant__departement=departement,
            statut='en_attente'
        ) if departement and not is_etudiant else None,

        # 🟢 Stages terminés (optionnel)
        'stages_termines': Stage.objects.filter(
            etudiant__departement=departement,
            statut='termine'
        ) if departement and not is_etudiant else None,

        # Entreprises ayant publié des offres
        'entreprises_offres': Entreprise.objects.filter(
            offredestage__est_valide=True,
            offredestage__domaine__in=[departement.nom] if departement else None
        ).distinct() if departement and not is_etudiant else None,

        # Mémoires
        'memoires': Memoire.objects.filter(
            etudiant__departement=departement
        ).select_related('etudiant') if departement and not is_etudiant else None,

        # Statistiques
        'stats': {
            'total_etudiants': Etudiant.objects.filter(departement=departement).count() if departement and not is_etudiant else None,
            'etudiants_stages': ConventionDeStage.objects.filter(
                etudiant__departement=departement,
                statut='validee'
            ).count() if departement and not is_etudiant else None,
            'offres_actives': OffreDeStage.objects.filter(
                est_valide=True,
                domaine__in=[departement.nom] if departement else None
            ).count() if departement and not is_etudiant else None,
        },

        'departement': departement,
        'is_chef': hasattr(request.user, 'chefdepartement'),
        'is_admin': request.user.is_superuser,
        'is_etudiant': is_etudiant
    }

    return render(request, 'messaging/liste_annonces.html', context)


from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from .models import Annonce

def masquer_annonce(request, annonce_id):
    annonce = get_object_or_404(Annonce, id=annonce_id)
    annonce.est_visible = False
    annonce.save()
    messages.info(request, "Annonce masquée.")
    return redirect('liste_annonces')

def afficher_annonce(request, annonce_id):
    annonce = get_object_or_404(Annonce, id=annonce_id)
    annonce.est_visible = True
    annonce.save()
    messages.success(request, "Annonce rendue visible.")
    return redirect('liste_annonces')

def supprimer_annonce(request, annonce_id):
    annonce = get_object_or_404(Annonce, id=annonce_id)
    if request.method == "POST":
        annonce.delete()
        messages.success(request, "Annonce supprimée avec succès.")
    return redirect('liste_annonces')

from django.shortcuts import render, get_object_or_404, redirect
from .models import Annonce
from .forms import AnnonceForm  # à adapter selon ton projet

def modifier_annonce(request, annonce_id):
    annonce = get_object_or_404(Annonce, id=annonce_id)
    if request.method == 'POST':
        form = AnnonceForm(request.POST, request.FILES, instance=annonce)
        if form.is_valid():
            form.save()
            messages.success(request, "Annonce mise à jour avec succès.")
    else:
        form = AnnonceForm(instance=annonce)
    return render(request, 'annonces/modifier_annonce.html', {'form': form})

from .models import Stage
from datetime import date

def dashboard_chef(request):
    today = date.today()
    stages_en_cours = Stage.objects.filter(
        statut='en_cours',
        date_debut_reelle__lte=today,
        date_fin_reelle__gte=today
    )
    return render(request, 'dashboard.html', {
        'stages_en_cours': stages_en_cours
    })
