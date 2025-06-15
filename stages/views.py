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




# --- Authentification et inscriptions ---

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

def register_view(request):
    if request.method == 'POST':
        form = EtudiantSignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = EtudiantSignupForm()
    return render(request, 'registration/register.html', {'form': form})

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

@login_required
def modifier_profil_entreprise(request):
    entreprise = getattr(request.user, 'entreprise', None)
    if not entreprise:
        return redirect('login')

    if request.method == 'POST':
        form = EntrepriseForm(request.POST, instance=entreprise)
        if form.is_valid():
            form.save()
            return redirect('mon_profil_entreprise')
    else:
        form = EntrepriseForm(instance=entreprise)

    return render(request, 'stages/modifier_profil.html', {'form': form})

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

    # Empêche les étudiants ou autres entreprises d'accéder
    if not hasattr(request.user, 'entreprise') or request.user.entreprise.id != entreprise.id:
        return redirect('voir_profil_entreprise', id=entreprise.id)

    offres = OffreDeStage.objects.filter(entreprise=entreprise)
    candidatures = Candidature.objects.filter(offre__entreprise=entreprise)

    if request.method == 'POST':
        form = OffreDeStageForm(request.POST)
        if form.is_valid():
            offre = form.save(commit=False)
            offre.entreprise = entreprise
            offre.save()
            return redirect('profil_entreprise', id=entreprise.id)
    else:
        form = OffreDeStageForm()

    context = {
        'entreprise': entreprise,
        'offres': offres,
        'candidatures': candidatures,
        'form': form,
    }
    return render(request, 'stages/profil_entreprise.html', context)

# --- Étudiants ---

@login_required
def etudiant_dashboard(request):
    return render(request, 'etudiant/dashboard.html')

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

