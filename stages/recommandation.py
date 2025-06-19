import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import nltk
import string
from .models import OffreDeStage, Etudiant, Candidature

# Téléchargement des ressources NLTK (à faire une fois)
nltk.download('punkt')
nltk.download('stopwords')

class RecommandationIA:
    def __init__(self):
        self.stop_words = set(stopwords.words('french')) | set(stopwords.words('english'))
        self.punctuation = set(string.punctuation)
        self.vectorizer = TfidfVectorizer()

    def preprocess_text(self, text):
        if not text:
            return ""
        
        # Convertir en minuscules
        text = text.lower()
        
        # Supprimer la ponctuation
        text = ''.join([char for char in text if char not in self.punctuation])
        
        # Tokenization
        tokens = word_tokenize(text)
        
        # Supprimer les stopwords
        tokens = [word for word in tokens if word not in self.stop_words]
        
        # Lemmatization simple (pourrait être amélioré avec WordNetLemmatizer)
        lemmatized = []
        for token in tokens:
            if token.endswith('s'):
                token = token[:-1]
            lemmatized.append(token)
        
        return ' '.join(lemmatized)

    def calculer_scores(self, offre, etudiants):
        # Préparer les textes à analyser
        texts = []
        
        # Texte de l'offre
        offre_text = f"{offre.titre} {offre.description} {offre.domaine} {offre.competences_requises}"
        texts.append(self.preprocess_text(offre_text))
        
        # Textes des étudiants
        etudiant_ids = []
        for etudiant in etudiants:
            etudiant_text = f"{etudiant.competences} {etudiant.domaine_etude} {etudiant.realisations}"
            texts.append(self.preprocess_text(etudiant_text))
            etudiant_ids.append(etudiant.id)
        
        # Vectorisation TF-IDF
        tfidf_matrix = self.vectorizer.fit_transform(texts)
        
        # Calcul de similarité cosinus
        cosine_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])
        
        # Associer les scores aux étudiants
        scores = {}
        for i, etudiant_id in enumerate(etudiant_ids):
            scores[etudiant_id] = cosine_sim[0][i]
        
        return scores

    def generer_feedback(self, score, offre, etudiant):
        if score >= 0.8:
            return f"Excellente correspondance ! Le profil de {etudiant.nom_complet} correspond parfaitement aux exigences de l'offre '{offre.titre}'."
        elif score >= 0.6:
            return f"Bonne correspondance. {etudiant.nom_complet} possède la plupart des compétences requises pour l'offre '{offre.titre}'."
        elif score >= 0.4:
            return f"Correspondance moyenne. Certaines compétences de {etudiant.nom_complet} correspondent à l'offre, mais des écarts existent."
        else:
            return f"Faible correspondance. Le profil de {etudiant.nom_complet} ne correspond que partiellement aux attentes de l'offre."

    def recommander_candidats(self, offre_id, limite=5):
        offre = OffreDeStage.objects.get(id=offre_id)
        
        # Récupérer les candidatures existantes pour éviter les doublons
        candidatures_existantes = Candidature.objects.filter(offre=offre).values_list('etudiant_id', flat=True)
        
        # Trouver les étudiants qui n'ont pas encore postulé et qui correspondent au domaine
        etudiants = Etudiant.objects.filter(
            domaine_etude=offre.domaine,
            est_valide=True
        ).exclude(
            id__in=candidatures_existantes
        )
        
        if not etudiants:
            return []
        
        # Calculer les scores de correspondance
        scores = self.calculer_scores(offre, etudiants)
        
        # Trier les étudiants par score décroissant
        etudiants_tries = sorted(
            etudiants,
            key=lambda e: scores.get(e.id, 0),
            reverse=True
        )[:limite]
        
        # Préparer les résultats avec scores et feedback
        resultats = []
        for etudiant in etudiants_tries:
            score = scores.get(etudiant.id, 0)
            resultats.append({
                'etudiant': etudiant,
                'score': round(score * 100, 1),  # Pourcentage
                'feedback': self.generer_feedback(score, offre, etudiant)
            })
        
        return resultats

    def evaluer_candidatures(self, offre_id):
        offre = OffreDeStage.objects.get(id=offre_id)
        candidatures = Candidature.objects.filter(offre=offre, score_ia__isnull=True)
        
        if not candidatures:
            return 0
        
        # Préparer les textes
        texts = []
        etudiant_ids = []
        
        # Texte de l'offre
        offre_text = f"{offre.titre} {offre.description} {offre.domaine} {offre.competences_requises}"
        texts.append(self.preprocess_text(offre_text))
        
        # Textes des candidatures
        for candidature in candidatures:
            etudiant = candidature.etudiant
            etudiant_text = f"{etudiant.competences} {etudiant.domaine_etude} {etudiant.realisations}"
            texts.append(self.preprocess_text(etudiant_text))
            etudiant_ids.append(candidature.id)
        
        # Vectorisation TF-IDF
        tfidf_matrix = self.vectorizer.fit_transform(texts)
        
        # Calcul de similarité cosinus
        cosine_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])
        
        # Mettre à jour les candidatures avec les scores
        updated = 0
        for i, candidature_id in enumerate(etudiant_ids):
            score = cosine_sim[0][i]
            feedback = self.generer_feedback(score, offre, candidature.etudiant)
            
            Candidature.objects.filter(id=candidature_id).update(
                score_ia=score,
                feedback_ia=feedback
            )
            updated += 1
        
        return updated
        