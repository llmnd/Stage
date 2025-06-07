// 🎯 Modifier profil
const editBtn = document.getElementById('edit-profile');
const saveBtn = document.getElementById('save-profile');
const nameInput = document.getElementById('name');
const bioText = document.getElementById('bio');
const bioEdit = document.getElementById('bio-edit');

editBtn.addEventListener('click', () => {
  nameInput.removeAttribute('readonly');
  bioEdit.style.display = 'block';
  bioEdit.value = bioText.innerText.trim();
  bioText.style.display = 'none';
  editBtn.style.display = 'none';
  saveBtn.style.display = 'inline-block';
});

saveBtn.addEventListener('click', () => {
  nameInput.setAttribute('readonly', true);
  bioText.innerText = bioEdit.value;
  bioText.style.display = 'block';
  bioEdit.style.display = 'none';
  saveBtn.style.display = 'none';
  editBtn.style.display = 'inline-block';
});

// 🖼️ Changer la photo de profil
const profilePicInput = document.getElementById('profile-pic');
const profileImage = document.getElementById('profile-image');

profilePicInput.addEventListener('change', (e) => {
  const file = e.target.files[0];
  if (file && file.type.startsWith('image/')) {
    const reader = new FileReader();
    reader.onload = () => {
      profileImage.src = reader.result;
    };
    reader.readAsDataURL(file);
  }
});

// 📄 Upload de CV
function uploadCV() {
  const input = document.getElementById('upload-cv');
  const fileName = document.getElementById('file-name');

  if (input.files.length === 0) {
    alert("Veuillez choisir un fichier CV.");
    return;
  }

  const file = input.files[0];
  fileName.textContent = `Fichier sélectionné : ${file.name}`;

  // Simule un envoi...
  setTimeout(() => {
    alert("CV téléversé avec succès !");
  }, 1000);
}

// 🖼️🎥 Galerie de réalisations
const mediaUpload = document.getElementById('media-upload');
const gallery = document.getElementById('gallery');

mediaUpload.addEventListener('change', () => {
  Array.from(mediaUpload.files).forEach(file => {
    const reader = new FileReader();
    reader.onload = () => {
      let element;
      if (file.type.startsWith('image/')) {
        element = document.createElement('img');
        element.src = reader.result;
        element.style.width = '160px';
        element.style.borderRadius = '10px';
      } else if (file.type.startsWith('video/')) {
        element = document.createElement('video');
        element.src = reader.result;
        element.controls = true;
        element.style.width = '200px';
        element.style.borderRadius = '10px';
      }

      if (element) {
        gallery.appendChild(element);
      }
    };
    reader.readAsDataURL(file);
  });
});

// 📬 Messagerie (fonction factice à adapter plus tard)
function ouvrirMessagerie() {
  alert("Ouverture de la messagerie… (fonctionnalité à venir)");
}

// 🏢 Entreprises (fonction factice à adapter plus tard)
function fetchEntreprises() {
  alert("Chargement des entreprises… (fonctionnalité à venir)");
}
document.addEventListener('DOMContentLoaded', () => {
  const name = localStorage.getItem('username');
  if (name) {
    document.getElementById('nom').innerText = name;
    document.getElementById('name').value = name;
  } else {
    window.location.href = 'login.html'; // Sécurité minimale
  }
});

