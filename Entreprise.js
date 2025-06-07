// Gestion des compétences dans le formulaire
document.addEventListener('DOMContentLoaded', function() {
    const skillsInput = document.getElementById('offer-skills');
    const skillsTags = document.getElementById('skills-tags');
    const offerForm = document.getElementById('offer-form');

    // Ajouter une compétence
    skillsInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && this.value.trim() !== '') {
            e.preventDefault();
            addSkill(this.value.trim());
            this.value = '';
        }
    });

    function addSkill(skill) {
        const li = document.createElement('li');
        li.innerHTML = `${skill} <i class="fas fa-times"></i>`;
        skillsTags.appendChild(li);

        // Supprimer une compétence
        li.querySelector('i').addEventListener('click', function() {
            li.remove();
        });
    }

    // Soumission du formulaire
    offerForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Récupérer les données du formulaire
        const formData = {
            title: document.getElementById('offer-title').value,
            type: document.getElementById('offer-type').value,
            duration: document.getElementById('offer-duration').value,
            description: document.getElementById('offer-description').value,
            skills: Array.from(skillsTags.children).map(li => li.textContent.trim())
        };

        // Envoyer les données au serveur (simulation)
        console.log('Offre soumise:', formData);
        alert('Offre publiée avec succès!');
        
        // Réinitialiser le formulaire
        this.reset();
        skillsTags.innerHTML = '';
        
        // Mettre à jour le compteur d'offres
        updateCounter('active-offers', 1);
    });

    // Charger les candidatures récentes
    loadRecentApplications();

    // Simulation de données
    function loadRecentApplications() {
        const applications = [
            { name: "Aïcha Diop", position: "Développeuse Fullstack", date: "10 min", status: "new" },
            { name: "", position: "Data Scientist", date: "25 min", status: "review" },
            { name: "Marie Fall", position: "Ingénieur DevOps", date: "1h", status: "new" }
        ];

        const container = document.getElementById('recent-applications');
        container.innerHTML = '';

        applications.forEach(app => {
            const item = document.createElement('div');
            item.className = 'application-item';
            item.innerHTML = `
                <div class="application-avatar">${app.name.charAt(0)}</div>
                <div class="application-info">
                    <h4>${app.name}</h4>
                    <p>${app.position} • ${app.date}</p>
                </div>
                <span class="application-status status-${app.status}">
                    ${app.status === 'new' ? 'Nouveau' : 'En revue'}
                </span>
            `;
            container.appendChild(item);
        });
    }

    // Mettre à jour un compteur
    function updateCounter(id, increment) {
        const element = document.getElementById(id);
        let value = parseInt(element.textContent) || 0;
        element.textContent = value + increment;
    }
});

// Gestion du menu déroulant utilisateur
document.querySelector('.user-btn').addEventListener('click', function() {
    document.querySelector('.dropdown-content').classList.toggle('show');
});

// Fermer le menu déroulant si on clique ailleurs
window.addEventListener('click', function(e) {
    if (!e.target.matches('.user-btn')) {
        const dropdowns = document.querySelectorAll('.dropdown-content');
        dropdowns.forEach(dropdown => {
            if (dropdown.classList.contains('show')) {
                dropdown.classList.remove('show');
            }
        });
    }
});