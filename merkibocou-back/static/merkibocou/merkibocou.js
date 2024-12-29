(() => {
    /**
     * Singleton pour gérer l'ID utilisateur partagé
     */
    const UserIDManager = (() => {
        let userId = null;

        return {
            getUserId: () => {
                if (!userId) {
                    userId = `user-${Math.random().toString(36).substr(2, 9)}`;
                }
                return userId;
            },
            setUserId: (id) => {
                userId = id;
            },
        };
    })();

    /**
     * Classe pour le bouton "Message"
     */
    class ThankYouMessageButton {
        constructor({
            selector,
            apiUrl = "/send-message",
            projectName = "default-project",
            devId = 0,
            placeholder = "Écrivez votre message...",
            styles = {},
        } = {}) {
            if (!selector) {
                throw new Error(
                    "Merci de spécifier un sélecteur pour attacher le bouton message."
                );
            }

            this.selector = selector;
            this.apiUrl = apiUrl;
            this.projectName = projectName;
            this.devId = devId;
            this.placeholder = placeholder;
            this.styles = styles;

            this.attachToElement();
        }

        attachToElement() {
            const parentElement = document.querySelector(this.selector);
            if (!parentElement) {
                throw new Error(
                    `Élément avec le sélecteur "${this.selector}" introuvable.`
                );
            }

            this.createMessageButton(parentElement);
            this.addStyles();
        }

        createMessageButton(parentElement) {
            this.button = document.createElement("button");
            this.button.textContent = "Message";
            this.button.setAttribute("class", "thank-you-message-button");
            parentElement.appendChild(this.button);

            this.textArea = document.createElement("textarea");
            this.textArea.setAttribute("class", "thank-you-message-textarea");
            this.textArea.setAttribute("placeholder", this.placeholder);
            this.textArea.style.display = "none"; // Caché par défaut
            parentElement.appendChild(this.textArea);

            this.sendButton = document.createElement("button");
            this.sendButton.textContent = "Envoyer";
            this.sendButton.setAttribute(
                "class",
                "thank-you-message-send-button"
            );
            this.sendButton.style.display = "none"; // Caché par défaut
            parentElement.appendChild(this.sendButton);

            this.attachEvent();
        }

        addStyles() {
            const defaultStyles = `
            .thank-you-message-button {
                background: #007bff;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 15px;
                cursor: pointer;
                font-size: 16px;
                transition: background-color 0.3s ease, transform 0.2s ease;
                box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
            }

            .thank-you-message-button:hover {
                background-color: #0056b3;
                box-shadow: 0px 6px 8px rgba(0, 0, 0, 0.2);
                transform: translateY(-2px);
            }

            .thank-you-message-button:active {
                background-color: #003f7f;
                transform: scale(0.95);
            }

            .thank-you-message-textarea {
                margin-top: 10px;
                width: 100%;
                height: 80px;
                font-size: 14px;
                padding: 10px;
                border-radius: 5px;
                border: 1px solid #ccc;
                transition: border-color 0.3s ease;
            }

            .thank-you-message-textarea:focus {
                border-color: #007bff;
                box-shadow: 0 0 4px rgba(0, 123, 255, 0.5);
                outline: none;
            }

            .thank-you-message-send-button {
                background: #28a745;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 15px;
                cursor: pointer;
                font-size: 16px;
                margin-top: 10px;
                transition: background-color 0.3s ease, transform 0.2s ease;
            box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
            }

            .thank-you-message-send-button:hover {
                background-color: #218838;
                box-shadow: 0px 6px 8px rgba(0, 0, 0, 0.2);
                transform: translateY(-2px);
            }

            .thank-you-message-send-button:active {
                background-color: #1e7e34;
                transform: scale(0.95);
            }
        `;

            const style = document.createElement("style");
            style.textContent = `${defaultStyles} ${this.styles}`;
            document.head.appendChild(style);
        }

        attachEvent() {
            // Bascule entre afficher et cacher les champs texte et bouton d'envoi
            this.button.addEventListener("click", () => {
                const isVisible = this.textArea.style.display === "block";
                this.textArea.style.display = isVisible ? "none" : "block";
                this.sendButton.style.display = isVisible ? "none" : "block";
            });
        
            // Envoie le message via une requête POST
            this.sendButton.addEventListener("click", () => {
                const message = this.textArea.value.trim();
                if (!message) {
                    alert("Veuillez écrire un message avant d'envoyer.");
                    return;
                }
        
                const payload = {
                    userId: UserIDManager.getUserId(),
                    projectName: this.projectName,
                    devId: this.devId,
                    message: message,
                };
        
                fetch(this.apiUrl, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload),
                })
                    .then((response) => response.json())
                    .then((data) => {
        
                        // Confirmation visuelle
                        this.showConfirmation("Message envoyé avec succès !");
        
                        // Réinitialise le champ texte et masque les éléments
                        this.textArea.value = "";
                        this.textArea.style.display = "none";
                        this.sendButton.style.display = "none";
                    })
                    .catch((error) => {                                
                        this.showConfirmation("Erreur dans l’envoi du message !");
        
                        // Réinitialise le champ texte et masque les éléments
                        this.textArea.value = "";
                        this.textArea.style.display = "none";
                        this.sendButton.style.display = "none";
                        console.error("Erreur lors de l'envoi du message :", error)
                    }
                    );
            }
        );
        }
        
        showConfirmation(message) {
            const confirmation = document.createElement("div");
            confirmation.textContent = message;
            confirmation.setAttribute("class", "thank-you-confirmation");
            this.textArea.parentElement.appendChild(confirmation);
        
            // Supprime la confirmation après 2 secondes
            setTimeout(() => {
                if (confirmation.parentElement) {
                    confirmation.parentElement.removeChild(confirmation);
                }
            }, 2000);
        }
    }

    class ThankYouButton {
        constructor({
            selector,
            emoji = "👍",
            label = "Dire merci",
            apiUrl = "/thank-you",
            projectName = "default-project",
            devId = 0,
            inactivityDelay = 1000,
            styles = {},
            messages = ["Mais de rien !", "Avec plaisir !", "Pas de souci !", "Tu régales !"],
        } = {}) {
            if (!selector) {
                throw new Error(
                    "Merci de spécifier un sélecteur pour attacher le bouton Thank You."
                );
            }
    
            this.selector = selector;
            this.emoji = emoji;
            this.label = label;
            this.apiUrl = apiUrl;
            this.projectName = projectName;
            this.devId = devId;
            this.inactivityDelay = inactivityDelay;
            this.styles = styles;
            this.messages = messages;
            this.hasDisplayedMessage = false; // Indique si un message a déjà été affiché
            this.clickCount = 0;
            this.inactivityTimeout = null;
    
            this.attachToElement();
        }
    
        attachToElement() {
            const parentElement = document.querySelector(this.selector);
            if (!parentElement) {
                throw new Error(
                    `Élément avec le sélecteur "${this.selector}" introuvable.`
                );
            }
    
            this.createButton(parentElement);
            this.addStyles();
        }
    
        createButton(parentElement) {
            // Conteneur principal
            this.container = document.createElement("div");
            this.container.setAttribute("class", "thank-you-container");
    
            // Bouton interactif combinant emoji et texte
            this.button = document.createElement("button");
            this.button.setAttribute("class", "thank-you-button");
            this.button.innerHTML = `
                <div class="thank-you-content">
                    <div class="thank-you-emoji">${this.emoji}</div>
                    <div class="thank-you-label">${this.label}</div>
                </div>
            `;
    
            // Ajout du bouton au conteneur
            this.container.appendChild(this.button);
            parentElement.appendChild(this.container);
    
            this.attachEvent();
        }
    
        addStyles() {
            const defaultStyles = `

/* Bouton principal */
.thank-you-button {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    background: #ffdd57;
    color: #333;
    border: none;
    border-radius: 50px;
    width: 200px; /* Largeur fixe */
    height: 50px; /* Hauteur fixe */
    font-size: 16px;
    cursor: pointer;
    font-family: Arial, sans-serif;
    gap: 8px;
    transition: background-color 0.3s ease, transform 0.2s ease;
    box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
    position: relative; /* Nécessaire pour positionner les "+1" */
    text-overflow: ellipsis; /* Gestion de texte trop long */
    overflow: hidden;
    white-space: nowrap;
}

.thank-you-button:hover {
    background-color: #ffcc33;
    box-shadow: 0px 6px 8px rgba(0, 0, 0, 0.2);
    transform: translateY(-2px);
}

.thank-you-button:active {
    background-color: #ffb400;
    transform: scale(0.95);
}

/* Contenu du bouton */
.thank-you-content {
    display: flex;
    align-items: center;
    gap: 8px;
}

.thank-you-emoji {
    font-size: 20px;
}

.thank-you-label {
    font-size: 16px;
}

/* Animation "+1" */
.thank-you-float {
    font-size: 16px;
    color: red;
    position: absolute;
    animation: floatUp 1s ease-out forwards;
    pointer-events: none;
    transform-origin: center;
    top: -10px; /* Position relative au bouton */
    left: 50%;
    transform: translateX(-50%);
}

/* Keyframes pour l'animation "+1" */
@keyframes floatUp {
    0% {
        opacity: 1;
        transform: translateY(0);
    }
    100% {
        opacity: 0;
        transform: translateY(-50px);
    }
}
            `;
    
            const style = document.createElement("style");
            style.textContent = `${defaultStyles} ${this.styles}`;
            document.head.appendChild(style);
        }
    
        attachEvent() {
            this.button.addEventListener("click", () => {
                this.clickCount++;
                this.showFloatingPlusOne();
                this.updateButtonContent();
    
                clearTimeout(this.inactivityTimeout);
                this.inactivityTimeout = setTimeout(
                    () => this.sendThankYou(),
                    this.inactivityDelay
                );
            });
        }
    
        updateButtonContent() {
            let message;
    
            // Premier clic : affichage systématique
            if (!this.hasDisplayedMessage) {
                message = this.messages[0];
                this.hasDisplayedMessage = true;
            } else {
                // Clics suivants : affichage probabiliste (50% de chance)
                if (Math.random() < 0.5) {
                    const randomIndex = Math.floor(
                        Math.random() * this.messages.length
                    );
                    message = this.messages[randomIndex];
                } else {
                    return; // On fait rien
                }
            }
    
            // Mise à jour du contenu du bouton
            const labelElement = this.button.querySelector(".thank-you-label");
            if (labelElement) {
                labelElement.textContent = message;
            }
        }
    
        showFloatingPlusOne() {
            const float = document.createElement("div");
            float.classList.add("thank-you-float");
            float.textContent = "+1";
        
            // Calcul des dimensions et position relative au bouton
            const rect = this.button.getBoundingClientRect();
            float.style.position = "absolute";
            float.style.left = `${rect.left + rect.width / 2 - 10}px`;
            float.style.top = `${rect.top - 10}px`;
        
            document.body.appendChild(float);
        
            // Retirer après animation
            float.addEventListener("animationend", () => {
                if (float.parentNode) {
                    float.parentNode.removeChild(float);
                }
            });
        }
    
        sendThankYou() {
            if (this.clickCount === 0) return;
    
            const payload = {
                userId: UserIDManager.getUserId(),
                projectName: this.projectName,
                devId: this.devId,
                clicks: this.clickCount,
            };
    
            this.clickCount = 0;
    
            fetch(this.apiUrl, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            })
                .then((response) => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    return response.json();
                })
                .then((data) => {
                    console.log("Thank You envoyé :", data);
                })
                .catch((error) => {
                    console.warn("Erreur lors de l'envoi du Thank You :", error);
                });
        }
    }
    // API exposée globalement
    window.ThankYouButton = ThankYouButton;

    // API exposée globalement
    window.ThankYouMessageButton = ThankYouMessageButton;
    window.dispatchEvent(new Event("merkitbocou-ready"));
})();
