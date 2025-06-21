import cohere
import logging
from django.conf import settings
from cohere import CohereError
from django.core.cache import cache

# Configurez le logger
logger = logging.getLogger(__name__)

def init_cohere():
    """Initialise et retourne le client Cohere"""
    return cohere.Client(settings.COHERE_API_KEY)

def generate_job_description(entreprise, competences):
    """
    Génère une description d'offre de stage en utilisant l'API Cohere
    Args:
        entreprise: Instance du modèle Entreprise
        competences: String des compétences requises
    Returns:
        str: Description générée ou message d'erreur
    """
    try:
        co = init_cohere()
        cache_key = f"job_desc_{entreprise.id}_{hash(competences)}"
        
        # Vérifie le cache d'abord
        if cached := cache.get(cache_key):
            return cached
            
        prompt = f"""
        Génère une description professionnelle d'offre de stage pour:
        Entreprise: {entreprise.nom_entreprise}
        Secteur: {entreprise.secteur}
        Description entreprise: {entreprise.description[:200]}...
        Compétences recherchées: {competences}

        La description doit:
        - Être attractive pour les étudiants
        - Mentionner les missions principales
        - Inclure les avantages du stage
        - Faire 150-200 mots
        """
        
        response = co.generate(
            model='command',
            prompt=prompt,
            max_tokens=300,
            temperature=0.7
        )
        
        result = response.generations[0].text.strip()
        cache.set(cache_key, result, timeout=3600)  # Cache pour 1 heure
        return result
        
    except CohereError as e:
        logger.error(f"Erreur Cohere: {str(e)}")
        return "Description non disponible pour le moment."
    except Exception as e:
        logger.error(f"Erreur inattendue: {str(e)}")
        return "Erreur lors de la génération de la description."

def suggest_skills(domaine):
    """
    Suggère des compétences pour un domaine donné
    Args:
        domaine: Domaine professionnel (ex: "informatique")
    Returns:
        str: Liste de compétences ou message d'erreur
    """
    try:
        co = init_cohere()
        response = co.generate(
            model='command',
            prompt=f"Liste 10 compétences techniques importantes pour le domaine {domaine}",
            max_tokens=200
        )
        return response.generations[0].text.strip()
    except CohereError as e:
        logger.error(f"Erreur Cohere (suggest_skills): {str(e)}")
        return "Impossible de générer les suggestions de compétences."

def analyze_cv(cv_text):
    """
    Analyse un texte de CV et en extrait les compétences clés
    Args:
        cv_text: Texte du CV à analyser
    Returns:
        str: Compétences identifiées ou message d'erreur
    """
    try:
        if not cv_text or len(cv_text) < 50:
            return "Texte de CV trop court pour analyse"
            
        co = init_cohere()
        response = co.generate(
            model='command',
            prompt=f"""Extrais les compétences techniques principales de ce CV:
            
            {cv_text[:2000]}  # Limite à 2000 caractères pour éviter les tokens excessifs
            
            Retourne uniquement la liste des compétences, sans commentaires.""",
            max_tokens=150,
            temperature=0.3  # Plus précis pour l'extraction
        )
        return response.generations[0].text.strip()
    except CohereError as e:
        logger.error(f"Erreur Cohere (analyze_cv): {str(e)}")
        return "Erreur lors de l'analyse du CV."