// Toggle password visibility
document.querySelector('.toggle-pwd').addEventListener('click', function() {
    const passwordInput = document.querySelector('input[name="password"]');
    const icon = this.querySelector('i');
    
    if (passwordInput.type === 'password') {
        passwordInput.type = 'text';
        icon.classList.remove('fa-eye');
        icon.classList.add('fa-eye-slash');
    } else {
        passwordInput.type = 'password';
        icon.classList.remove('fa-eye-slash');
        icon.classList.add('fa-eye');
    }
});

// Simple animation on load
document.addEventListener('DOMContentLoaded', () => {
    const loginCard = document.querySelector('.login-card');
    loginCard.style.opacity = '0';
    loginCard.style.transform = 'translateY(20px)';
    
    setTimeout(() => {
        loginCard.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
        loginCard.style.opacity = '1';
        loginCard.style.transform = 'translateY(0)';
    }, 100);
});