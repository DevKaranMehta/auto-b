// Newsletter subscription
document.addEventListener('DOMContentLoaded', function() {
    const newsletterForm = document.getElementById('newsletter-form');
    
    if (newsletterForm) {
        newsletterForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const emailInput = this.querySelector('input[type="email"]');
            const button = this.querySelector('button');
            const email = emailInput.value;
            
            if (!email) {
                alert('Please enter your email address');
                return;
            }
            
            // Save original button text
            const originalText = button.textContent;
            
            // Show loading state
            button.textContent = 'Subscribing...';
            button.disabled = true;
            
            // Submit form
            fetch('/newsletter/subscribe', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: 'email=' + encodeURIComponent(email)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Successfully subscribed to the newsletter!');
                    emailInput.value = '';
                    button.textContent = 'Subscribed!';
                    button.style.background = '#28a745';
                    
                    // Reset button after 3 seconds
                    setTimeout(() => {
                        button.textContent = originalText;
                        button.style.background = '';
                        button.disabled = false;
                    }, 3000);
                } else {
                    alert(data.message || 'An error occurred. Please try again.');
                    button.textContent = originalText;
                    button.disabled = false;
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred. Please try again.');
                button.textContent = originalText;
                button.disabled = false;
            });
        });
    }
    
    // Admin form validation
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        // Skip newsletter form
        if (form.id === 'newsletter-form') return;
        
        form.addEventListener('submit', function(e) {
            const requiredFields = this.querySelectorAll('[required]');
            let isValid = true;
            
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    isValid = false;
                    field.style.borderColor = '#dc3545';
                    field.focus();
                } else {
                    field.style.borderColor = '';
                }
            });
            
            if (!isValid) {
                e.preventDefault();
                alert('Please fill in all required fields.');
            }
        });
    });
    
    console.log('🚀 Blockchain Latest News platform loaded successfully!');
});

// Simple content preview for admin
function previewContent(textareaId) {
    const textarea = document.getElementById(textareaId);
    if (!textarea) return;
    
    const content = textarea.value;
    const previewWindow = window.open('', '_blank', 'width=800,height=600');
    previewWindow.document.write(`
        <html>
        <head>
            <title>Content Preview</title>
            <style>
                body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; padding: 20px; line-height: 1.6; }
                h3 { color: #333; margin-top: 30px; }
                ul { padding-left: 20px; }
                p { margin-bottom: 15px; }
            </style>
        </head>
        <body>
            ${content}
        </body>
        </html>
    `);
    previewWindow.document.close();
}

// Auto-save functionality for admin forms
let autoSaveTimeout;
function autoSave(field) {
    clearTimeout(autoSaveTimeout);
    autoSaveTimeout = setTimeout(() => {
        const data = {
            field: field.name,
            value: field.value,
            timestamp: new Date().toISOString()
        };
        localStorage.setItem('blog_autosave', JSON.stringify(data));
        console.log('Auto-saved:', field.name);
    }, 2000);
}

// Load auto-saved data
function loadAutoSave() {
    const saved = localStorage.getItem('blog_autosave');
    if (saved) {
        const data = JSON.parse(saved);
        const field = document.querySelector(`[name="${data.field}"]`);
        if (field && !field.value) {
            field.value = data.value;
            console.log('Loaded auto-saved data for:', data.field);
        }
    }
}

// Initialize auto-save on admin pages
if (window.location.pathname.includes('/admin/')) {
    document.addEventListener('DOMContentLoaded', function() {
        loadAutoSave();
        
        const textFields = document.querySelectorAll('input[type="text"], textarea');
        textFields.forEach(field => {
            field.addEventListener('input', () => autoSave(field));
        });
    });
}
