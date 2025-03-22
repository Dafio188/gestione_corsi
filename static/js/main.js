document.addEventListener('DOMContentLoaded', function() {
    // Enable tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });

    // Enable popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'))
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl)
    });

    // Sidebar toggle for mobile
    const sidebarToggle = document.getElementById('sidebarToggle');
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function() {
            document.querySelector('.sidebar').classList.toggle('show');
        });
    }

    // File input custom text
    document.querySelectorAll('.custom-file-input').forEach(function(input) {
        input.addEventListener('change', function(e) {
            const fileName = this.files[0].name;
            const nextSibling = this.nextElementSibling;
            nextSibling.innerText = fileName;
        });
    });

    // Data tables initialization
    const dataTables = document.querySelectorAll('.data-table');
    if (dataTables.length > 0 && typeof $.fn.DataTable !== 'undefined') {
        dataTables.forEach(function(table) {
            $(table).DataTable({
                responsive: true,
                language: {
                    url: '//cdn.datatables.net/plug-ins/1.10.25/i18n/Italian.json'
                }
            });
        });
    }

    // Form validation
    const forms = document.querySelectorAll('.needs-validation');
    Array.from(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });

    // Dynamic form fields
    const addFieldButton = document.getElementById('addFieldButton');
    if (addFieldButton) {
        addFieldButton.addEventListener('click', function() {
            const container = document.getElementById('dynamicFields');
            const fieldCount = container.children.length;
            
            const newField = document.createElement('div');
            newField.className = 'input-group mb-2';
            newField.innerHTML = `
                <input type="text" class="form-control" name="fields[${fieldCount}][name]" placeholder="Nome campo">
                <input type="text" class="form-control" name="fields[${fieldCount}][value]" placeholder="Valore">
                <button class="btn btn-outline-danger remove-field" type="button">
                    <i class="bi bi-trash"></i>
                </button>
            `;
            
            container.appendChild(newField);
            
            // Add event listener to the remove button
            newField.querySelector('.remove-field').addEventListener('click', function() {
                container.removeChild(newField);
            });
        });
    }

    // Excel file preview
    const excelFileInput = document.getElementById('excelFile');
    if (excelFileInput) {
        excelFileInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    try {
                        const data = new Uint8Array(e.target.result);
                        const workbook = XLSX.read(data, {type: 'array'});
                        
                        // Get first worksheet
                        const worksheetName = workbook.SheetNames[0];
                        const worksheet = workbook.Sheets[worksheetName];
                        
                        // Convert to HTML table
                        const html = XLSX.utils.sheet_to_html(worksheet);
                        
                        // Display preview
                        document.getElementById('excelPreview').innerHTML = html;
                        document.getElementById('previewContainer').classList.remove('d-none');
                    } catch (error) {
                        console.error('Error parsing Excel file:', error);
                        alert('Errore durante la lettura del file Excel. Assicurati che il file sia valido.');
                    }
                };
                reader.readAsArrayBuffer(file);
            }
        });
    }
});

// Function to confirm deletion
function confirmDelete(itemType, itemId) {
    return new Promise((resolve, reject) => {
        if (confirm(`Sei sicuro di voler eliminare questo ${itemType}? Questa azione non può essere annullata.`)) {
            resolve(itemId);
        } else {
            reject();
        }
    });
}

// Function to handle AJAX requests
function ajaxRequest(url, method = 'GET', data = null) {
    return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        xhr.open(method, url, true);
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
        
        xhr.onload = function() {
            if (xhr.status >= 200 && xhr.status < 300) {
                try {
                    const response = JSON.parse(xhr.responseText);
                    resolve(response);
                } catch (e) {
                    resolve(xhr.responseText);
                }
            } else {
                reject({
                    status: xhr.status,
                    statusText: xhr.statusText
                });
            }
        };
        
        xhr.onerror = function() {
            reject({
                status: xhr.status,
                statusText: xhr.statusText
            });
        };
        
        if (data) {
            xhr.send(JSON.stringify(data));
        } else {
            xhr.send();
        }
    });
}