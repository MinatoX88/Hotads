// =========================
// ANIMACIÓN DE CARGA DE PÁGINA
// =========================

// Efecto de desvanecimiento al cargar la página
document.addEventListener("DOMContentLoaded", function() {
    document.body.style.opacity = "1";
});

// =========================
// MENÚ RESPONSIVO (MÓVILES)
// =========================

document.addEventListener("DOMContentLoaded", function() {
    let menuToggle = document.getElementById("menu-toggle");
    let navMenu = document.getElementById("nav-menu");

    if (menuToggle && navMenu) {
        menuToggle.addEventListener("click", function() {
            navMenu.classList.toggle("show");
        });
    }
});

// =========================
// VALIDACIÓN BÁSICA DE FORMULARIOS
// =========================

document.addEventListener("DOMContentLoaded", function() {
    let loginForm = document.getElementById("login-form");

    if (loginForm) {
        loginForm.addEventListener("submit", function(event) {
            let email = document.getElementById("email").value.trim();
            let password = document.getElementById("password").value.trim();
            let errorMessage = document.getElementById("error-message");

            // Validación simple
            if (email === "" || password === "") {
                event.preventDefault();
                errorMessage.textContent = "Por favor, complete todos los campos.";
                errorMessage.style.display = "block";
            }
        });
    }
});

// =========================
// EFECTOS DE HOVER EN TARJETAS DE PUBLICACIONES
// =========================

document.addEventListener("DOMContentLoaded", function() {
    let cards = document.querySelectorAll(".card");

    cards.forEach(function(card) {
        card.addEventListener("mouseenter", function() {
            this.style.transform = "scale(1.05)";
            this.style.boxShadow = "0 0 15px rgba(255, 64, 129, 0.7)";
        });

        card.addEventListener("mouseleave", function() {
            this.style.transform = "scale(1)";
            this.style.boxShadow = "0 0 10px rgba(255, 64, 129, 0.5)";
        });
    });
});

// =========================
// BOTÓN PARA VOLVER ARRIBA
// =========================

document.addEventListener("DOMContentLoaded", function() {
    let scrollTopButton = document.createElement("button");
    scrollTopButton.innerHTML = "▲";
    scrollTopButton.id = "scrollTopButton";
    document.body.appendChild(scrollTopButton);

    // Estilos del botón
    scrollTopButton.style.position = "fixed";
    scrollTopButton.style.bottom = "20px";
    scrollTopButton.style.right = "20px";
    scrollTopButton.style.backgroundColor = "#ff4081";
    scrollTopButton.style.color = "white";
    scrollTopButton.style.border = "none";
    scrollTopButton.style.padding = "10px 15px";
    scrollTopButton.style.borderRadius = "50%";
    scrollTopButton.style.cursor = "pointer";
    scrollTopButton.style.display = "none";
    scrollTopButton.style.fontSize = "20px";
    scrollTopButton.style.boxShadow = "0 0 10px rgba(255, 64, 129, 0.7)";

    // Mostrar/ocultar botón en el scroll
    window.addEventListener("scroll", function() {
        if (window.scrollY > 300) {
            scrollTopButton.style.display = "block";
        } else {
            scrollTopButton.style.display = "none";
        }
    });

    // Función para volver arriba
    scrollTopButton.addEventListener("click", function() {
        window.scrollTo({ top: 0, behavior: "smooth" });
    });
});