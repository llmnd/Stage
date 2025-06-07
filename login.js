document.getElementById('login-form').addEventListener('submit', function(e) {
  e.preventDefault();

  const username = this.username.value.trim();
  const password = this.password.value.trim();

  // Exemple simple de validation — remplacer par appel API ou autre système sécurisé plus tard
  if (username === 'lamine' && password === 'passer') {
    // Redirection vers la page Étudiant après "connexion"
    window.location.href = 'index.html';
  } else {
    const errorMsg = document.getElementById('login-error');
    errorMsg.style.display = 'block';
  }
});
