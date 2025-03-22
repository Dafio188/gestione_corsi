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


// Example of AJAX request with CSRF token
function exportReportPDF() {
    fetch('/admin/report/export/pdf', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
        },
        body: JSON.stringify({
            // your data here
        })
    })
    .then(response => response.blob())
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'report.pdf';
        document.body.appendChild(a);
        a.click();
        a.remove();
    })
    .catch(error => console.error('Error:', error));
}