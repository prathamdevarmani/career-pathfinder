// AI Career Pathfinder - Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    initializeAnimations();
    initializeFormValidation();
    initializeSkillManagement();
    initializeJobRecommendations();
    initializeResumeUpload();
    initializeTooltips();
    initializeScrollEffects();
});

// Animation Utilities
function initializeAnimations() {
    // Fade in animations for cards
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in-up');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    // Observe all cards and feature elements
    document.querySelectorAll('.card, .feature-box, .step-card').forEach(el => {
        observer.observe(el);
    });

    // Typing effect for hero text
    const heroTitle = document.querySelector('.hero-section h1');
    if (heroTitle) {
        typeWriter(heroTitle, heroTitle.textContent, 100);
    }
}

function typeWriter(element, text, speed) {
    element.textContent = '';
    let i = 0;
    function type() {
        if (i < text.length) {
            element.textContent += text.charAt(i);
            i++;
            setTimeout(type, speed);
        }
    }
    type();
}

// Form Validation
function initializeFormValidation() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!form.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
                showValidationErrors(form);
            }
            form.classList.add('was-validated');
        });

        // Real-time validation
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.addEventListener('blur', function() {
                validateField(this);
            });
        });
    });
}

function validateField(field) {
    const feedback = field.parentNode.querySelector('.invalid-feedback') || 
                    createFeedbackElement(field);
    
    if (!field.checkValidity()) {
        field.classList.add('is-invalid');
        feedback.textContent = getValidationMessage(field);
    } else {
        field.classList.remove('is-invalid');
        field.classList.add('is-valid');
    }
}

function createFeedbackElement(field) {
    const feedback = document.createElement('div');
    feedback.className = 'invalid-feedback';
    field.parentNode.appendChild(feedback);
    return feedback;
}

function getValidationMessage(field) {
    if (field.validity.valueMissing) {
        return `${field.labels[0]?.textContent || 'This field'} is required.`;
    }
    if (field.validity.typeMismatch) {
        return 'Please enter a valid value.';
    }
    if (field.validity.patternMismatch) {
        return 'Please match the requested format.';
    }
    return 'Please enter a valid value.';
}

function showValidationErrors(form) {
    const firstInvalid = form.querySelector(':invalid');
    if (firstInvalid) {
        firstInvalid.focus();
        firstInvalid.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
}

// Skill Management
function initializeSkillManagement() {
    const skillCheckboxes = document.querySelectorAll('input[name="it_skills"], input[name="non_it_skills"]');
    
    skillCheckboxes.forEach(checkbox => {
        const skillItem = checkbox.closest('.skill-item');
        const proficiencySelect = skillItem?.querySelector('select');
        
        if (proficiencySelect) {
            // Initial state
            proficiencySelect.disabled = !checkbox.checked;
            
            checkbox.addEventListener('change', function() {
                proficiencySelect.disabled = !this.checked;
                if (!this.checked) {
                    proficiencySelect.value = 'Beginner';
                }
                
                // Add visual feedback
                skillItem.classList.toggle('selected', this.checked);
                
                // Update skill counter
                updateSkillCounter();
            });
        }
    });
    
    // Initialize skill counter
    updateSkillCounter();
    
    // Skill search functionality
    const skillSearch = document.getElementById('skillSearch');
    if (skillSearch) {
        skillSearch.addEventListener('input', function() {
            filterSkills(this.value);
        });
    }
}

function updateSkillCounter() {
    const checkedSkills = document.querySelectorAll('input[name="it_skills"]:checked, input[name="non_it_skills"]:checked');
    const counter = document.getElementById('skillCounter');
    
    if (counter) {
        counter.textContent = `${checkedSkills.length} skills selected`;
    }
}

function filterSkills(searchTerm) {
    const skillItems = document.querySelectorAll('.skill-item');
    
    skillItems.forEach(item => {
        const label = item.querySelector('.form-check-label');
        const skillName = label.textContent.toLowerCase();
        const matches = skillName.includes(searchTerm.toLowerCase());
        
        item.style.display = matches ? 'block' : 'none';
    });
}

// Job Recommendations
function initializeJobRecommendations() {
    const jobCards = document.querySelectorAll('.job-card');
    
    jobCards.forEach(card => {
        // Add hover effects
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-8px)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
        
        // Save job functionality
        const saveBtn = card.querySelector('.btn-outline-secondary');
        if (saveBtn) {
            saveBtn.addEventListener('click', function(e) {
                e.preventDefault();
                toggleSaveJob(this, card);
            });
        }
    });
    
    // Filter functionality
    const filterButtons = document.querySelectorAll('.filter-btn');
    filterButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const filter = this.dataset.filter;
            filterJobs(filter);
            
            // Update active state
            filterButtons.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
        });
    });
}

function toggleSaveJob(button, card) {
    const icon = button.querySelector('i');
    const isSaved = button.classList.contains('saved');
    
    if (isSaved) {
        button.classList.remove('saved');
        icon.classList.remove('fas');
        icon.classList.add('far');
        showToast('Job removed from saved list', 'info');
    } else {
        button.classList.add('saved');
        icon.classList.remove('far');
        icon.classList.add('fas');
        showToast('Job saved successfully!', 'success');
    }
}

function filterJobs(filter) {
    const jobCards = document.querySelectorAll('.job-card');
    
    jobCards.forEach(card => {
        const shouldShow = filter === 'all' || card.dataset.category === filter;
        card.style.display = shouldShow ? 'block' : 'none';
    });
}

// Resume Upload
function initializeResumeUpload() {
    const fileInput = document.getElementById('resume');
    const uploadForm = document.getElementById('resumeForm');
    
    if (fileInput) {
        fileInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                validateResumeFile(file);
                showFilePreview(file);
            }
        });
        
        // Drag and drop functionality
        const dropZone = fileInput.closest('.input-group');
        if (dropZone) {
            setupDragAndDrop(dropZone, fileInput);
        }
    }
    
    if (uploadForm) {
        uploadForm.addEventListener('submit', function(e) {
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn && fileInput.files.length > 0) {
                showUploadProgress(submitBtn);
            }
        });
    }
}

function validateResumeFile(file) {
    const maxSize = 16 * 1024 * 1024; // 16MB
    const allowedTypes = ['application/pdf'];
    
    if (!allowedTypes.includes(file.type)) {
        showToast('Please select a PDF file only.', 'error');
        return false;
    }
    
    if (file.size > maxSize) {
        showToast('File size must be less than 16MB.', 'error');
        return false;
    }
    
    return true;
}

function showFilePreview(file) {
    const preview = document.getElementById('filePreview') || createFilePreview();
    preview.innerHTML = `
        <div class="d-flex align-items-center p-3 bg-light rounded">
            <i class="fas fa-file-pdf fa-2x text-danger me-3"></i>
            <div>
                <h6 class="mb-0">${file.name}</h6>
                <small class="text-muted">${formatFileSize(file.size)}</small>
            </div>
            <button type="button" class="btn btn-sm btn-outline-danger ms-auto" onclick="clearFilePreview()">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;
}

function createFilePreview() {
    const preview = document.createElement('div');
    preview.id = 'filePreview';
    preview.className = 'mt-3';
    
    const fileInput = document.getElementById('resume');
    fileInput.parentNode.parentNode.appendChild(preview);
    
    return preview;
}

function clearFilePreview() {
    const preview = document.getElementById('filePreview');
    const fileInput = document.getElementById('resume');
    
    if (preview) preview.remove();
    if (fileInput) fileInput.value = '';
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function setupDragAndDrop(dropZone, fileInput) {
    dropZone.addEventListener('dragover', function(e) {
        e.preventDefault();
        this.classList.add('drag-over');
    });
    
    dropZone.addEventListener('dragleave', function(e) {
        e.preventDefault();
        this.classList.remove('drag-over');
    });
    
    dropZone.addEventListener('drop', function(e) {
        e.preventDefault();
        this.classList.remove('drag-over');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            fileInput.files = files;
            fileInput.dispatchEvent(new Event('change'));
        }
    });
}

function showUploadProgress(button) {
    const originalText = button.innerHTML;
    button.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Analyzing...';
    button.disabled = true;
    
    // Simulate progress (in real app, this would be actual progress)
    let progress = 0;
    const interval = setInterval(() => {
        progress += Math.random() * 15;
        if (progress >= 100) {
            clearInterval(interval);
            progress = 100;
        }
        
        // Update progress bar if exists
        const progressBar = document.querySelector('.upload-progress');
        if (progressBar) {
            progressBar.style.width = progress + '%';
        }
    }, 200);
}

// Tooltips
function initializeTooltips() {
    // Initialize Bootstrap tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Scroll Effects
function initializeScrollEffects() {
    // Navbar scroll effect
    const navbar = document.querySelector('.navbar');
    if (navbar) {
        window.addEventListener('scroll', function() {
            if (window.scrollY > 50) {
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.remove('scrolled');
            }
        });
    }
    
    // Back to top button
    const backToTop = document.getElementById('backToTop');
    if (backToTop) {
        window.addEventListener('scroll', function() {
            if (window.scrollY > 300) {
                backToTop.style.display = 'block';
            } else {
                backToTop.style.display = 'none';
            }
        });
        
        backToTop.addEventListener('click', function() {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    }
}

// Utility Functions
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    toast.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(toast);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (toast.parentNode) {
            toast.remove();
        }
    }, 5000);
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// API Utilities
async function makeAPIRequest(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API request failed:', error);
        showToast('An error occurred. Please try again.', 'error');
        throw error;
    }
}

// Export functions for use in other scripts
window.CareerPathfinder = {
    showToast,
    makeAPIRequest,
    validateField,
    updateSkillCounter,
    toggleSaveJob,
    debounce,
    throttle
};
