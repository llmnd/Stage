// Gestion des onglets
document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
        // Désactiver tous les onglets
        document.querySelectorAll('.tab').forEach(t => {
            t.classList.remove('active');
        });
        
        // Activer l'onglet cliqué
        tab.classList.add('active');
        
        // Masquer tous les contenus
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.add('hidden');
            content.classList.remove('active');
        });
        
        // Afficher le contenu cible
        const target = document.getElementById(tab.dataset.target);
        target.classList.remove('hidden');
        target.classList.add('active');
    });
});

// Animation au chargement de la page
document.addEventListener('DOMContentLoaded', () => {
    const cards = document.querySelectorAll('.stat-card, .content-card');
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
        setTimeout(() => {
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, 100 * index);
    });
});