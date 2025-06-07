from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Données simulées
entreprises = {
    "id": 1,
    "nom": "TechSolutions SARL",
    "secteur": "Informatique",
    "localisation": "Dakar, Sénégal",
    "description": "Entreprise spécialisée dans les solutions IT innovantes",
    "offres": [
        {
            "id": 1,
            "titre": "Développeur Fullstack",
            "type": "PFE",
            "duree": 6,
            "description": "Développement d'applications web modernes",
            "competences": ["JavaScript", "Python", "React"]
        }
    ],
    "candidatures": [
        {
            "id": 1,
            "candidat": "Aïcha Diop",
            "offre": "Développeur Fullstack",
            "date": "2023-06-15",
            "status": "en_revue"
        }
    ]
}

@app.route('/')
def index():
    return render_template('entreprise.html')

@app.route('/api/offres', methods=['GET', 'POST'])
def gestion_offres():
    if request.method == 'POST':
        data = request.json
        # Ajouter la nouvelle offre
        new_id = len(entreprises['offres']) + 1
        new_offer = {
            "id": new_id,
            "titre": data['title'],
            "type": data['type'],
            "duree": int(data['duration']),
            "description": data['description'],
            "competences": data['skills']
        }
        entreprises['offres'].append(new_offer)
        return jsonify({"success": True, "offer_id": new_id}), 201
    
    return jsonify(entreprises['offres'])

@app.route('/api/candidatures')
def get_candidatures():
    return jsonify(entreprises['candidatures'])

@app.route('/api/stats')
def get_stats():
    stats = {
        "offres_actives": len(entreprises['offres']),
        "total_candidatures": len(entreprises['candidatures']),
        "en_attente": sum(1 for c in entreprises['candidatures'] if c['status'] == 'en_attente'),
        "top_candidats": sum(1 for c in entreprises['candidatures'] if c['status'] == 'selectionne')
    }
    return jsonify(stats)

if __name__ == '__main__':
    app.run(debug=True)