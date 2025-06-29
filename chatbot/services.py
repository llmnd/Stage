import random
from spacy.matcher import PhraseMatcher
from spacy.tokens import Span
from .models import ChatMessage
from stages.models import OffreDeStage, Etudiant, Candidature, Entreprise
from django.contrib.auth import get_user_model
import spacy
import fitz
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
from spacy.lang.fr.stop_words import STOP_WORDS
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from collections import defaultdict
from django.db.models import Count
import numpy as np
from typing import Dict, List, Optional, Tuple
import groq
import os
from datetime import timedelta

User = get_user_model()

class GroqClient:
    _instance = None
    
    @classmethod
    def get_client(cls):
        if cls._instance is None:
            api_key = os.getenv('GROQ_API_KEY', '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')
            if not api_key:
                raise ValueError("GROQ_API_KEY environment variable not set")
            cls._instance = groq.Client(api_key=api_key)
        return cls._instance

class SpacyModelSingleton:
    _model = None

    @classmethod
    def get_model(cls):
        if cls._model is None:
            try:
                cls._model = spacy.load("fr_core_news_lg")
                test_similarity = cls._model("test").similarity(cls._model("test"))
                if test_similarity != 1:
                    raise ValueError("Le modèle spaCy ne fonctionne pas correctement")
            except Exception as e:
                print(f"Erreur lors du chargement du modèle spaCy : {e}")
                cls._model = spacy.load("fr_core_news_sm")
        return cls._model

class RecommandationIA:
    def __init__(self):
        self.nlp = SpacyModelSingleton.get_model()
        self.groq_client = GroqClient.get_client()
        self.weights = {
            'competences': 0.4,
            'domaine': 0.3,
            'localisation': 0.2,
            'niveau_etude': 0.1
        }
        self.user_preferences = defaultdict(dict)
        self._init_skill_patterns()
        self.cache_timeout = getattr(settings, 'RECOMMENDATION_CACHE_TIMEOUT', 86400)

    def _init_skill_patterns(self):
        raw_skills = [
            "python", "java", "javascript", "html", "css", "php", "c++", "c#", "swift", "kotlin",
            "ruby", "go", "rust", "scala", "r", "matlab", "machine learning", "deep learning",
            "data science", "big data", "gestion projet", "gestion temps", "travail équipe",
            "communication", "leadership", "résolution problèmes", "analyse données",
            "base de données", "sql", "mysql", "postgresql", "mongodb", "redis", "oracle",
            "docker", "kubernetes", "aws", "azure", "google cloud", "devops", "ci/cd",
            "agile", "scrum", "kanban"
        ]
        self.skill_patterns = [self.nlp.make_doc(skill) for skill in raw_skills]

    def preprocess_text(self, text: str) -> str:
        if not text:
            return ""
        
        doc = self.nlp(text.lower())
        return " ".join([
            token.lemma_ for token in doc 
            if not token.is_stop 
            and not token.is_punct
            and not token.is_space
            and len(token.text) > 2
        ])

    def get_groq_embeddings(self, text: str) -> np.ndarray:
        cache_key = f"embeddings_{hash(text)}"
        cached = cache.get(cache_key)
        
        if cached is not None:
            return np.array(cached)
        
        try:
            response = self.groq_client.embeddings.create(
                input=[text],
                model="llama3-8b-8192"
            )
            embeddings = response.data[0].embedding
            cache.set(cache_key, embeddings, timeout=self.cache_timeout)
            return np.array(embeddings)
        except Exception as e:
            print(f"Erreur lors de la génération des embeddings avec Groq: {e}")
            vectorizer = TfidfVectorizer(max_features=512)
            return vectorizer.fit_transform([text]).toarray()[0]

    def calculer_score(self, texte_offre: str, texte_etudiant: str) -> float:
        if not texte_offre.strip() or not texte_etudiant.strip():
            return 0.0

        texte_offre_clean = self.preprocess_text(texte_offre)
        texte_etudiant_clean = self.preprocess_text(texte_etudiant)

        if not texte_offre_clean or not texte_etudiant_clean:
            return 0.0

        try:
            # Similarité spaCy
            doc_offre = self.nlp(texte_offre_clean)
            doc_etudiant = self.nlp(texte_etudiant_clean)
            score_spacy = doc_offre.similarity(doc_etudiant)

            # Similarité TF-IDF
            vectorizer = TfidfVectorizer(max_features=512)
            tfidf_matrix = vectorizer.fit_transform([texte_offre_clean, texte_etudiant_clean])
            score_tfidf = cosine_similarity(tfidf_matrix[0], tfidf_matrix[1])[0][0]

            # Similarité embeddings Groq (si possible)
            try:
                emb_offre = self.get_groq_embeddings(texte_offre[:512])
                emb_etudiant = self.get_groq_embeddings(texte_etudiant[:512])
                if emb_offre.shape == emb_etudiant.shape:
                    score_groq = cosine_similarity([emb_offre], [emb_etudiant])[0][0]
                else:
                    score_groq = 0.5  # Valeur par défaut en cas de dimensions différentes
            except Exception as e:
                print(f"Erreur Groq : {e}")
                score_groq = 0.5  # Valeur par défaut si Groq échoue

            # Moyenne pondérée
            score_total = (
                0.4 * score_spacy +
                0.3 * score_tfidf +
                0.3 * score_groq
            )
            return round(score_total, 3)

        except Exception as e:
            print(f"Erreur dans le calcul de similarité : {e}")
            return 0.0

    def extraire_texte_pdf(self, fichier_pdf) -> str:
        if not fichier_pdf or not hasattr(fichier_pdf, 'path'):
            return ""
        
        cache_key = f"pdf_text_{hash(fichier_pdf.name)}"
        cached = cache.get(cache_key)
        
        if cached is not None:
            return cached
        
        try:
            with fitz.open(fichier_pdf.path) as doc:
                text = []
                for page in doc:
                    text.append(page.get_text())
                result = " ".join(text)
                cache.set(cache_key, result, timeout=self.cache_timeout)
                return result
        except Exception as e:
            print(f"Erreur extraction PDF: {e}")
            return ""

    def extraire_competences(self, texte: str) -> List[str]:
        if not texte:
            return []
        
        doc = self.nlp(texte.lower())
        competences = []
        
        matcher = PhraseMatcher(self.nlp.vocab)
        matcher.add("SKILL", self.skill_patterns)
        
        matches = matcher(doc)
        for match_id, start, end in matches:
            span = doc[start:end]
            competences.append(span.text)
        
        for ent in doc.ents:
            if ent.label_ == "SKILL":
                competences.append(ent.text)
        
        return list(set(competences))[:5]

    def generer_feedback(self, score: float) -> str:
        cache_key = f"feedback_{score}"
        cached = cache.get(cache_key)
        
        if cached is not None:
            return cached
        
        try:
            prompt = (
                f"Génère un feedback professionnel en français pour un score de {round(score * 100)}% "
                "de correspondance avec une offre de stage. Sois encourageant et donne des conseils pertinents."
            )
            
            chat_completion = self.groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama3-70b-8192",
                temperature=0.7,
                max_tokens=150
            )
            
            feedback = chat_completion.choices[0].message.content
            cache.set(cache_key, feedback, timeout=self.cache_timeout)
            return feedback
        except Exception as e:
            print(f"Erreur lors de la génération du feedback avec Groq: {e}")
            pourcentage = round(score * 100)
            if score > 0.85:
                return f"Correspondance exceptionnelle ({pourcentage}%) - Candidature fortement recommandée"
            elif score > 0.7:
                return f"Très bonne correspondance ({pourcentage}%) - Bonne chance !"
            elif score > 0.5:
                return f"Correspondance satisfaisante ({pourcentage}%) - Postulez avec une lettre de motivation adaptée"
            elif score > 0.3:
                return f"Correspondance partielle ({pourcentage}%) - À considérer si le domaine vous intéresse"
            else:
                return f"Correspondance faible ({pourcentage}%) - Peu adapté à votre profil actuel"

    def recommander_offres(self, etudiant_id: int, limite: int = 5, force_recompute: bool = False) -> List[Dict]:
        cache_key = f"reco_offres_v4_{etudiant_id}"

        if not force_recompute:
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result[:limite]

        try:
            etudiant = Etudiant.objects.get(id=etudiant_id)
            if not etudiant.est_valide:
                return []
        except Etudiant.DoesNotExist:
            return []

        texte_cv = self.extraire_texte_pdf(etudiant.cv) if etudiant.cv else ""
        
        texte_etudiant = " ".join(filter(None, [
            etudiant.competences or "",
            str(etudiant.domaine_etude),
            etudiant.realisations or "",
            texte_cv,
            getattr(etudiant, 'centre_interet', '')
        ])).strip()

        if not texte_etudiant:
            return []

        candidatures_existantes = Candidature.objects.filter(
            etudiant=etudiant
        ).values_list('offre_id', flat=True)

        offres = OffreDeStage.objects.filter(
            est_valide=True,
            date_limite__gte=timezone.now()
        ).exclude(id__in=candidatures_existantes).select_related('entreprise')

        content_based_results = []
        for offre in offres:
            texte_offre = " ".join(filter(None, [
                offre.titre,
                offre.description,
                str(offre.domaine),
                offre.competences_requises,
                getattr(offre.entreprise, 'secteur_activite', '')
            ])).strip()

            if not texte_offre:
                continue

            score = self.calculer_score(texte_offre, texte_etudiant)

            if score >= 0.1:
                content_based_results.append({
                    'offre': offre,
                    'score': round(score * 100, 1),
                    'feedback': self.generer_feedback(score),
                    'details': {
                        'domaine': str(offre.domaine),
                        'competences': self.extraire_competences(offre.competences_requises)[:5],
                        'points_forts': self.analyser_points_forts(texte_offre, texte_etudiant)
                    }
                })

        content_based_results = sorted(content_based_results, key=lambda x: x['score'], reverse=True)
        final_results = self.apply_hybrid_recommendation(etudiant_id, content_based_results)

        cache.set(cache_key, final_results, timeout=self.cache_timeout)

        return final_results[:limite]

    def apply_hybrid_recommendation(self, etudiant_id: int, content_based: List[Dict]) -> List[Dict]:
        try:
            etudiant = Etudiant.objects.get(id=etudiant_id)
            similar_users = Etudiant.objects.filter(
                domaine_etude=etudiant.domaine_etude,
                niveau_etude=etudiant.niveau_etude
            ).exclude(id=etudiant_id)
            
            popular_offers = OffreDeStage.objects.filter(
                candidature__etudiant__in=similar_users,
                est_valide=True,
                date_limite__gte=timezone.now()
            ).annotate(
                num_candidatures=Count('candidature')
            ).order_by('-num_candidatures')[:10]
            
            for offer in popular_offers:
                existing = next((item for item in content_based if item['offre'].id == offer.id), None)
                if existing:
                    existing['score'] = min(100, existing['score'] * 1.15)
                else:
                    content_based.append({
                        'offre': offer,
                        'score': 50,
                        'feedback': "Recommandé car populaire parmi les profils similaires",
                        'details': {
                            'domaine': str(offer.domaine),
                            'competences': self.extraire_competences(offer.competences_requises)[:5]
                        }
                    })
                    
            return sorted(content_based, key=lambda x: x['score'], reverse=True)
        except Exception as e:
            print(f"Erreur dans la recommandation hybride: {e}")
            return content_based

    def analyser_points_forts(self, texte_offre: str, texte_etudiant: str) -> List[str]:
        competences_offre = set(self.extraire_competences(texte_offre))
        competences_etudiant = set(self.extraire_competences(texte_etudiant))
        communs = competences_offre & competences_etudiant
        
        points_forts = []
        if len(communs) > 0:
            points_forts.append(f"{len(communs)} compétences correspondantes")
            
        doc_offre = self.nlp(texte_offre.lower())
        doc_etudiant = self.nlp(texte_etudiant.lower())
        
        if "domaine" in texte_offre.lower() and "domaine" in texte_etudiant.lower():
            domaine_offre = next((ent.text for ent in doc_offre.ents if ent.label_ == "DOMAIN"), "")
            domaine_etudiant = next((ent.text for ent in doc_etudiant.ents if ent.label_ == "DOMAIN"), "")
            
            if domaine_offre and domaine_etudiant and domaine_offre.lower() == domaine_etudiant.lower():
                points_forts.append(f"Même domaine: {domaine_offre}")
        
        return points_forts[:3] if points_forts else ["Correspondance sur les mots-clés généraux"]

    def expliquer_recommandation(self, offre_id: int, etudiant_id: int) -> str:
        cache_key = f"explication_{offre_id}_{etudiant_id}"
        cached = cache.get(cache_key)
        
        if cached is not None:
            return cached
        
        try:
            offre = OffreDeStage.objects.get(id=offre_id)
            etudiant = Etudiant.objects.get(id=etudiant_id)
            
            texte_offre = " ".join(filter(None, [
                offre.titre,
                offre.description,
                str(offre.domaine),
                offre.competences_requises
            ])).strip()
            
            texte_etudiant = " ".join(filter(None, [
                etudiant.competences,
                str(etudiant.domaine_etude),
                etudiant.realisations,
                self.extraire_texte_pdf(etudiant.cv)
            ])).strip()
            
            score = self.calculer_score(texte_offre, texte_etudiant)
            
            competences_offre = set(self.extraire_competences(texte_offre))
            competences_etudiant = set(self.extraire_competences(texte_etudiant))
            competences_communes = competences_offre & competences_etudiant
            competences_manquantes = competences_offre - competences_etudiant
            
            prompt = (
                f"Génère une explication détaillée en français pour un étudiant concernant une offre de stage.\n"
                f"Titre de l'offre: {offre.titre}\n"
                f"Entreprise: {offre.entreprise.nom_entreprise}\n"
                f"Domaine: {offre.domaine}\n"
                f"Score de correspondance: {round(score * 100)}%\n"
                f"Compétences correspondantes: {', '.join(competences_communes) if competences_communes else 'Aucune'}\n"
                f"Compétences manquantes: {', '.join(competences_manquantes) if competences_manquantes else 'Aucune'}\n\n"
                "L'explication doit être claire, encourageante et professionnelle. "
                "Inclure des conseils pour améliorer sa candidature si le score n'est pas excellent."
            )
            
            chat_completion = self.groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama3-70b-8192",
                temperature=0.6,
                max_tokens=300
            )
            
            explication = chat_completion.choices[0].message.content
            cache.set(cache_key, explication, timeout=self.cache_timeout)
            return explication
            
        except Exception as e:
            print(f"Erreur lors de la génération de l'explication avec Groq: {e}")
            return "Je n'ai pas pu générer d'explication détaillée pour le moment."

    def update_user_preferences(self, user_id: int, accepted_offers: List[int], rejected_offers: List[int]):
        try:
            etudiant = Etudiant.objects.get(user_id=user_id)
            
            for offer_id in accepted_offers:
                offer = OffreDeStage.objects.get(id=offer_id)
                competences = self.extraire_competences(offer.competences_requises)
                
                for comp in competences:
                    self.user_preferences[user_id].setdefault(comp, 0)
                    self.user_preferences[user_id][comp] += 1
            
            total = sum(self.user_preferences[user_id].values())
            if total > 0:
                for comp in self.user_preferences[user_id]:
                    self.user_preferences[user_id][comp] /= total
            
            self.weights['competences'] = 0.5 if len(self.user_preferences.get(user_id, {})) > 3 else 0.4
            
        except Exception as e:
            print(f"Erreur mise à jour préférences utilisateur: {e}")

class ChatbotService:
    def __init__(self):
        self.nlp = SpacyModelSingleton.get_model()
        self.reco_ia = RecommandationIA()
        self.groq_client = GroqClient.get_client()
        self._setup_intents()
        self.context = {}
        self.cache_timeout = getattr(settings, 'CHATBOT_CACHE_TIMEOUT', 3600)
    
    def _setup_intents(self):
        self.matcher = PhraseMatcher(self.nlp.vocab)
        
        self.greetings = ["bonjour", "salut", "hello", "coucou", "hey"]
        self.goodbyes = ["au revoir", "bye", "à plus", "ciao", "adieu"]
        self.thanks = ["merci", "merci beaucoup", "je vous remercie"]
        
        help_patterns = [self.nlp(text) for text in ["aide", "aider", "assistance", "comment faire"]]
        offers_patterns = [self.nlp(text) for text in ["offres", "stages disponibles", "propositions"]]
        candidacy_patterns = [self.nlp(text) for text in ["postuler", "candidature", "appliquer"]]
        details_patterns = [self.nlp(text) for text in ["détails", "plus d'info", "explique", "pourquoi cette offre"]]
        profile_patterns = [self.nlp(text) for text in ["mon profil", "mes compétences", "mon cv"]]
        feedback_patterns = [self.nlp(text) for text in ["feedback", "avis", "amélioration"]]
        esp_patterns = [self.nlp(text) for text in [ "qu'est-ce que l'ESP", "école supérieure polytechnique", "présente moi l'esp", "infos sur l'esp", "où se trouve l'esp"]]
        # Patterns for enterprise information
        entreprise_info_patterns = [self.nlp(text) for text in [
        "parle-moi de", "que fait", "présente", "infos sur", "information sur"]]

        
        self.matcher.add("HELP", help_patterns)
        self.matcher.add("OFFERS", offers_patterns)
        self.matcher.add("CANDIDACY", candidacy_patterns)
        self.matcher.add("DETAILS", details_patterns)
        self.matcher.add("PROFILE", profile_patterns)
        self.matcher.add("FEEDBACK", feedback_patterns)
        self.matcher.add("ESP_INFO", esp_patterns)
        self.matcher.add("ENTREPRISE_INFO", entreprise_info_patterns)
    
    def _detect_intent(self, message: str) -> Tuple[str, float]:
        doc = self.nlp(message.lower())
        matches = self.matcher(doc)
        
        last_intent = self.context.get('last_intent')
        
        if matches:
            match_id, start, end = matches[0]
            intent = self.nlp.vocab.strings[match_id]
            
            if intent == "DETAILS" and last_intent == "OFFERS":
                return "OFFER_DETAILS", 1.0
                
            return intent, 1.0
        
        if any(token.text.lower() in self.greetings for token in doc):
            return "GREETING", 0.9
        elif any(token.text.lower() in self.goodbyes for token in doc):
            return "GOODBYE", 0.9
        elif any(token.text.lower() in self.thanks for token in doc):
            return "THANKS", 0.9
        
        return "UNKNOWN", 0.0
    
    def _generate_groq_response(self, prompt: str, max_tokens: int = 1000) -> str:
        cache_key = f"groq_response_{hash(prompt)}"
        cached = cache.get(cache_key)
        
        if cached is not None:
            return cached
        
        try:
            chat_completion = self.groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama3-70b-8192",
                temperature=0.7,
                max_tokens=max_tokens
            )
            response = chat_completion.choices[0].message.content
            cache.set(cache_key, response, timeout=self.cache_timeout)
            return response
        except Exception as e:
            print(f"Erreur avec l'API Groq: {e}")
            return "Je n'ai pas pu traiter votre demande pour le moment."

    def _generate_response(self, intent: str, user, confidence: float) -> str:
        try:
            user_profile = Etudiant.objects.get(user=user)
            is_etudiant = True
        except Etudiant.DoesNotExist:
            try:
                user_profile = Entreprise.objects.get(user=user)
                is_etudiant = False
            except Entreprise.DoesNotExist:
                user_profile = None
                is_etudiant = False
        
        self.context['last_intent'] = intent
        
        if intent == "GREETING":
            return self._generate_groq_response(
                f"Génère une salutation personnalisée pour {user.first_name} en tant que chatbot d'une plateforme de stages. "
                "Sois amical et professionnel. En français."
            )
        
        elif intent == "GOODBYE":
            return self._generate_groq_response(
                f"Génère un message d'au revoir pour {user.first_name} en tant que chatbot d'une plateforme de stages. "
                "Sois courtois et encourage le retour. En français."
            )
        
        elif intent == "THANKS":
            return self._generate_groq_response(
                "Génère une réponse polie à un remerciement pour un chatbot professionnel. En français."
            )
        
        elif intent == "HELP":
            if is_etudiant:
                return self._generate_groq_response(
                    "Liste les fonctionnalités disponibles pour un étudiant sur une plateforme de stages en français. "
                    "Sois clair et concis, avec des points bullet."
                )
            else:
                return self._generate_groq_response(
                    "Liste les fonctionnalités disponibles pour une entreprise sur une plateforme de stages en français. "
                    "Sois clair et concis, avec des points bullet."
                )
        
        elif intent == "OFFERS" and is_etudiant:
            recommandations = self.reco_ia.recommander_offres(user_profile.id, limite=3)
            
            if recommandations:
                prompt = (
                    "Présente 3 offres de stage à un étudiant de manière engageante. "
                    "Pour chaque offre, mentionne le titre, l'entreprise et les compétences clés. "
                    "Ajoute une phrase pour inviter à demander plus de détails. En français.\n\n"
                    "Offres:\n"
                )
                
                for reco in recommandations:
                    prompt += (
                        f"- Titre: {reco['offre'].titre}\n"
                        f"  Entreprise: {reco['offre'].entreprise.nom_entreprise}\n"
                        f"  Compétences: {', '.join(reco['details']['competences'])}\n"
                        f"  Score: {reco['score']}%\n\n"
                    )
                
                return self._generate_groq_response(prompt)
            else:
                return self._generate_groq_response(
                    "Explique à un étudiant qu'aucune offre correspondante n'a été trouvée, "
                    "et propose des solutions alternatives. En français."
                )
        
        elif intent == "OFFER_DETAILS" and is_etudiant:
            last_offers = ChatMessage.objects.filter(
                user=user,
                intent="OFFERS"
            ).order_by('-timestamp')[:1]
            
            if last_offers:
                try:
                    recommandations = self.reco_ia.recommander_offres(user_profile.id, limite=1)
                    if recommandations:
                        return self.reco_ia.expliquer_recommandation(
                            recommandations[0]['offre'].id, 
                            user_profile.id
                        )
                except Exception:
                    pass
            
            return self._generate_groq_response(
                "Demande poliment à un étudiant de préciser à quelle offre il souhaite plus de détails. En français."
            )
        
        elif intent == "PROFILE" and is_etudiant:
            competences = user_profile.competences or "Aucune compétence renseignée"
            domaine = str(user_profile.domaine_etude) or "Non spécifié"
            realisations = user_profile.realisations or "Aucune réalisation renseignée"
            
            prompt = (
                f"Résume le profil d'un étudiant avec ces informations:\n"
                f"- Domaine: {domaine}\n"
                f"- Compétences: {competences[:200]}\n"
                f"- Réalisations: {realisations[:200]}\n\n"
                "Ajoute des conseils pour améliorer son profil et CV. En français."
            )
            
            return self._generate_groq_response(prompt)
        
        elif intent == "FEEDBACK":
            return self._generate_groq_response(
                "Demande poliment à l'utilisateur de préciser son feedback sur quelle aspect "
                "de la plateforme (recommandations, interface, fonctionnalités). En français."
            )
        
        elif intent == "ESP_INFO":
            return self._generate_groq_response(
                "Donne une présentation complète, professionnelle et à jour de l'École Supérieure Polytechnique de Dakar (ESP), en français. Mentionne son histoire, ses formations, ses missions, ses partenaires, etc."
            )
        
        elif intent == "ENTREPRISE_INFO":
            entreprise_nom = self._extract_entreprise_nom(self.context.get("last_message", ""))
            
            if not entreprise_nom:
                return self._generate_groq_response(
                    "Demande à l'utilisateur de préciser le nom de l'entreprise. En français."
                )
            
            entreprise = Entreprise.objects.filter(nom_entreprise__icontains=entreprise_nom).first()
            
            if entreprise:
                prompt = (
                    f"Présente de manière professionnelle et concise l'entreprise suivante :\n"
                    f"Nom : {entreprise.nom_entreprise}\n"
                    f"Secteur : {entreprise.secteur_activite}\n"
                    f"Localisation : {entreprise.localisation or 'Non spécifiée'}\n"
                    f"Description : {entreprise.description or 'Pas encore renseignée'}\n"
                    f"Langue : Français"
                )
                return self._generate_groq_response(prompt)
            else:
                return self._generate_groq_response(
                    f"Explique que l'entreprise '{entreprise_nom}' n'existe pas ou n'est pas encore enregistrée sur la plateforme."
                )
        
        else:
            return self._generate_groq_response(
                "Répond poliment que tu n'as pas compris la demande et propose de l'aide. En français."
            )

        
            


    def process_message(self, user, message: str) -> str:
        intent, confidence = self._detect_intent(message)
        response = self._generate_response(intent, user, confidence)
        
        ChatMessage.objects.create(
            user=user,
            message=message,
            response=response,
            is_user_message=True,
            intent=intent,
            confidence=confidence
        )
        
        ChatMessage.objects.create(
            user=user,
            message=response,
            response="",
            is_user_message=False,
            intent=None
        )
        self.context['last_message'] = message

        
        return response
    
    def _extract_entreprise_nom(self, message: str) -> Optional[str]:
        doc = self.nlp(message)
        # Recherche du nom propre
        for ent in doc.ents:
            if ent.label_ in ("ORG", "PER"):
                return ent.text.strip()
        # Plan B : dernier mot pertinent
        tokens = [t.text for t in doc if not t.is_stop and t.pos_ == "PROPN"]
        return tokens[-1] if tokens else None
