var training_plan;

// Lorsque la page est complètement chargée
$(document).ready(function () {


    $('#subject-form').submit(function (e) {
        e.preventDefault();  // Empêcher l'action de base
        var subject = $('#subject').val();  // Récupération du sujet
        $('#loading-message-plan').show();  // Affichage message de chargement

        makeAjaxRequest('/plan', 'POST', { subject: subject }, function (data) {
            training_plan = data.training_plan  // Enregistrer le plan en mémoire
            $('#loading-message-plan').hide();  // Cacher le message de chargement
            $('#description').hide();  // Cacher description plateforme
            $('#training-plan-block').show();  // afficher le bloc du plan
            $('#training-plan-content').html(training_plan);  // mettre à jour le contenu avec le plan généré
            $('#generate-block').show();  // Afficher le bloc de génération
        });
    });


    $('#modify-btn-plan').click(function () {
        $(this).prop('disabled', true);  // Désactiver le boutton
        $('#loading-message-modify-plan').show();  // Affciher le message de chargement
        var modifications = $('#modification-request-plan').val();  // Récupérer les modifications dans le textarea

        makeAjaxRequest('/modify', 'POST', { training_plan: training_plan, modification_requests: modifications }, function (data) {
            $('#loading-message-modify-plan').hide();  // Cacher le message de chargement
            $('#training-plan-content').html(data.modified_plan);  // Mettre à jour le plan avec les modifications
            training_plan = data.modified_plan;  // Enregistrer le nouveau plan en mémoire
            $('#modification-request-plan').val('');  // Vider le textarea pour les demandes de modifications
            $('#modify-btn-plan').prop('disabled', false);  // Réactiver le boutton
        });
    });


    $('#generate-btn').click(function () {
        $(this).prop('disabled', true);  // Désactiver le boutton
        $('#loading-message-generation').show();  // Afficher le message de chargement
        $('#generate-btn').hide();  // Masquer le boutton de génération
        $('#modification-request-plan').hide();  // Masquer le textarea de modifications
        $('#modify-btn-plan').hide(); // Masquer le boutton de modifications
        $('#form-block').hide();  // Masquer le bloc du choix du sujet

        makeAjaxRequest('/generate', 'POST', {}, function (data) {
            $('#loading-message-generation').hide();  // Cacher le message de chargement
            if (data.success) {
                var allContent = data.all_content;  // Récupération noms des sections (liste)
                var sectionLinksDiv = document.getElementById('section-links');  // Division ou seront ajouté les bouttons
                var buttonHtml = '';  // Variables qui stockera les bouttons html pour chaque section

                // Création des bouttons pour chaque section
                allContent.forEach((content, index) => {
                    // Pour chaque nouvelle paire de boutton, créer une ligne
                    if (index % 2 === 0) {
                        buttonHtml += '<div class="row">';
                    }

                    const encodedContent = encodeURIComponent(content).replace(/'/g, "\\'"); // Échapper les apostrophes

                    // Création du boutton
                    buttonHtml += `
                        <button class="col" onclick="window.location.href='/verify?section=${encodedContent}'">
                            ${content}
                        </button>
                    `;

                    // Si c'est le dernier boutton ou la fin d'une paire, fermer la ligne
                    if (index % 2 === 1 || index + 1 === allContent.length) {
                        buttonHtml += '</div>';
                    }
                });

                // Ajouter les boutons à la division prévue à cet effet
                sectionLinksDiv.innerHTML = buttonHtml;

                // Afficher le boutton de validation
                document.getElementById('central-button-container').style.display = 'flex';


            }
        });
    });


    // Boutton pour revenir en arrière (consultation du contenu généré)
    $('#back-btn').click(function () {
        window.history.back();
    });


    $('#modify-btn-content').click(function () {
        $(this).prop('disabled', true);  // Désactiver le boutton
        $('#loading-message-modify-content').show();  // Affichage message de chargement
        var currentContent = $('#generated-content').html();  // Récupération du contenu existant
        var modifications = $('#modification-request-content').val();  // Récupération des modifications du contenu souhaitées
        // Récupération du nom de la section en question à l'aide de l'URL
        var urlParams = new URLSearchParams(window.location.search);
        var sectionTitle = urlParams.get('section');

        makeAjaxRequest('/modify_content', 'POST', { current_content: currentContent, modification_requests: modifications, section_title: sectionTitle }, function (data) {
            $('#loading-message-modify-content').hide();  // Hide loading message
            $('#generated-content').html(data.modified_content);  // Update the content with the modifications
            $('#modification-request-content').val('');  // Clear the modification textarea
            $('#modify-btn-content').prop('disabled', false);  // Enable the button
        });
    });


    $('#validate-btn').click(function () {
        $('#central-button-container').hide(); // Cachez le bouton pendant la requête
        $('#training-plan-block').hide();  // Masquer le bloc du plan de formation
        $('#fsection-links').hide();  // Masquer les bouttons des sections

        makeAjaxRequest('/valider', 'POST', {}, function (data) {
            if (data.success) {
                window.location.href = "/";
                $('#training-plan-block').show();  // Afficher le bloc du plan de formation
                $('#genearte-block').hide();  // Masquer le bloc du plan de formation
            } else {
                // Gérer ici les erreurs ou autres comportements si la réponse n'indique pas un succès.
                alert("Une erreur s'est produite. Veuillez réessayer.");
            }
        });
    });


});