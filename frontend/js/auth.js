/**
 * Authentication module
 * Handles JWT token storage and validation
 */

const auth = {
    TOKEN_KEY: 'trustvoice_admin_token',
    
    /**
     * Store JWT token in localStorage
     */
    setToken(token) {
        localStorage.setItem(this.TOKEN_KEY, token);
    },
    
    /**
     * Get JWT token from localStorage
     */
    getToken() {
        return localStorage.getItem(this.TOKEN_KEY);
    },
    
    /**
     * Remove JWT token from localStorage
     */
    clearToken() {
        localStorage.removeItem(this.TOKEN_KEY);
    },
    
    /**
     * Check if user is authenticated
     */
    isAuthenticated() {
        const token = this.getToken();
        if (!token) return false;
        
        // Check if token is expired (basic check)
        try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            const exp = payload.exp * 1000; // Convert to milliseconds
            return Date.now() < exp;
        } catch (e) {
            return false;
        }
    },
    
    /**
     * Logout user
     */
    logout() {
        this.clearToken();
        window.location.href = 'login.html';
    }
};

// Protect dashboard pages - redirect to login if not authenticated
if (window.location.pathname.includes('dashboard.html') && !auth.isAuthenticated()) {
    window.location.href = 'login.html';
}
