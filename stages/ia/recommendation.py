import spacy
import fitz  # PyMuPDF
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
from stages.models import OffreDeStage, Etudiant, Candidature
from spacy.lang.fr.stop_words import STOP_WORDS


class SpacyModelSingleton:
    _model = None

    @classmethod
    def get_model(cls):
        if cls._model is None:
            try:
                cls._model = spacy.load("fr_core_news_md")
                test_similarity = cls._model("test").similarity(cls._model("test"))
                if test_similarity != 1:
                    raise ValueError("Le modèle spaCy ne fonctionne pas correctement")
            except Exception as e:
                print(f"Erreur lors du chargement du modèle spaCy : {e}")
                raise
        return cls._model


class RecommandationIA:
    def __init__(self):
        self.nlp = SpacyModelSingleton.get_model()

    def preprocess_text(self, text):
        if not text:
            return ""
        doc = self.nlp(text.lower())
        return " ".join([token.lemma_ for token in doc if not token.is_stop and not token.is_punct])

    def calculer_score_spacy(self, texte_offre, texte_etudiant):
        if not texte_offre.strip() or not texte_etudiant.strip():
            return 0.0

        texte_offre = self.preprocess_text(texte_offre)
        texte_etudiant = self.preprocess_text(texte_etudiant)

        if not texte_offre or not texte_etudiant:
            return 0.0

        try:
            return round(self.nlp(texte_offre).similarity(self.nlp(texte_etudiant)), 3)
        except Exception as e:
            print(f"Erreur dans le calcul de similarité : {e}")
            return 0.0

    def extraire_texte_pdf(self, fichier_pdf):
        if not fichier_pdf or not hasattr(fichier_pdf, 'path'):
            return ""
        try:
            with fitz.open(fichier_pdf.path) as doc:
                return " ".join([page.get_text() for page in doc])
        except Exception as e:
            print(f"Erreur extraction PDF {getattr(fichier_pdf, 'name', 'PDF inconnu')}: {e}")
            return ""

    def recommander_candidats(self, offre_id, limite=5, force_recompute=False):
        cache_key = f"reco_candidats_{offre_id}"

        if not force_recompute:
            try:
                cached_result = cache.get(cache_key)
                if cached_result is not None:
                    return cached_result[:limite]
            except Exception as e:
                print(f"Erreur cache: {e}")

        try:
            offre = OffreDeStage.objects.get(id=offre_id)
            if not offre.est_valide:
                return []
        except OffreDeStage.DoesNotExist:
            return []

        texte_offre = " ".join(filter(None, [
            offre.titre,
            offre.description,
            getattr(offre.domaine, 'nom', str(offre.domaine)),
            offre.competences_requises
        ])).strip()

        candidatures_existantes = Candidature.objects.filter(offre=offre).values_list('etudiant_id', flat=True)
        etudiants = Etudiant.objects.filter(est_valide=True).exclude(id__in=candidatures_existantes)

        resultats = []
        for etudiant in etudiants:
            texte_etudiant = " ".join(filter(None, [
                etudiant.competences,
                str(etudiant.domaine_etude),
                etudiant.realisations,
                self.extraire_texte_pdf(etudiant.cv)
            ])).strip()

            score = self.calculer_score_spacy(texte_offre, texte_etudiant)

            if score >= 0.1:
                resultats.append({
                    'etudiant': etudiant,
                    'score': round(score * 100, 1),
                    'feedback': self.generer_feedback(score),
                    'details': {
                        'competences': etudiant.competences,
                        'domaine': str(etudiant.domaine_etude)
                    }
                })

        resultats_tries = sorted(resultats, key=lambda x: x['score'], reverse=True)
        try:
            cache.set(cache_key, resultats_tries, timeout=getattr(settings, 'RECOMMENDATION_CACHE_TIMEOUT', 86400))
        except Exception as e:
            print(f"Erreur mise en cache: {e}")

        return resultats_tries[:limite]

    def recommander_offres(self, etudiant_id, limite=5, force_recompute=False, debug=False):
        cache_key = f"reco_offres_{etudiant_id}_v2"

        if not force_recompute:
            try:
                cached_result = cache.get(cache_key)
                if cached_result is not None:
                    if debug:
                        print("Utilisation du cache existant")
                    return cached_result[:limite]
            except Exception as e:
                if debug:
                    print(f"Erreur cache: {e}")

        try:
            etudiant = Etudiant.objects.get(id=etudiant_id)
            if not etudiant.est_valide:
                return []
        except Etudiant.DoesNotExist:
            return []

        if debug:
            print(f"\n=== DEBUG ÉTUDIANT {etudiant_id} ===")
            print(f"Domaine: {etudiant.domaine_etude}")
            print(f"Compétences: {etudiant.competences[:200]}...")
            print(f"Réalisations: {etudiant.realisations[:200]}...\n")

        texte_etudiant = " ".join(filter(None, [
            etudiant.competences,
            str(etudiant.domaine_etude),
            etudiant.realisations,
            self.extraire_texte_pdf(etudiant.cv)
        ])).strip()

        candidatures_existantes = Candidature.objects.filter(etudiant=etudiant).values_list('offre_id', flat=True)
        offres = OffreDeStage.objects.filter(est_valide=True).exclude(id__in=candidatures_existantes)

        resultats = []
        for offre in offres:
            texte_offre = " ".join(filter(None, [
                offre.titre,
                offre.description,
                str(offre.domaine),
                offre.competences_requises
            ])).strip()

            if debug and len(resultats) < 2:
                print(f"\n--- Comparaison avec Offre {offre.id} ---")
                print(f"Titre: {offre.titre}")
                print(f"Domaine: {offre.domaine}")
                print(f"Texte offre (nettoyé): {self.preprocess_text(texte_offre)[:200]}...")
                print(f"Texte étudiant (nettoyé): {self.preprocess_text(texte_etudiant)[:200]}...")

            score = self.calculer_score_spacy(texte_offre, texte_etudiant)

            if debug and len(resultats) < 2:
                print(f"Score brut: {score}")

            if score >= 0.1:
                resultats.append({
                    'offre': offre,
                    'score': round(score * 100, 1),
                    'feedback': self.generer_feedback(score),
                    'details': {
                        'domaine': str(offre.domaine),
                        'competences': offre.competences_requises
                    }
                })

        resultats_tries = sorted(resultats, key=lambda x: x['score'], reverse=True)

        if debug:
            print("\n=== RÉSULTATS FINAUX ===")
            print(f"Offres trouvées: {len(offres)}")
            print(f"Offres correspondantes: {len(resultats)}")
            if resultats_tries:
                print("Meilleure offre:")
                print(f"ID: {resultats_tries[0]['offre'].id}")
                print(f"Titre: {resultats_tries[0]['offre'].titre}")
                print(f"Score: {resultats_tries[0]['score']}%")
            else:
                print("Aucune offre ne dépasse le seuil de similarité")

        try:
            cache.set(cache_key, resultats_tries, timeout=getattr(settings, 'RECOMMENDATION_CACHE_TIMEOUT', 86400))
        except Exception as e:
            if debug:
                print(f"Erreur mise en cache: {e}")

        return resultats_tries[:limite]

    def generer_feedback(self, score):
        pourcentage = round(score * 100)
        if score > 0.75:
            return f"Correspondance exceptionnelle ({pourcentage}%) - Vos compétences correspondent parfaitement aux exigences"
        elif score > 0.5:
            return f"Bonne correspondance ({pourcentage}%) - Vous avez la plupart des compétences requises"
        elif score > 0.3:
            return f"Correspondance moyenne ({pourcentage}%) - Certaines compétences correspondent"
        elif score > 0.1:
            return f"Correspondance minimale ({pourcentage}%) - Quelques éléments correspondent"
        else:
            return "Correspondance insuffisante"

    def evaluer_candidatures(self, offre_id, force_recompute=False):
        cache_key = f"eval_candidatures_{offre_id}_v2"

        if not force_recompute:
            try:
                cached_result = cache.get(cache_key)
                if cached_result is not None:
                    return cached_result
            except Exception:
                pass

        try:
            offre = OffreDeStage.objects.get(id=offre_id)
            if not offre.est_valide:
                return 0
        except OffreDeStage.DoesNotExist:
            return 0

        texte_offre = " ".join(filter(None, [
            offre.titre,
            offre.description,
            str(offre.domaine),
            offre.competences_requises
        ])).strip()

        candidatures = Candidature.objects.filter(offre=offre, score_ia__isnull=True)
        updated = 0

        for candidature in candidatures:
            try:
                texte_etudiant = " ".join(filter(None, [
                    candidature.etudiant.competences,
                    str(candidature.etudiant.domaine_etude),
                    candidature.etudiant.realisations,
                    self.extraire_texte_pdf(candidature.cv)
                ])).strip()

                score = self.calculer_score_spacy(texte_offre, texte_etudiant)

                Candidature.objects.filter(id=candidature.id).update(
                    score_ia=round(score * 100, 1),
                    feedback_ia=self.generer_feedback(score),
                    date_evaluation_ia=timezone.now()
                )
                updated += 1
            except Exception as e:
                print(f"Erreur évaluation candidature {candidature.id}: {e}")

        try:
            cache.set(cache_key, updated, timeout=getattr(settings, 'RECOMMENDATION_CACHE_TIMEOUT', 43200))
        except Exception:
            pass

        return updated
