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
