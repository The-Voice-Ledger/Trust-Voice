/**
 * Dashboard JavaScript
 * Handles registration approval/rejection UI
 */

let currentRegistrationId = null;

// Load admin info on page load
async function loadAdminInfo() {
    try {
        const user = await api.get('/admin/me');
        document.getElementById('adminName').textContent = user.full_name || user.phone_number;
    } catch (error) {
        console.error('Failed to load admin info:', error);
        auth.logout();
    }
}

// Load dashboard statistics
async function loadStats() {
    try {
        const stats = await api.get('/admin/registrations/stats');
        document.getElementById('totalUsers').textContent = stats.total_users;
        document.getElementById('pendingCount').textContent = stats.pending_registrations;
        document.getElementById('approvedToday').textContent = stats.approved_today;
        document.getElementById('rejectedToday').textContent = stats.rejected_today;
    } catch (error) {
        console.error('Failed to load stats:', error);
    }
}

// Load registrations based on filters
async function loadRegistrations() {
    const statusFilter = document.getElementById('statusFilter').value;
    const roleFilter = document.getElementById('roleFilter').value;
    
    const loadingSpinner = document.getElementById('loadingSpinner');
    const errorMessage = document.getElementById('errorMessage');
    const emptyState = document.getElementById('emptyState');
    const table = document.getElementById('registrationsTable');
    const tbody = document.getElementById('registrationsBody');
    
    // Show loading
    loadingSpinner.style.display = 'block';
    errorMessage.style.display = 'none';
    emptyState.style.display = 'none';
    table.style.display = 'none';
    
    try {
        let endpoint = `/admin/registrations/?status_filter=${statusFilter}`;
        if (roleFilter) {
            endpoint += `&role_filter=${roleFilter}`;
        }
        
        const registrations = await api.get(endpoint);
        
        loadingSpinner.style.display = 'none';
        
        if (registrations.length === 0) {
            emptyState.style.display = 'block';
            return;
        }
        
        // Populate table
        tbody.innerHTML = registrations.map(reg => `
            <tr>
                <td><strong>${reg.full_name}</strong></td>
                <td>${reg.phone_number}</td>
                <td>${formatRole(reg.role)}</td>
                <td>${reg.organization || '-'}</td>
                <td>${reg.reason || '-'}</td>
                <td>${formatDate(reg.created_at)}</td>
                <td><span class="status-badge status-${reg.status}">${reg.status}</span></td>
                <td>
                    ${reg.status === 'pending' ? `
                        <div class="actions-cell">
                            <button onclick="openApprovalModal(${reg.id}, '${reg.full_name}')" class="btn btn-success btn-sm">
                                ✅ Approve
                            </button>
                            <button onclick="openRejectionModal(${reg.id}, '${reg.full_name}')" class="btn btn-danger btn-sm">
                                ❌ Reject
                            </button>
                        </div>
                    ` : '-'}
                </td>
            </tr>
        `).join('');
        
        table.style.display = 'table';
    } catch (error) {
        console.error('Failed to load registrations:', error);
        loadingSpinner.style.display = 'none';
        errorMessage.textContent = 'Failed to load registrations: ' + error.message;
        errorMessage.style.display = 'block';
    }
}

// Open approval modal
function openApprovalModal(regId, name) {
    currentRegistrationId = regId;
    document.getElementById('approvalMessage').textContent = `Approve registration for ${name}?`;
    document.getElementById('approvalNotes').value = '';
    document.getElementById('approvalModal').style.display = 'flex';
}

// Open rejection modal
function openRejectionModal(regId, name) {
    currentRegistrationId = regId;
    document.getElementById('rejectionMessage').textContent = `Reject registration for ${name}?`;
    document.getElementById('rejectionReason').value = '';
    document.getElementById('rejectionModal').style.display = 'flex';
}

// Close all modals
function closeModal() {
    document.getElementById('approvalModal').style.display = 'none';
    document.getElementById('rejectionModal').style.display = 'none';
    currentRegistrationId = null;
}

// Confirm approval
async function confirmApprove() {
    if (!currentRegistrationId) return;
    
    const notes = document.getElementById('approvalNotes').value;
    
    try {
        const result = await api.post(`/admin/registrations/${currentRegistrationId}/approve`, {
            admin_notes: notes || null
        });
        
        alert(`✅ ${result.message}`);
        closeModal();
        
        // Reload data
        await loadStats();
        await loadRegistrations();
    } catch (error) {
        alert(`Failed to approve: ${error.message}`);
    }
}

// Confirm rejection
async function confirmReject() {
    if (!currentRegistrationId) return;
    
    const reason = document.getElementById('rejectionReason').value.trim();
    
    if (!reason) {
        alert('Please provide a reason for rejection');
        return;
    }
    
    try {
        const result = await api.post(`/admin/registrations/${currentRegistrationId}/reject`, {
            reason: reason
        });
        
        alert(`❌ ${result.message}`);
        closeModal();
        
        // Reload data
        await loadStats();
        await loadRegistrations();
    } catch (error) {
        alert(`Failed to reject: ${error.message}`);
    }
}

// Handle logout
function handleLogout() {
    if (confirm('Are you sure you want to logout?')) {
        auth.logout();
    }
}

// Utility functions
function formatRole(role) {
    const roleMap = {
        'CAMPAIGN_CREATOR': 'Campaign Creator',
        'FIELD_AGENT': 'Field Agent',
        'DONOR': 'Donor',
        'SYSTEM_ADMIN': 'Admin'
    };
    return roleMap[role] || role;
}

function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    
    return date.toLocaleDateString();
}

// Close modal when clicking outside
window.onclick = function(event) {
    const approvalModal = document.getElementById('approvalModal');
    const rejectionModal = document.getElementById('rejectionModal');
    
    if (event.target === approvalModal) {
        closeModal();
    }
    if (event.target === rejectionModal) {
        closeModal();
    }
}

// Initialize dashboard on page load
document.addEventListener('DOMContentLoaded', async () => {
    await loadAdminInfo();
    await loadStats();
    await loadRegistrations();
    
    // Auto-refresh every 30 seconds
    setInterval(async () => {
        await loadStats();
        await loadRegistrations();
    }, 30000);
});
