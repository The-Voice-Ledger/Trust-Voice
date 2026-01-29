/**
 * TrustVoice Field Agent Mini App
 * Main application logic
 */

// ========================================
// Telegram Web App Integration
// ========================================

const tg = window.Telegram.WebApp;
const user = tg.initData && tg.initDataUnsafe?.user;

// Initialize Telegram Web App
if (tg) {
    tg.ready();
    tg.expand();
    tg.setHeaderColor('#1f4fb8');
    tg.setBackgroundColor('#f3f4f6');
}

// ========================================
// Global State
// ========================================

const state = {
    currentStep: 1,
    photos: [],
    location: {
        latitude: null,
        longitude: null,
        source: null // 'exif', 'gps', or 'manual'
    },
    campaign: {
        id: null,
        title: null
    },
    description: '',
    beneficiaryCount: null,
    testimonials: '',
    trustScore: 0
};

// ========================================
// API Configuration
// ========================================

const API_BASE_URL = window.location.origin.includes('localhost')
    ? 'http://localhost:8000/api'
    : 'https://web-production-dd7cf.up.railway.app/api';

const FIELD_AGENT_API = `${API_BASE_URL}/field-agent`;

// Get user info from Telegram
const getTelegramUserId = () => {
    if (user?.id) {
        return user.id.toString();
    }
    // Fallback for testing
    return localStorage.getItem('testTelegramUserId') || 'test_user_local';
};

// ========================================
// Step Navigation
// ========================================

function goToStep(stepNumber) {
    // Validate current step before moving forward
    if (stepNumber > state.currentStep) {
        if (!validateStep(state.currentStep)) {
            return;
        }
    }

    // Hide all sections
    document.querySelectorAll('.step-section').forEach(section => {
        section.classList.remove('active');
    });

    // Show target section
    const targetSection = document.querySelector(`[data-step="${stepNumber}"]`);
    if (targetSection) {
        targetSection.classList.add('active');
    }

    // Update step indicator
    document.querySelectorAll('.step').forEach(step => {
        step.classList.remove('step-active');
        if (step.dataset.step <= stepNumber) {
            step.classList.add('step-active');
        }
    });

    // Update review section if going to step 4
    if (stepNumber === 4) {
        updateReview();
    }

    // Scroll to top
    window.scrollTo(0, 0);

    state.currentStep = stepNumber;
}

// ========================================
// Step 1: Photo Upload
// ========================================

function triggerPhotoUpload() {
    const input = document.getElementById('photoInput');
    input.value = ''; // Reset input
    input.click();
}

function selectExistingPhotos() {
    const input = document.getElementById('photoInput');
    input.value = ''; // Reset input
    input.click();
}

document.getElementById('photoInput').addEventListener('change', async (e) => {
    const files = Array.from(e.target.files);

    for (const file of files) {
        if (state.photos.length >= 5) {
            showError('Maximum 5 photos allowed');
            break;
        }

        await processPhotoFile(file);
    }

    updatePhotoGrid();
});

async function processPhotoFile(file) {
    return new Promise((resolve) => {
        const reader = new FileReader();

        reader.onload = async (e) => {
            const imageData = e.target.result;

            // Try to extract EXIF GPS data
            let gpsCoords = null;
            try {
                gpsCoords = await extractExifGPS(file);
                if (gpsCoords) {
                    console.log('✅ GPS extracted from photo:', gpsCoords);
                    state.location = {
                        latitude: gpsCoords.latitude,
                        longitude: gpsCoords.longitude,
                        source: 'exif'
                    };
                }
            } catch (error) {
                console.warn('Could not extract EXIF:', error.message);
            }

            // Store photo
            const photoId = `photo_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
            state.photos.push({
                id: photoId,
                data: imageData,
                file: file,
                gpsExtracted: !!gpsCoords
            });

            resolve();
        };

        reader.readAsDataURL(file);
    });
}

function extractExifGPS(file) {
    return new Promise((resolve, reject) => {
        // Using piexifjs library for EXIF extraction
        // This would require loading piexifjs library
        // For now, we'll use a simplified approach

        const reader = new FileReader();

        reader.onload = (e) => {
            try {
                // Look for EXIF markers in JPEG
                const data = new Uint8Array(e.target.result);
                const gps = parseExifFromJpeg(data);
                resolve(gps);
            } catch (error) {
                resolve(null); // No GPS data found
            }
        };

        reader.readAsArrayBuffer(file);
    });
}

function parseExifFromJpeg(data) {
    // Simplified EXIF parser for GPS data
    // In production, use a library like piexifjs or exif-js

    // Look for EXIF marker (0xFFE1)
    for (let i = 0; i < data.length - 10; i++) {
        if (data[i] === 0xFF && data[i + 1] === 0xE1) {
            // Found EXIF marker
            // This is simplified - real implementation would parse full EXIF
            console.log('EXIF marker found');
            return null; // Placeholder
        }
    }

    return null;
}

function updatePhotoGrid() {
    const grid = document.getElementById('photoGrid');
    grid.innerHTML = '';

    state.photos.forEach((photo) => {
        const div = document.createElement('div');
        div.className = 'photo-item';
        div.innerHTML = `
            <img src="${photo.data}" alt="Photo">
            <button class="delete-btn" onclick="deletePhoto('${photo.id}')">×</button>
            ${photo.gpsExtracted ? '<div style="position: absolute; top: 4px; left: 4px; background: #10b981; color: white; padding: 2px 6px; border-radius: 2px; font-size: 10px; font-weight: 600;">📍</div>' : ''}
        `;
        grid.appendChild(div);
    });

    const count = document.getElementById('photoCount');
    count.textContent = state.photos.length;
}

function deletePhoto(photoId) {
    state.photos = state.photos.filter(p => p.id !== photoId);
    updatePhotoGrid();
}

// ========================================
// Step 2: Location
// ========================================

function getLocationFromPhone() {
    if (!navigator.geolocation) {
        showError('Geolocation not supported on this device');
        return;
    }

    const loader = document.querySelector('.location-status');
    loader.innerHTML = '<p>Getting location...</p>';

    navigator.geolocation.getCurrentPosition(
        (position) => {
            state.location = {
                latitude: position.coords.latitude,
                longitude: position.coords.longitude,
                source: 'gps'
            };
            updateLocationDisplay();
        },
        (error) => {
            console.error('Geolocation error:', error);
            showError(`Location error: ${error.message}`);
            loader.innerHTML = '<p class="text-gray">Failed to get location. Try manual entry.</p>';
        }
    );
}

function manualLocationEntry() {
    const form = document.getElementById('manualLocationForm');
    form.style.display = form.style.display === 'none' ? 'block' : 'none';
}

function saveManualLocation() {
    const lat = parseFloat(document.getElementById('latitudeInput').value);
    const lng = parseFloat(document.getElementById('longitudeInput').value);

    if (!lat || !lng || isNaN(lat) || isNaN(lng)) {
        showError('Please enter valid latitude and longitude');
        return;
    }

    if (lat < -90 || lat > 90 || lng < -180 || lng > 180) {
        showError('Latitude must be -90 to 90, Longitude must be -180 to 180');
        return;
    }

    state.location = {
        latitude: lat,
        longitude: lng,
        source: 'manual'
    };

    updateLocationDisplay();
    document.getElementById('manualLocationForm').style.display = 'none';
}

function updateLocationDisplay() {
    const display = document.getElementById('locationDisplay');

    if (state.location.latitude && state.location.longitude) {
        const source = {
            'exif': '📷 Extracted from photo',
            'gps': '📍 From your device',
            'manual': '✏️ Manually entered'
        }[state.location.source] || 'Unknown source';

        display.innerHTML = `
            <div class="location-status">
                <p style="font-weight: 600; color: #10b981; margin-bottom: 8px;">✅ Location Confirmed</p>
                <p><strong>Latitude:</strong> ${state.location.latitude.toFixed(6)}</p>
                <p><strong>Longitude:</strong> ${state.location.longitude.toFixed(6)}</p>
                <p style="font-size: 12px; color: #6b7280; margin-top: 8px;">${source}</p>
            </div>
        `;
    } else {
        display.innerHTML = '<div class="location-status"><p class="text-gray">Location not yet provided</p></div>';
    }
}

// ========================================
// Step 3: Details
// ========================================

// Load pending campaigns
async function loadPendingCampaigns() {
    try {
        const response = await fetch(`${FIELD_AGENT_API}/campaigns/pending?telegram_user_id=${getTelegramUserId()}`);
        const data = await response.json();

        const select = document.getElementById('campaignSelect');
        const campaigns = data.campaigns || [];

        campaigns.forEach(campaign => {
            const option = document.createElement('option');
            option.value = campaign.id;
            option.textContent = `${campaign.title} ($${campaign.goal_amount_usd.toLocaleString()})`;
            select.appendChild(option);
        });

        if (campaigns.length === 0) {
            const option = document.createElement('option');
            option.disabled = true;
            option.textContent = 'No pending campaigns available';
            select.appendChild(option);
        }
    } catch (error) {
        console.error('Error loading campaigns:', error);
    }
}

// Update campaign selection
document.getElementById('campaignSelect').addEventListener('change', (e) => {
    const selected = e.target.options[e.target.selectedIndex];
    state.campaign = {
        id: e.target.value,
        title: selected.textContent
    };
});

// Character counter for description
document.getElementById('description').addEventListener('input', (e) => {
    state.description = e.target.value;
    const count = e.target.value.length;
    document.getElementById('charCount').textContent = `${count}/300`;

    // Update character counter color
    const counter = document.getElementById('charCount');
    if (count < 50) {
        counter.style.color = '#ef4444';
    } else if (count < 100) {
        counter.style.color = '#f59e0b';
    } else {
        counter.style.color = '#10b981';
    }
});

document.getElementById('beneficiaryCount').addEventListener('change', (e) => {
    state.beneficiaryCount = parseInt(e.target.value) || null;
});

document.getElementById('testimonials').addEventListener('change', (e) => {
    state.testimonials = e.target.value;
});

// ========================================
// Step 4: Review & Submit
// ========================================

function updateReview() {
    // Photos
    const reviewPhotos = document.getElementById('reviewPhotos');
    reviewPhotos.innerHTML = '';
    state.photos.forEach(photo => {
        const img = document.createElement('img');
        img.src = photo.data;
        reviewPhotos.appendChild(img);
    });

    // Location
    const reviewLocation = document.getElementById('reviewLocation');
    if (state.location.latitude && state.location.longitude) {
        reviewLocation.innerHTML = `📍 ${state.location.latitude.toFixed(4)}, ${state.location.longitude.toFixed(4)}`;
        reviewLocation.classList.remove('text-gray');
    }

    // Campaign
    const reviewCampaign = document.getElementById('reviewCampaign');
    if (state.campaign.id) {
        reviewCampaign.textContent = state.campaign.title;
        reviewCampaign.classList.remove('text-gray');
    }

    // Description
    const reviewDescription = document.getElementById('reviewDescription');
    if (state.description) {
        reviewDescription.textContent = state.description;
        reviewDescription.classList.remove('text-gray');
    }

    // Beneficiaries
    const reviewBeneficiaries = document.getElementById('reviewBeneficiaries');
    if (state.beneficiaryCount) {
        reviewBeneficiaries.textContent = `${state.beneficiaryCount} people`;
        reviewBeneficiaries.classList.remove('text-gray');
    }
    if (state.testimonials) {
        reviewBeneficiaries.innerHTML += `<p style="margin-top: 8px; font-style: italic;">"${state.testimonials}"</p>`;
    }

    // Trust score preview
    updateTrustScorePreview();
}

function updateTrustScorePreview() {
    const scoreBreakdown = document.getElementById('scoreBreakdown');
    let score = 0;

    // Calculate score
    const scores = {
        'Photos': state.photos.length * 10,
        'GPS Location': state.location.latitude ? 25 : 0,
        'Description': state.description.length >= 300 ? 15 : state.description.length >= 100 ? 10 : 5,
        'Beneficiaries': state.beneficiaryCount && state.beneficiaryCount >= 50 ? 10 : 3,
        'Testimonials': state.testimonials ? 20 : 0
    };

    let html = '';
    for (const [item, value] of Object.entries(scores)) {
        score += value;
        html += `
            <div class="score-item">
                <span class="score-item-name">${item}</span>
                <span class="score-item-value">${value} pts</span>
            </div>
        `;
    }

    score = Math.min(score, 100);
    state.trustScore = score;

    html += `
        <div class="total-score">
            <span>Total Trust Score</span>
            <span>${score}/100</span>
        </div>
    `;

    const autoApproved = score >= 80;
    html += `
        <div class="approval-indicator ${autoApproved ? 'approved' : 'pending'}">
            ${autoApproved ? '✅ Will be AUTO-APPROVED ($30 payout)' : '⏳ Pending manual review'}
        </div>
    `;

    scoreBreakdown.innerHTML = html;
}

async function submitVerification() {
    // Validate
    if (!state.campaign.id) {
        showError('Please select a campaign');
        return;
    }

    if (state.photos.length === 0) {
        showError('Please upload at least one photo');
        return;
    }

    if (!state.location.latitude || !state.location.longitude) {
        showError('Please provide a location');
        return;
    }

    if (state.description.length < 50) {
        showError('Description must be at least 50 characters');
        return;
    }

    // Show loading
    document.getElementById('loadingOverlay').style.display = 'flex';

    try {
        // Upload photos and get their IDs
        const photoIds = [];
        for (const photo of state.photos) {
            const formData = new FormData();
            formData.append('telegram_user_id', getTelegramUserId());
            formData.append('photo', photo.file);

            const response = await fetch(`${FIELD_AGENT_API}/photos/upload`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error('Photo upload failed');
            }

            const data = await response.json();
            photoIds.push(data.photo_id);
        }

        // Submit verification
        const verificationResponse = await fetch(`${FIELD_AGENT_API}/verifications/submit`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                telegram_user_id: getTelegramUserId(),
                campaign_id: state.campaign.id,
                description: state.description,
                photo_ids: photoIds,
                gps_latitude: state.location.latitude,
                gps_longitude: state.location.longitude,
                beneficiary_count: state.beneficiaryCount,
                testimonials: state.testimonials
            })
        });

        if (!verificationResponse.ok) {
            const errorData = await verificationResponse.json();
            throw new Error(errorData.error || 'Submission failed');
        }

        const result = await verificationResponse.json();

        // Hide loading
        document.getElementById('loadingOverlay').style.display = 'none';

        // Show success
        const successDetails = document.getElementById('successDetails');
        const autoApproved = result.auto_approved;

        successDetails.innerHTML = `
            <p><strong>Campaign:</strong> ${state.campaign.title}</p>
            <p><strong>Trust Score:</strong> <span style="color: #3b82f6; font-weight: 600;">${result.trust_score}/100</span></p>
            <p><strong>Status:</strong> ${autoApproved ? '✅ Auto-Approved' : '⏳ Pending Review'}</p>
            ${autoApproved ? '<p style="color: #10b981; font-weight: 600;">💰 $30 USD will be sent to your M-Pesa account!</p>' : ''}
            <p style="margin-top: 8px; font-size: 12px; color: #6b7280;">Verification ID: ${result.verification_id}</p>
        `;

        document.getElementById('successMessage').style.display = 'flex';

        // Send close message to Telegram
        if (tg) {
            tg.sendData(JSON.stringify({
                verification_id: result.verification_id,
                trust_score: result.trust_score,
                auto_approved: result.auto_approved
            }));
        }
    } catch (error) {
        console.error('Submission error:', error);
        showError(error.message || 'Failed to submit verification');
    } finally {
        document.getElementById('loadingOverlay').style.display = 'none';
    }
}

function resetForm() {
    state.photos = [];
    state.location = { latitude: null, longitude: null, source: null };
    state.campaign = { id: null, title: null };
    state.description = '';
    state.beneficiaryCount = null;
    state.testimonials = '';

    document.getElementById('photoInput').value = '';
    document.getElementById('campaignSelect').value = '';
    document.getElementById('description').value = '';
    document.getElementById('beneficiaryCount').value = '';
    document.getElementById('testimonials').value = '';
    document.getElementById('charCount').textContent = '0/300';

    updatePhotoGrid();
    updateLocationDisplay();

    document.getElementById('successMessage').style.display = 'none';
    goToStep(1);
}

// ========================================
// Validation
// ========================================

function validateStep(step) {
    switch (step) {
        case 1:
            if (state.photos.length === 0) {
                showError('Please upload at least one photo');
                return false;
            }
            return true;

        case 2:
            if (!state.location.latitude || !state.location.longitude) {
                showError('Please provide a location');
                return false;
            }
            return true;

        case 3:
            if (!state.campaign.id) {
                showError('Please select a campaign');
                return false;
            }
            if (state.description.length < 50) {
                showError('Description must be at least 50 characters');
                return false;
            }
            return true;

        default:
            return true;
    }
}

// ========================================
// Error Handling
// ========================================

function showError(message) {
    const errorMessage = document.getElementById('errorMessage');
    const errorText = document.getElementById('errorText');
    errorText.textContent = message;
    errorMessage.style.display = 'block';

    setTimeout(() => {
        errorMessage.style.display = 'none';
    }, 5000);
}

function closeError() {
    document.getElementById('errorMessage').style.display = 'none';
}

// ========================================
// Initialization
// ========================================

document.addEventListener('DOMContentLoaded', () => {
    loadPendingCampaigns();

    // Log state for debugging
    console.log('TrustVoice Mini App Initialized');
    console.log('Telegram User ID:', getTelegramUserId());
    console.log('API Base:', FIELD_AGENT_API);
});
