document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("loginForm");
    const togglePasswordBtn = document.querySelector(".toggle-password");
    
    // Toggle Password Visibility
    if (togglePasswordBtn) {
        togglePasswordBtn.addEventListener("click", function () {
            const passwordInput = document.getElementById("password-field");
            const icon = this.querySelector("i");
            
            if (passwordInput.type === "password") {
                passwordInput.type = "text";
                icon.classList.replace("fa-eye", "fa-eye-slash");
            } else {
                passwordInput.type = "password";
                icon.classList.replace("fa-eye-slash", "fa-eye");
            }
        });
    }

    // Submit Loading State
    if (form) {
        form.addEventListener("submit", () => {
            const button = document.getElementById("submitBtn");
            if (!button) return;

            button.disabled = true;
            button.innerHTML = `
                <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                Signing In...
            `;
        });
    }
});