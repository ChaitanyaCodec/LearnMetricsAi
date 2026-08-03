document.addEventListener("DOMContentLoaded", () => {

    const toggle = document.getElementById("sidebarToggle");

    const sidebar = document.querySelector(".sidebar");

    if (!toggle || !sidebar) return;

    toggle.addEventListener("click", () => {

        sidebar.classList.toggle("show");

    });

});