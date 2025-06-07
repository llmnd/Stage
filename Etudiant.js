// Simulation de l'ajout de compétences
document.querySelector('.add-skill button').addEventListener('click', function() {
    const input = document.querySelector('.add-skill input');
    const skill = input.value.trim();
    
    if (skill) {
        const skillTag = document.createElement('div');
        skillTag.className = 'skill-tag';
        skillTag.innerHTML = `${skill} <i class="fas fa-plus-circle"></i>`;
        
        document.querySelector('.skills-container').appendChild(skillTag);
        input.value = '';
        
        // Mise à jour du pourcentage de complétion
        const progressFill = document.querySelector('.progress-item:nth-child(2) .progress-fill');
        progressFill.style.width = '95%';
        document.querySelector('.progress-item:nth-child(2) .progress-label span:last-child').textContent = '95%';
        
        // Mise à jour du score global
        document.querySelector('.profile-score').innerHTML = '<i class="fas fa-star"></i> Profil complété à 90%';
    }
});

// Simulation de la navigation
document.querySelectorAll('.nav-links a').forEach(link => {
    link.addEventListener('click', function(e) {
        e.preventDefault();
        document.querySelectorAll('.nav-links a').forEach(a => a.classList.remove('active'));
        this.classList.add('active');
    });
});

// Simulation des actions sur les offres
document.querySelectorAll('.match-actions .btn-primary').forEach(btn => {
    btn.addEventListener('click', function () {
        const card = this.closest('.match-card');
        const title = card.querySelector('.match-title').textContent;
        alert(`Candidature envoyée pour : ${title}`);

        // Changer le texte du bouton
        this.innerHTML = '<i class="fas fa-check"></i> Postulé';
        this.classList.remove('btn-primary');
        this.classList.add('btn-outline');
        this.disabled = true;
    });
});
