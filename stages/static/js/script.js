document.addEventListener('DOMContentLoaded', function() {
  // Animation de chargement
  setTimeout(function() {
    document.querySelector('.loading-overlay').style.opacity = '0';
    setTimeout(function() {
      document.querySelector('.loading-overlay').style.display = 'none';
    }, 500);
  }, 1000);

  // Animations d'apparition
  const fadeElements = document.querySelectorAll('.fade-in');
  
  const fadeInObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.style.opacity = '1';
        entry.target.style.transform = 'translateY(0)';
      }
    });
  }, { threshold: 0.1 });

  fadeElements.forEach(el => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(20px)';
    el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
    fadeInObserver.observe(el);
  });

  // Gestion des cartes de candidature
  const applicationCards = document.querySelectorAll('.application-card');
  
  applicationCards.forEach(card => {
    card.addEventListener('click', function() {
      // Ajouter une fonctionnalité de clic si nécessaire
    });
  });

  // Tooltips pour les icônes
  const tooltipElements = document.querySelectorAll('[data-tooltip]');
  
  tooltipElements.forEach(el => {
    const tooltip = document.createElement('span');
    tooltip.className = 'tooltip';
    tooltip.textContent = el.getAttribute('data-tooltip');
    el.appendChild(tooltip);
    
    el.addEventListener('mouseenter', function() {
      tooltip.style.visibility = 'visible';
      tooltip.style.opacity = '1';
    });
    
    el.addEventListener('mouseleave', function() {
      tooltip.style.visibility = 'hidden';
      tooltip.style.opacity = '0';
    });
  });
});