# signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from stages.models import OffreDeStage, Etudiant
from stages.ia.recommendation import RecommandationIA
from stages.models import Candidature

@receiver(post_save, sender=Candidature)
def reevaluation_automatique(sender, instance, created, **kwargs):
    # Réévalue seulement si score_ia est vide ou à la création
    if created or instance.score_ia is None:
        ia = RecommandationIA()
        score = ia.calculer_score_spacy(
            f"{instance.offre.titre} {instance.offre.description} {instance.offre.domaine} {instance.offre.competences_requises}",
            f"{instance.etudiant.competences} {instance.etudiant.domaine_etude} {instance.etudiant.realisations}"
        )
        feedback = ia.generer_feedback(score)
        instance.score_ia = round(score * 100, 1)
        instance.feedback_ia = feedback
        instance.save()
# signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from .models import Entreprise, Etudiant

@receiver(post_save, sender=Entreprise)
def notify_admin_new_entreprise(sender, instance, created, **kwargs):
    if created and not instance.est_valide:
        send_mail(
            "Nouvelle entreprise en attente de validation",
            f"L'entreprise {instance.nom_entreprise} attend une validation.",
            "admin@esp.sn",  # From
            ["admin@esp.sn"],  # To
        )

@receiver(post_save, sender=Etudiant)
def notify_admin_new_etudiant(sender, instance, created, **kwargs):
    if created and not instance.est_valide:
        send_mail(
            "Nouvel étudiant en attente de validation",
            f"L'étudiant {instance.nom_complet} attend une validation.",
            "admin@esp.sn",  # From
            ["admin@esp.sn"],
        )

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Etudiant, Entreprise
from django.core.mail import mail_admins

@receiver(post_save, sender=Etudiant)
def notify_admin_new_etudiant(sender, instance, created, **kwargs):
    if created:
        mail_admins(
            subject="Nouvel étudiant inscrit",
            message=f"Un nouvel étudiant vient de s'inscrire : {instance.nom_complet} ({instance.email})",
        )

@receiver(post_save, sender=Entreprise)
def notify_admin_new_entreprise(sender, instance, created, **kwargs):
    if created:
        mail_admins(
            subject="Nouvelle entreprise inscrite",
            message=f"Nouvelle entreprise : {instance.nom_entreprise} ({instance.user.email})",
        )

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Candidature, Stage


@receiver(post_save, sender=Candidature)
def creer_stage_apres_acceptation(sender, instance, created, **kwargs):
    if instance.statut == 'acceptee':
        Stage.objects.get_or_create(
            etudiant=instance.etudiant,
            offre=instance.offre,
            entreprise=instance.offre.entreprise,
        )

