import re
from collections import defaultdict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from .models import Etudiant, OffreDeStage

class RecommandationEngine:
    @staticmethod
    def extract_skills(text):
        """Extrait les compétences d'un texte brut"""
        if not text:
            return []
        # Expression régulière pour détecter les compétences
        skills = re.findall(r'[A-Z][a-zA-Z0-9-]+|[\w\+]+', text)
        return [skill.lower() for skill in skills if len(skill) > 2]

    @staticmethod
    def prepare_data():
        """Prépare les données pour l'analyse"""
        etudiants = Etudiant.objects.all()
        offres = OffreDeStage.objects.all()
        
        # Création des profils
        data = {
            'etudiants': [],
            'offres': []
        }
        
        for etudiant in etudiants:
            skills = RecommandationEngine.extract_skills(etudiant.competences or "")
            data['etudiants'].append({
                'id': etudiant.id,
                'skills': skills,
                'domaine': etudiant.domaine_etude,
                'niveau': etudiant.niveau_etude
            })
        
        for offre in offres:
            skills = RecommandationEngine.extract_skills(offre.competences_requises or "")
            data['offres'].append({
                'id': offre.id,
                'skills': skills,
                'domaine': offre.domaine
            })
        
        return data

    @staticmethod
    def calculate_similarity(offre_skills, etudiant_skills):
        """Calcule la similarité entre les compétences"""
        all_skills = list(set(offre_skills + etudiant_skills))
        if not all_skills:
            return 0
            
        # Création des vecteurs
        offre_vec = [1 if skill in offre_skills else 0 for skill in all_skills]
        etudiant_vec = [1 if skill in etudiant_skills else 0 for skill in all_skills]
        
        # Calcul de similarité cosinus
        return cosine_similarity([offre_vec], [etudiant_vec])[0][0]

    @staticmethod
    def recommend_for_offer(offer_id, top_n=5):
        """Génère les recommandations pour une offre"""
        data = RecommandationEngine.prepare_data()
        target_offer = next((o for o in data['offres'] if o['id'] == offer_id), None)
        
        if not target_offer:
            return []
        
        recommendations = []
        for etudiant in data['etudiants']:
            # Score basé sur les compétences
            skill_score = RecommandationEngine.calculate_similarity(
                target_offer['skills'],
                etudiant['skills']
            )
            
            # Bonus pour domaine correspondant
            domain_bonus = 0.2 if etudiant['domaine'] == target_offer['domaine'] else 0
            
            # Score final (entre 0 et 1)
            final_score = min(1, skill_score + domain_bonus)
            
            if final_score > 0.3:  # Seuil minimum
                recommendations.append({
                    'etudiant_id': etudiant['id'],
                    'score': round(final_score * 100, 1),
                    'matching_skills': list(set(target_offer['skills']) & set(etudiant['skills'])),
                    'missing_skills': list(set(target_offer['skills']) - set(etudiant['skills']))
                })
        
        # Tri par score décroissant
        return sorted(recommendations, key=lambda x: x['score'], reverse=True)[:top_n]