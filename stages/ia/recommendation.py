import spacy
import fitz  # PyMuPDF
from django.core.cache import cache
from django.conf import settings
from stages.models import OffreDeStage, Etudiant, Candidature
from spacy.lang.fr.stop_words import STOP_WORDS

class SpacyModelSingleton:
    _model = None

    @classmethod
    def get_model(cls):
        if cls._model is None:
            try:
                cls._model = spacy.load("fr_core_news_md")
                # Vérification que le modèle fonctionne
                test_similarity = cls._model("test").similarity(cls._model("test"))
                if test_similarity != 1:
                    raise ValueError("Le modèle spaCy ne fonctionne pas correctement")
            except Exception as e:
                print(f"Erreur lors du chargement du modèle spaCy : {e}")
                raise
        return cls._model

class RecommandationIA:
    def __init__(self):
        # Charger le modèle NLP français avec vérification
        self.nlp = SpacyModelSingleton.get_model()
    
    def preprocess_text(self, text):
        """Nettoyage du texte pour améliorer la similarité"""
        if not text:
            return ""
        doc = self.nlp(text.lower())
        return " ".join([token.lemma_ for token in doc if not token.is_stop and not token.is_punct])

    def calculer_score_spacy(self, texte_offre, texte_etudiant):
        """Calcule une similarité sémantique améliorée entre deux textes"""
        if not texte_offre.strip() or not texte_etudiant.strip():
            return 0.0
        
        # Prétraitement des textes
        texte_offre = self.preprocess_text(texte_offre)
        texte_etudiant = self.preprocess_text(texte_etudiant)
        
        if not texte_offre or not texte_etudiant:
            return 0.0
            
        doc1 = self.nlp(texte_offre)
        doc2 = self.nlp(texte_etudiant)
        
        try:
            return round(doc1.similarity(doc2), 3)
        except Exception as e:
            print(f"Erreur dans le calcul de similarité : {e}")
            return 0.0

    def extraire_texte_pdf(self, fichier_pdf):
        """Extrait le texte d'un fichier PDF de manière robuste"""
        if not fichier_pdf:
            return ""
        try:
            if not hasattr(fichier_pdf, 'path'):
                return ""
                
            with fitz.open(fichier_pdf.path) as doc:
                return " ".join([page.get_text() for page in doc])
        except Exception as e:
            print(f"Erreur extraction PDF {fichier_pdf.name}: {e}")
            return ""

    def recommander_candidats(self, offre_id, limite=5, force_recompute=False):
        """Version améliorée avec meilleure gestion des erreurs"""
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

        # Construction du texte de l'offre plus complète
        texte_offre = " ".join([
            offre.titre or "",
            offre.description or "",
            offre.domaine.nom if hasattr(offre.domaine, 'nom') else str(offre.domaine) or "",
            offre.competences_requises or ""
        ]).strip()

        # Récupération des candidats éligibles
        candidatures_existantes = Candidature.objects.filter(offre=offre).values_list('etudiant_id', flat=True)
        etudiants = Etudiant.objects.filter(
            est_valide=True
        ).exclude(id__in=candidatures_existantes)
        
        resultats = []
        for etudiant in etudiants:
            texte_etudiant = " ".join([
                etudiant.competences or "",
                str(etudiant.domaine_etude) or "",
                etudiant.realisations or "",
                self.extraire_texte_pdf(etudiant.cv) or ""
            ]).strip()
            
            score = self.calculer_score_spacy(texte_offre, texte_etudiant)
            
            if score >= 0.1:  # Seuil ajustable
                resultats.append({
                    'etudiant': etudiant,
                    'score': round(score * 100, 1),
                    'feedback': self.generer_feedback(score),
                    'details': {
                        'competences': etudiant.competences,
                        'domaine': str(etudiant.domaine_etude)
                    }
                })
        
        # Tri et mise en cache
        resultats_tries = sorted(resultats, key=lambda x: x['score'], reverse=True)
        try:
            cache.set(cache_key, resultats_tries, timeout=getattr(settings, 'RECOMMENDATION_CACHE_TIMEOUT', 60*60*24))
        except Exception as e:
            print(f"Erreur mise en cache: {e}")
        
        return resultats_tries[:limite]

    def recommander_offres(self, etudiant_id, limite=5, force_recompute=False, debug=False):
        """Version finale avec debug et optimisation"""
        cache_key = f"reco_offres_{etudiant_id}_v2"  # Nouvelle version
        
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

        # Construction du profil étudiant enrichi
        texte_etudiant = " ".join([
            etudiant.competences or "",
            str(etudiant.domaine_etude) or "",
            etudiant.realisations or "",
            self.extraire_texte_pdf(etudiant.cv) or ""
        ]).strip()
        
        # Récupération des offres éligibles
        candidatures_existantes = Candidature.objects.filter(etudiant=etudiant).values_list('offre_id', flat=True)
        offres = OffreDeStage.objects.filter(
            est_valide=True
        ).exclude(id__in=candidatures_existantes)
        
        resultats = []
        for offre in offres:
            texte_offre = " ".join([
                offre.titre or "",
                offre.description or "",
                str(offre.domaine) or "",
                offre.competences_requises or ""
            ]).strip()
            
            if debug and len(resultats) < 2:  # Affiche les 2 premières comparaisons
                print(f"\n--- Comparaison avec Offre {offre.id} ---")
                print(f"Titre: {offre.titre}")
                print(f"Domaine: {offre.domaine}")
                print(f"Texte offre (nettoyé): {self.preprocess_text(texte_offre)[:200]}...")
                print(f"Texte étudiant (nettoyé): {self.preprocess_text(texte_etudiant)[:200]}...")
            
            score = self.calculer_score_spacy(texte_offre, texte_etudiant)
            
            if debug and len(resultats) < 2:
                print(f"Score brut: {score}")
            
            if score >= 0.1:  # Seuil minimal
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
            print(f"\n=== RÉSULTATS FINAUX ===")
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
            cache.set(cache_key, resultats_tries, timeout=getattr(settings, 'RECOMMENDATION_CACHE_TIMEOUT', 60*60*24))
        except Exception as e:
            if debug:
                print(f"Erreur mise en cache: {e}")
        
        return resultats_tries[:limite]

    def generer_feedback(self, score):
        """Génère un feedback détaillé"""
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
        """Évaluation robuste des candidatures"""
        cache_key = f"eval_candidatures_{offre_id}_v2"
        
        if not force_recompute:
            try:
                cached_result = cache.get(cache_key)
                if cached_result is not None:
                    return cached_result
            except:
                pass

        try:
            offre = OffreDeStage.objects.get(id=offre_id)
            if not offre.est_valide:
                return 0
        except OffreDeStage.DoesNotExist:
            return 0

        texte_offre = " ".join([
            offre.titre or "",
            offre.description or "",
            str(offre.domaine) or "",
            offre.competences_requises or ""
        ]).strip()

        candidatures = Candidature.objects.filter(offre=offre, score_ia__isnull=True)
        updated = 0

        for candidature in candidatures:
            try:
                texte_etudiant = " ".join([
                    candidature.etudiant.competences or "",
                    str(candidature.etudiant.domaine_etude) or "",
                    candidature.etudiant.realisations or "",
                    self.extraire_texte_pdf(candidature.cv) or ""
                ]).strip()

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
            cache.set(cache_key, updated, timeout=getattr(settings, 'RECOMMENDATION_CACHE_TIMEOUT', 60*60*12))
        except:
            pass

        return updated