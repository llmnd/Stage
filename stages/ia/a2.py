import spacy
from stages.models import OffreDeStage, Etudiant, Candidature

class RecommandationIA:
    def __init__(self):
        # Charger le modèle NLP français
        self.nlp = spacy.load("fr_core_news_md")
    
    def calculer_score_spacy(self, texte_offre, texte_etudiant):
        """Calcule une similarité sémantique entre deux textes (0 à 1)"""
        if not texte_offre.strip() or not texte_etudiant.strip():
            return 0.0
        doc1 = self.nlp(texte_offre)
        doc2 = self.nlp(texte_etudiant)
        return round(doc1.similarity(doc2), 3)

    def recommander_candidats(self, offre_id, limite=5):
        try:
            offre = OffreDeStage.objects.get(id=offre_id)
        except OffreDeStage.DoesNotExist:
            return []

        texte_offre = f"{offre.titre} {offre.description} {offre.domaine} {offre.competences_requises}"
        
        candidatures_existantes = Candidature.objects.filter(offre=offre).values_list('etudiant_id', flat=True)
        etudiants = Etudiant.objects.filter(domaine_etude=offre.domaine, est_valide=True).exclude(id__in=candidatures_existantes)
        
        resultats = []
        for etudiant in etudiants:
            texte_etudiant = f"{etudiant.competences} {etudiant.domaine_etude} {etudiant.realisations}"
            score = self.calculer_score_spacy(texte_offre, texte_etudiant)
            
            if score >= 0.2:
                resultats.append({
                    'etudiant': etudiant,
                    'score': round(score * 100, 1),
                    'feedback': self.generer_feedback(score)
                })
        
        return sorted(resultats, key=lambda x: x['score'], reverse=True)[:limite]

    def generer_feedback(self, score):
        """Retourne un texte de feedback basé sur le score"""
        pourcentage = round(score * 100)
        if score > 0.75:
            commentaire = "Excellente correspondance avec l'offre."
        elif score > 0.5:
            commentaire = "Bonne correspondance avec plusieurs éléments clés."
        elif score > 0.2:
            commentaire = "Correspondance partielle, améliorable avec plus d'adéquation."
        else:
            commentaire = "Correspondance faible."
        return f"Score de correspondance : {pourcentage}% - {commentaire}"

    def evaluer_candidatures(self, offre_id):
        try:
            offre = OffreDeStage.objects.get(id=offre_id)
        except OffreDeStage.DoesNotExist:
            return 0

        texte_offre = f"{offre.titre} {offre.description} {offre.domaine} {offre.competences_requises}"
        candidatures = Candidature.objects.filter(offre=offre, score_ia__isnull=True)

        updated = 0
        for candidature in candidatures:
            texte_etudiant = f"{candidature.etudiant.competences} {candidature.etudiant.domaine_etude} {candidature.etudiant.realisations}"
            score = self.calculer_score_spacy(texte_offre, texte_etudiant)

            Candidature.objects.filter(id=candidature.id).update(
                score_ia=round(score * 100, 1),
                feedback_ia=self.generer_feedback(score)
            )
            updated += 1

        return updated
