from .admin import admin_site
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import TemplateView
from django.shortcuts import redirect
from stages import views
from django.conf import settings
from django.conf.urls.static import static
from .views import mes_candidatures
from .views import voir_recommandations
from .views import offres_recommandees
from .views import register_choice, register_etudiant, register_entreprise
from stages.views import admin_validation, valider_utilisateur
from .views import modifier_profil_etudiant
from .views import SupprimerMemoireView
from .views import liste_annonces





from stages.views import (
    RegisterView,
    dashboard,
    liste_offres,
    ajouter_offre,
    signup_entreprise,
    valider_entreprises,
    etudiant_dashboard,
    post_login_redirect,
    modifier_profil_entreprise,
    PrivacyPolicyView,
    TermsView,
    ContactView,
    detail_offre,
    postuler_offre,
    mon_profil_entreprise,
    profil_entreprise,
    page_etudiant,
    modifier_offre,
    supprimer_offre,
    detail_candidature
)

urlpatterns = [
    # Admin
    path('admin/', admin_site.urls),

    # Authentification
    path('accounts/', include('django.contrib.auth.urls')),
    path('login/', LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('redirect/', post_login_redirect, name='post_login_redirect'),
    path('register/', RegisterView.as_view(), name='register'),

    # Accueil : redirection vers login
    path('', lambda request: redirect('login'), name='home'),

    # Pages statiques
    path('privacy/', PrivacyPolicyView.as_view(), name='privacy'),
    path('terms/', TermsView.as_view(), name='terms'),
    path('contact/', ContactView.as_view(), name='contact'),
    path('faq/', TemplateView.as_view(template_name='faq.html'), name='faq'),
    path('about/', TemplateView.as_view(template_name='about.html'), name='about'),

    # Offres de stage
    path('offres/', liste_offres, name='liste_offres'),
    path('ajouter/', ajouter_offre, name='ajouter_offre'),
    path('offre/<int:offre_id>/', detail_offre, name='detail_offre'),
    path('offre/<int:offre_id>/modifier/', modifier_offre, name='modifier_offre'),
    path('offre/<int:offre_id>/supprimer/', supprimer_offre, name='supprimer_offre'),
    path('postuler/<int:offre_id>/', postuler_offre, name='postuler_offre'),

    # Candidatures
    path('candidature/<int:candidature_id>/', detail_candidature, name='detail_candidature'),

    # Espace Entreprise
    path('signup/entreprise/', signup_entreprise, name='signup_entreprise'),
    path('admin/valider-entreprises/', valider_entreprises, name='valider_entreprises'),
    path('entreprise/mon-profil/', mon_profil_entreprise, name='mon_profil_entreprise'),
    path('entreprise/espace/', profil_entreprise, name='espace_entreprise'),
    path('entreprise/modifier-profil/', modifier_profil_entreprise, name='modifier_profil_entreprise'),
    path('entreprise/profil/', profil_entreprise, name='profil_entreprise'),
    path('entreprise/profil/<int:id>/', views.profil_entreprise, name='profil_entreprise'),


    # Espace Étudiant
    path('etudiant/', etudiant_dashboard, name='page_etudiant'),
    path('etudiant/dashboard/', etudiant_dashboard, name='etudiant_dashboard'),
    path('login/etudiant/', page_etudiant, name='login_etudiant'),
    path('dashboard/', dashboard, name='dashboard'),
    path('entreprise/voir/<int:id>/', views.voir_profil_entreprise, name='voir_profil_entreprise'),
    path('offre/<int:pk>/', views.detail_offre, name='offre_detail'),
    path('candidature/<int:candidature_id>/telecharger-cv/', views.telecharger_cv, name='telecharger_cv'),
    path('deconnexion/', views.deconnexion, name='deconnexion'),
    path('candidature/<int:candidature_id>/modifier-statut/<str:nouveau_statut>/', 
         views.modifier_statut_candidature, 
         name='modifier_statut_candidature'),
         path('mes-candidatures/', mes_candidatures, name='mes_candidatures'),

          path('offre/<int:offre_id>/recommandations/', views.recommander_candidats, name='recommandations_ia'),
    path('offre/<int:offre_id>/evaluer-candidatures/', views.evaluer_candidatures_ia, name='evaluer_candidatures_ia'),
    path('api/offre/<int:offre_id>/analyse-candidatures/', views.api_candidatures_analyse, name='api_analyse_candidatures'),
    
    # Conventions
    path('candidature/<int:candidature_id>/convention/', views.creer_convention, name='creer_convention'),
    path('convention/<int:convention_id>/', views.detail_convention, name='detail_convention'),
    path('convention/<int:convention_id>/valider/', views.valider_convention, name='valider_convention'),
    
    # Suivi
    path('convention/<int:convention_id>/suivi/ajouter/', views.ajouter_suivi, name='ajouter_suivi'),
    
    # Mémoires
    path('memoires/deposer/', views.deposer_memoire, name='deposer_memoire'),
    path('memoires/mes-memoires/', views.mes_memoires, name='mes_memoires'),
    path('memoire/<int:memoire_id>/evaluer/', views.evaluer_memoire, name='evaluer_memoire'),
    path('memoire/<int:memoire_id>/modifier/', views.modifier_memoire, name='modifier_memoire'),
    path('memoires/<int:memoire_id>/', views.detail_memoire, name='detail_memoire'),

    # Enseignants
    path('register/enseignant/', views.register_enseignant, name='register_enseignant'),
    path('enseignant/dashboard/', views.enseignant_dashboard, name='enseignant_dashboard'),
    path('offre/<int:offre_id>/candidatures/', views.candidatures_offre, name='candidature_offre'),
    path('offre/<int:offre_id>/candidatures/', views.liste_candidatures_offre, name='candidatures_offre'),
    path('offre/<int:offre_id>/evaluer-candidatures/', views.evaluer_candidatures_ia, name='evaluer_candidatures'),
    path('entreprise/offre/<int:offre_id>/reevaluer/', views.reevaluer_candidatures, name='reevaluer_candidatures'),
    path('conventions/', views.mes_conventions, name='mes_conventions'),
    path('mes-conventions/', views.mes_conventions, name='mes_conventions'),
    path('convention/creer/<int:candidature_id>/', views.creer_convention, name='creer_convention'),

    path('convention/<int:convention_id>/pdf/', views.generer_pdf_convention, name='generer_pdf_convention'),
    path('register/', RegisterView.as_view(), name='register_choice'),
    path('register/success/', TemplateView.as_view(template_name='registration/register_success.html'), name='register_success'),
    path('etudiant/recommandations/', offres_recommandees, name='offres_recommandees'),
    path('recommander-candidats/<int:offre_id>/', views.recommander_candidats, name='recommander_candidats'),
    path('conversation/start/<int:user_id>/', views.start_conversation, name='start_conversation'),
    path('conversation/<int:conversation_id>/', views.view_conversation, name='view_conversation'),
    path('conversations/', views.liste_conversations, name='liste_conversations'),
    path('annonce/ajouter/', views.ajouter_annonce, name='ajouter_annonce'),
    path('annonces/supprimer/<int:annonce_id>/', views.supprimer_annonce, name='supprimer_annonce'),
    path('messaging/liste_annonces/', views.liste_annonces, name='liste_annonces'),
    path('annonce/<int:annonce_id>/modifier/', views.modifier_annonce, name='modifier_annonce'),
    path('annonce/<int:annonce_id>/masquer/', views.masquer_annonce, name='masquer_annonce'),
    path('annonce/<int:annonce_id>/afficher/', views.afficher_annonce, name='afficher_annonce'),
    path('annonce/<int:annonce_id>/supprimer/', views.supprimer_annonce, name='supprimer_annonce'),
    path('annonces/', liste_annonces, name='liste_annonces'),
    path('chatbot/', include('chatbot.urls')),
    path('register/', register_choice, name='register_choice'),
    path('register/etudiant/', register_etudiant, name='register_etudiant'),
    path('register/entreprise/', register_entreprise, name='register_entreprise'),
    path('admin/validation/', admin_validation, name='admin_validation'),
    path('admin/valider/<int:user_id>/', valider_utilisateur, name='valider_utilisateur'),
    path('etudiant/modifier_profil/', modifier_profil_etudiant, name='modifier_profil_etudiant'),
    path('entreprise/modifier-profil/', views.modifier_profil_entreprise, name='modifier_profil_entreprise'),
    path('memoires/<int:pk>/supprimer/', SupprimerMemoireView.as_view(), name='supprimer_memoire'),



] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
