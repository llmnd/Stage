// interactions.js

// Récupère toutes les sections cliquables
const clickableSections = document.querySelectorAll('.clickable-section');

clickableSections.forEach(section => {
  // Clic souris : navigation
  section.addEventListener('click', () => {
    const href = section.getAttribute('data-href');
    if(href) window.location.href = href;
  });

  // Navigation au clavier (Enter ou Espace)
  section.addEventListener('keydown', (event) => {
    if(event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();  // Empêche le scroll sur espace
      const href = section.getAttribute('data-href');
      if(href) window.location.href = href;
    }
  });
});
// Création de la barre de progression au chargement
const progressBar = document.createElement('div');
progressBar.id = 'progress-bar';
document.body.prepend(progressBar);

// Fonction pour mettre à jour la barre au scroll
function updateProgressBar() {
  const scrollTop = window.scrollY || window.pageYOffset;
  const docHeight = document.documentElement.scrollHeight - window.innerHeight;
  const scrollPercent = (scrollTop / docHeight) * 100;
  progressBar.style.width = scrollPercent + '%';
}

// Événement scroll pour mettre à jour la barre
window.addEventListener('scroll', updateProgressBar);
window.addEventListener('resize', updateProgressBar);

// Initialisation au chargement
updateProgressBar();
// scroll-reveal.js

function revealOnScroll() {
  const reveals = document.querySelectorAll('.reveal');

  reveals.forEach(el => {
    const windowHeight = window.innerHeight;
    const elementTop = el.getBoundingClientRect().top;
    const revealPoint = 150; // déclenchement quand l'élément est à 150px du bas de la fenêtre

    if (elementTop < windowHeight - revealPoint) {
      el.classList.add('visible');
    } else {
      el.classList.remove('visible');
    }
  });
}

window.addEventListener('scroll', revealOnScroll);

// Trigger au chargement au cas où les éléments sont déjà visibles
window.addEventListener('load', revealOnScroll);


