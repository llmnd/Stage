from django.contrib import admin
from .models import Entreprise, OffreDeStage, Etudiant

@admin.register(Entreprise)
class ProfilEntrepriseAdmin(admin.ModelAdmin):
    list_display = ("user", "nom_entreprise", "est_valide")
    list_filter = ("est_valide",)
    readonly_fields = ('logo_preview',)

    def logo_preview(self, obj):
        from django.utils.html import format_html
        if obj.logo:
            return format_html('<img src="{}" style="max-height: 100px; max-width: 100px;" />', obj.logo.url)
        return "Aucun logo"
    logo_preview.short_description = 'Aperçu du logo'

@admin.register(OffreDeStage)
class OffreDeStageAdmin(admin.ModelAdmin):
    list_display = ("titre", "entreprise", "date_publication")
    search_fields = ("titre", "entreprise__nom_entreprise")
    list_filter = ("date_publication",)

@admin.register(Etudiant)
class EtudiantAdmin(admin.ModelAdmin):
    list_display = ('nom_complet', 'email', 'universite', 'est_valide')
    list_filter = ('est_valide', 'universite')
    actions = ['valider_etudiants']

    def valider_etudiants(self, request, queryset):
        queryset.update(est_valide=True)
    valider_etudiants.short_description = "Valider les étudiants sélectionnés"
    from django.contrib import admin
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.contrib.admin.sites import AdminSite
from django.template.response import TemplateResponse
from django.db.models import Count

class CustomAdminSite(AdminSite):
    site_header = "Administration ESP Stages"
    site_title = "ESP Stages Admin"
    index_title = "Tableau de bord"

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('custom_dashboard/', self.admin_view(self.custom_dashboard), name='custom_dashboard'),
        ]
        return custom_urls + urls

    def custom_dashboard(self, request):
        # Récupérer les statistiques
        from django.contrib.auth.models import User
        from stages.models import OffreDeStage, Entreprise, Candidature
        
        stats = {
            'users': User.objects.count(),
            'offers': OffreDeStage.objects.count(),
            'companies': Entreprise.objects.count(),
            'applications': Candidature.objects.count(),
        }

        # Simuler une activité récente (à adapter avec vos modèles)
        recent_activity = [
            {'icon': 'user-plus', 'title': 'Nouvel utilisateur créé', 'date': '2023-05-01 14:30'},
            {'icon': 'briefcase', 'title': 'Nouvelle offre publiée', 'date': '2023-05-01 12:15'},
            {'icon': 'building-2', 'title': 'Nouvelle entreprise ajoutée', 'date': '2023-04-30 16:45'},
        ]

        context = {
            **self.each_context(request),
            'stats': stats,
            'recent_activity': recent_activity,
        }
        return TemplateResponse(request, 'admin/admin_dashboard.html', context)

    def index(self, request, extra_context=None):
        if request.user.is_superuser:
            return HttpResponseRedirect(reverse('admin:custom_dashboard'))
        return super().index(request, extra_context)

# Remplacez l'admin par défaut
admin_site = CustomAdminSite(name='customadmin')

# Enregistrez vos modèles normalement
from django.contrib.auth.models import User, Group
admin_site.register(User)
admin_site.register(Group)

# Enregistrez vos autres modèles
from stages.models import OffreDeStage, Entreprise, Candidature
admin_site.register(OffreDeStage)
admin_site.register(Entreprise)
admin_site.register(Candidature)