import re
from collections import Counter
from stages.models import OffreDeStage, Etudiant, Candidature

class RecommandationIA:
    def __init__(self):
        # Liste de stopwords français simplifiée
        self.stop_words = set([
            'le', 'la', 'les', 'de', 'des', 'du', 'et', 'en', 'à', 'au', 'aux',
            'avec', 'dans', 'pour', 'par', 'sur', 'est', 'un', 'une', 'a', 'son',
            'se', 'qui', 'que', 'ce', 'cette', 'pas', 'plus', 'sont', 'comme',
            'the', 'and', 'of', 'to', 'in', 'is', 'it', 'that', 'with'
        ])
    
    def extraire_mots_cles(self, texte):
        """Extrait et nettoie les mots-clés d'un texte"""
        if not texte:
            return []
        
        # Nettoyage de base
        texte = texte.lower()
        texte = re.sub(r'[^\w\s]', ' ', texte)  # Supprime la ponctuation
        mots = re.findall(r'\b\w+\b', texte)
        
        # Filtrage des stopwords et mots courts
        return [mot for mot in mots 
               if mot not in self.stop_words and len(mot) > 2]
    
    def calculer_score(self, mots_cles_offre, mots_cles_etudiant):
        """Calcule un score de correspondance entre 0 et 1"""
        if not mots_cles_offre or not mots_cles_etudiant:
            return 0.0
        
        # Compter les occurrences
        compte_offre = Counter(mots_cles_offre)
        compte_etudiant = Counter(mots_cles_etudiant)
        
        # Calcul du score pondéré
        score_total = 0
        poids_total = 0
        
        for mot, count in compte_offre.items():
            if mot in compte_etudiant:
                # Pondération par la fréquence dans l'offre
                score_total += count * compte_etudiant[mot]
            poids_total += count
        
        # Normalisation entre 0 et 1
        return min(score_total / poids_total, 1.0) if poids_total > 0 else 0.0
    
    def recommander_candidats(self, offre_id, limite=5):
        """Recommande des candidats pour une offre"""
        try:
            offre = OffreDeStage.objects.get(id=offre_id)
        except OffreDeStage.DoesNotExist:
            return []
        
        # Extraire mots-clés de l'offre
        texte_offre = f"{offre.titre} {offre.description} {offre.domaine} {offre.competences_requises}"
        mots_cles_offre = self.extraire_mots_cles(texte_offre)
        
        # Récupérer étudiants éligibles (non candidatés)
        candidatures_existantes = Candidature.objects.filter(offre=offre).values_list('etudiant_id', flat=True)
        etudiants = Etudiant.objects.filter(
            domaine_etude=offre.domaine,
            est_valide=True
        ).exclude(id__in=candidatures_existantes)
        
        # Calculer les scores
        resultats = []
        for etudiant in etudiants:
            texte_etudiant = f"{etudiant.competences} {etudiant.domaine_etude} {etudiant.realisations}"
            mots_cles_etudiant = self.extraire_mots_cles(texte_etudiant)
            
            score = self.calculer_score(mots_cles_offre, mots_cles_etudiant)
            score_pourcentage = round(score * 100, 1)  # Convertir en pourcentage
            
            if score >= 0.2:  # Seuil minimal de 20%
                resultats.append({
                    'etudiant': etudiant,
                    'score': score_pourcentage,
                    'feedback': self.generer_feedback(score, mots_cles_offre, mots_cles_etudiant)
                })
        
        # Trier et retourner les meilleurs résultats
        return sorted(resultats, key=lambda x: x['score'], reverse=True)[:limite]
    
    def generer_feedback(self, score, mots_cles_offre, mots_cles_etudiant):
        """Génère un feedback textuel sur la correspondance"""
        mots_offre = set(mots_cles_offre)
        mots_etudiant = set(mots_cles_etudiant)
        
        communs = mots_offre & mots_etudiant
        manquants = mots_offre - mots_etudiant
        
        feedback = [
            f"Correspondance: {round(score * 100)}%",
            f"Mots-clés correspondants: {', '.join(communs) or 'Aucun'}",
            f"Mots-clés manquants: {', '.join(manquants) or 'Aucun'}"
        ]
        
        return "\n".join(feedback)
    
    def evaluer_candidatures(self, offre_id):
        """Évalue les candidatures non encore évaluées"""
        try:
            offre = OffreDeStage.objects.get(id=offre_id)
        except OffreDeStage.DoesNotExist:
            return 0
        
        candidatures = Candidature.objects.filter(offre=offre, score_ia__isnull=True)
        if not candidatures:
            return 0
        
        # Pré-calculer les mots-clés de l'offre
        texte_offre = f"{offre.titre} {offre.description} {offre.domaine} {offre.competences_requises}"
        mots_cles_offre = self.extraire_mots_cles(texte_offre)
        
        updated = 0
        for candidature in candidatures:
            texte_etudiant = f"{candidature.etudiant.competences} {candidature.etudiant.domaine_etude} {candidature.etudiant.realisations}"
            mots_cles_etudiant = self.extraire_mots_cles(texte_etudiant)
            
            score = self.calculer_score(mots_cles_offre, mots_cles_etudiant)
            
            Candidature.objects.filter(id=candidature.id).update(
                score_ia=round(score * 100, 1),  # Stockage en pourcentage
                feedback_ia=self.generer_feedback(score, mots_cles_offre, mots_cles_etudiant)
            )
            updated += 1
        
        return updated