// Global script for the application

// Fix for modal flickering and focus issues
document.addEventListener('DOMContentLoaded', function() {
    // Ensure all modals are properly initialized
    var deleteModals = document.querySelectorAll('.modal');
    deleteModals.forEach(function(modal) {
        modal.addEventListener('shown.bs.modal', function() {
            // Focus the delete button when modal is shown
            var deleteButton = this.querySelector('.delete-btn');
            if (deleteButton) {
                deleteButton.focus();
            }
        });
        
        // Prevent modal from closing when clicking inside the modal content
        modal.addEventListener('click', function(event) {
            if (event.target === this.querySelector('.modal-content') || 
                this.querySelector('.modal-content').contains(event.target)) {
                event.stopPropagation();
            }
        });
        
        // Fix for modal backdrop issues
        modal.addEventListener('hidden.bs.modal', function() {
            // Remove any lingering backdrop elements
            var backdrops = document.querySelectorAll('.modal-backdrop');
            backdrops.forEach(function(backdrop) {
                backdrop.remove();
            });
            // Reset body classes
            document.body.classList.remove('modal-open');
            document.body.style.paddingRight = '';
        });
    });
    
    // Initialize Bootstrap tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Auto-dismiss alerts after 5 seconds
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);

    // Form validation
    var forms = document.querySelectorAll('.needs-validation');
    Array.prototype.slice.call(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });

    // Add confirm dialog to delete buttons with class btn-delete
    var deleteButtons = document.querySelectorAll('.btn-delete');
    deleteButtons.forEach(function(button) {
        button.addEventListener('click', function(event) {
            if (!confirm('Sei sicuro di voler eliminare questo elemento?')) {
                event.preventDefault();
            }
        });
    });
});


// Funzione per esportare report in PDF tramite AJAX
function exportReportPDF(tipoReport, idElemento) {
    // Ottieni il token CSRF dal meta tag
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    
    // Crea i dati del form
    const formData = new FormData();
    formData.append('csrf_token', csrfToken);
    formData.append('tipo_report', tipoReport);
    
    // Aggiungi l'ID dell'elemento se fornito
    if (idElemento) {
        formData.append('id_elemento', idElemento);
    }
    
    // Esegui la richiesta POST
    fetch('/admin/report/export/pdf', {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken
        },
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Errore nella richiesta: ' + response.status);
        }
        return response.blob();
    })
    .then(blob => {
        // Crea un URL per il blob e scarica il file
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'report_' + tipoReport + '.pdf';
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url); // Libera la memoria
    })
    .catch(error => {
        console.error('Errore durante l\'esportazione del PDF:', error);
        alert('Si è verificato un errore durante l\'esportazione del PDF. Riprova più tardi.');
    });
}