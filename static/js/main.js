// Main JavaScript for Rwanda Report System
document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    initNavigation();
    initReportForm();
    initStatusCheck();
    initLocationService();
    initModals();
});

// Navigation functionality
function initNavigation() {
    const navToggle = document.querySelector('.nav-toggle');
    const navMenu = document.querySelector('.nav-menu');
    
    if (navToggle) {
        navToggle.addEventListener('click', function() {
            navMenu.style.display = navMenu.style.display === 'flex' ? 'none' : 'flex';
        });
    }

    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// Report Form functionality
function initReportForm() {
    const reportForm = document.getElementById('reportForm');
    const anonymousCheckbox = document.getElementById('is_anonymous');
    const reporterInfo = document.getElementById('reporterInfo');
    const submitBtn = document.getElementById('submitBtn');
    const btnText = submitBtn.querySelector('.btn-text');
    const btnLoading = submitBtn.querySelector('.btn-loading');

    // Toggle reporter info based on anonymity
    anonymousCheckbox.addEventListener('change', function() {
        if (this.checked) {
            reporterInfo.style.display = 'none';
            // Clear reporter info fields
            document.getElementById('reporter_name').value = '';
            document.getElementById('reporter_phone').value = '';
            document.getElementById('reporter_email').value = '';
        } else {
            reporterInfo.style.display = 'block';
        }
    });

    // Form submission
    reportForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        if (!validateForm()) {
            return;
        }

        // Show loading state
        btnText.classList.add('hidden');
        btnLoading.classList.remove('hidden');
        submitBtn.disabled = true;

        try {
            const formData = new FormData(this);
            
            const response = await fetch('/api/reports/api/submit/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            const result = await response.json();

            if (result.success) {
                showSuccessModal(result.reference_code);
                reportForm.reset();
                // Reset location fields
                document.getElementById('latitude').value = '';
                document.getElementById('longitude').value = '';
                document.getElementById('locationStatus').textContent = '';
            } else {
                showError('Failed to submit report: ' + (result.error || 'Please check your input'));
            }
        } catch (error) {
            console.error('Submission error:', error);
            showError('Network error. Please check your connection and try again.');
        } finally {
            // Reset button state
            btnText.classList.remove('hidden');
            btnLoading.classList.add('hidden');
            submitBtn.disabled = false;
        }
    });

    // Form validation
    function validateForm() {
        const category = document.getElementById('category').value;
        const description = document.getElementById('description').value.trim();
        
        if (!category) {
            showError('Please select an incident type');
            return false;
        }
        
        if (!description) {
            showError('Please provide a description of the incident');
            return false;
        }
        
        if (description.length < 10) {
            showError('Please provide a more detailed description (at least 10 characters)');
            return false;
        }

        // File validation
        const fileInput = document.getElementById('media');
        if (fileInput.files.length > 0) {
            const file = fileInput.files[0];
            const maxSize = 10 * 1024 * 1024; // 10MB
            
            if (file.size > maxSize) {
                showError('File size must be less than 10MB');
                return false;
            }
            
            if (!file.type.startsWith('image/') && !file.type.startsWith('video/')) {
                showError('Please upload only images or videos');
                return false;
            }
        }

        return true;
    }
}

// Location service
function initLocationService() {
    const getLocationBtn = document.getElementById('getLocation');
    const locationStatus = document.getElementById('locationStatus');
    const latitudeInput = document.getElementById('latitude');
    const longitudeInput = document.getElementById('longitude');

    getLocationBtn.addEventListener('click', function() {
        if (!navigator.geolocation) {
            locationStatus.textContent = 'Geolocation is not supported by this browser';
            locationStatus.style.color = 'var(--danger-color)';
            return;
        }

        locationStatus.textContent = 'Getting location...';
        locationStatus.style.color = 'var(--warning-color)';
        getLocationBtn.disabled = true;

        navigator.geolocation.getCurrentPosition(
            function(position) {
                const lat = position.coords.latitude;
                const lng = position.coords.longitude;
                
                latitudeInput.value = lat.toFixed(6);
                longitudeInput.value = lng.toFixed(6);
                
                locationStatus.textContent = 'Location captured successfully!';
                locationStatus.style.color = 'var(--success-color)';
                getLocationBtn.disabled = false;
                
                // Optional: Reverse geocoding to get address
                getAddressFromCoordinates(lat, lng);
            },
            function(error) {
                let errorMessage = 'Unable to retrieve your location';
                
                switch(error.code) {
                    case error.PERMISSION_DENIED:
                        errorMessage = 'Location access denied. Please enable location permissions.';
                        break;
                    case error.POSITION_UNAVAILABLE:
                        errorMessage = 'Location information unavailable.';
                        break;
                    case error.TIMEOUT:
                        errorMessage = 'Location request timed out.';
                        break;
                }
                
                locationStatus.textContent = errorMessage;
                locationStatus.style.color = 'var(--danger-color)';
                getLocationBtn.disabled = false;
            },
            {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 60000
            }
        );
    });

    async function getAddressFromCoordinates(lat, lng) {
        try {
            // Using OpenStreetMap Nominatim for reverse geocoding
            const response = await fetch(
                `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}&zoom=18&addressdetails=1`
            );
            const data = await response.json();
            
            if (data.display_name) {
                const locationInput = document.getElementById('location');
                if (locationInput && !locationInput.value) {
                    locationInput.value = data.display_name;
                }
            }
        } catch (error) {
            console.log('Reverse geocoding failed:', error);
        }
    }
}

// Status check functionality
function initStatusCheck() {
    const checkStatusBtn = document.getElementById('checkStatus');
    const referenceInput = document.getElementById('referenceInput');
    const statusResult = document.getElementById('statusResult');

    checkStatusBtn.addEventListener('click', async function() {
        const referenceCode = referenceInput.value.trim();
        
        if (!referenceCode) {
            showError('Please enter a reference code');
            return;
        }

        // Validate reference code format
        if (!/^RRS-\d{4}-\d{5}$/.test(referenceCode)) {
            showError('Invalid reference code format. Example: RRS-2024-00123');
            return;
        }

        checkStatusBtn.disabled = true;
        checkStatusBtn.textContent = 'Checking...';

        try {
            const response = await fetch(`/api/reports/api/status/${referenceCode}/`);
            
            if (response.ok) {
                const report = await response.json();
                displayStatusResult(report);
            } else if (response.status === 404) {
                statusResult.innerHTML = `
                    <div class="error-message">
                        <h3>Report Not Found</h3>
                        <p>The reference code "${referenceCode}" was not found in our system.</p>
                        <p>Please check the code and try again.</p>
                    </div>
                `;
            } else {
                throw new Error('Server error');
            }
        } catch (error) {
            statusResult.innerHTML = `
                <div class="error-message">
                    <h3>Error Checking Status</h3>
                    <p>Unable to retrieve report status. Please try again later.</p>
                </div>
            `;
        } finally {
            checkStatusBtn.disabled = false;
            checkStatusBtn.textContent = 'Check Status';
        }
    });

    function displayStatusResult(report) {
        const statusColors = {
            'new': 'var(--primary-color)',
            'in_review': 'var(--warning-color)',
            'forwarded': 'var(--accent-color)',
            'actioned': 'var(--success-color)',
            'closed': 'var(--text-light)'
        };

        const statusText = {
            'new': 'New',
            'in_review': 'In Review',
            'forwarded': 'Forwarded',
            'actioned': 'Actioned',
            'closed': 'Closed'
        };

        const statusColor = statusColors[report.status] || statusColors.new;
        const statusDisplay = statusText[report.status] || report.status;

        statusResult.innerHTML = `
            <div class="status-report">
                <div class="status-header">
                    <h3>Report Status: ${report.reference_code}</h3>
                    <span class="status-badge" style="background: ${statusColor}">${statusDisplay}</span>
                </div>
                <div class="status-details">
                    <div class="detail-row">
                        <strong>Category:</strong>
                        <span>${getCategoryDisplay(report.category)}</span>
                    </div>
                    <div class="detail-row">
                        <strong>Submitted:</strong>
                        <span>${new Date(report.created_at).toLocaleString()}</span>
                    </div>
                    <div class="detail-row">
                        <strong>Description:</strong>
                        <p>${report.description}</p>
                    </div>
                    ${report.location_description ? `
                    <div class="detail-row">
                        <strong>Location:</strong>
                        <span>${report.location_description}</span>
                    </div>
                    ` : ''}
                    ${report.is_hash_anchored ? `
                    <div class="detail-row">
                        <strong>Blockchain:</strong>
                        <span class="blockchain-verified">✅ Evidence Secured on Blockchain</span>
                    </div>
                    ` : ''}
                </div>
            </div>
        `;
    }

    function getCategoryDisplay(category) {
        const categories = {
            'theft': 'Theft',
            'kidnapping': 'Kidnapping',
            'corruption': 'Corruption',
            'house_fire': 'House Fire',
            'road_accident': 'Road Accident',
            'other': 'Other'
        };
        return categories[category] || category;
    }
}

// Modal functionality
function initModals() {
    const successModal = document.getElementById('successModal');
    const modalClose = document.querySelector('.modal-close');
    const printReference = document.getElementById('printReference');
    const newReport = document.getElementById('newReport');

    function showModal(modal) {
        modal.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
    }

    function hideModal(modal) {
        modal.classList.add('hidden');
        document.body.style.overflow = '';
    }

    // Close modal when clicking X or outside
    if (modalClose) {
        modalClose.addEventListener('click', () => hideModal(successModal));
    }

    successModal.addEventListener('click', (e) => {
        if (e.target === successModal) {
            hideModal(successModal);
        }
    });

    // Print reference
    if (printReference) {
        printReference.addEventListener('click', function() {
            const referenceCode = document.getElementById('referenceCode').textContent;
            const printWindow = window.open('', '_blank');
            printWindow.document.write(`
                <html>
                    <head>
                        <title>Report Reference - ${referenceCode}</title>
                        <style>
                            body { font-family: Arial, sans-serif; padding: 20px; text-align: center; }
                            .reference { font-size: 24px; font-weight: bold; margin: 20px 0; }
                            .note { color: #666; margin-top: 30px; }
                        </style>
                    </head>
                    <body>
                        <h2>Rwanda Report System</h2>
                        <p>Your report has been submitted successfully.</p>
                        <div class="reference">${referenceCode}</div>
                        <p>Keep this reference code to check your report status.</p>
                        <div class="note">
                            Visit: ${window.location.origin}/#status<br>
                            Emergency Contacts: Police 112 | RIB 997
                        </div>
                    </body>
                </html>
            `);
            printWindow.document.close();
            printWindow.print();
        });
    }

    // New report button
    if (newReport) {
        newReport.addEventListener('click', function() {
            hideModal(successModal);
            // Scroll to report form
            document.getElementById('report').scrollIntoView({ behavior: 'smooth' });
        });
    }

    // Make showSuccessModal globally available
    window.showSuccessModal = function(referenceCode) {
        document.getElementById('referenceCode').textContent = referenceCode;
        showModal(successModal);
    };
}

// Utility functions
function showError(message) {
    // Simple error notification
    const errorDiv = document.createElement('div');
    errorDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: var(--danger-color);
        color: white;
        padding: 15px 20px;
        border-radius: 8px;
        box-shadow: var(--shadow-lg);
        z-index: 3000;
        max-width: 400px;
    `;
    errorDiv.textContent = message;
    
    document.body.appendChild(errorDiv);
    
    setTimeout(() => {
        errorDiv.remove();
    }, 5000);
}

// Add some sample images
console.log('Rwanda Report System Frontend Loaded Successfully!');

// Export functions for global access (if needed)
window.RRS = {
    showSuccessModal: window.showSuccessModal,
    showError: showError
};