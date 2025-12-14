// CSRF TOKEN HELPER
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    
    // Fallback to meta tag if cookie not found
    if (!cookieValue) {
        const metaTag = document.querySelector('meta[name="csrf-token"]');
        if (metaTag) {
            cookieValue = metaTag.getAttribute('content');
        }
    }
    
    return cookieValue;
}


// MESSAGE DISPLAY HELPER
function showMessage(message, type = 'info') {
    const messageEl = document.getElementById('message');
    if (!messageEl) {
        console.warn('Message element not found');
        return;
    }
    
    // Remove existing classes
    messageEl.className = 'alert';
    
    // Add appropriate class
    switch(type) {
        case 'success':
            messageEl.classList.add('alert-success');
            break;
        case 'error':
        case 'danger':
            messageEl.classList.add('alert-danger');
            break;
        case 'warning':
            messageEl.classList.add('alert-warning');
            break;
        default:
            messageEl.classList.add('alert-info');
    }
    
    // Set message with icon
    const icon = type === 'success' ? '✓' : type === 'error' ? '✗' : 'ℹ';
    messageEl.innerHTML = `<strong>${icon} ${type === 'success' ? 'Success!' : 'Error!'}</strong> ${message}`;
    
    // Show message
    messageEl.classList.remove('d-none');
    
    // Scroll to message
    messageEl.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    
    // Auto-hide success messages after 5 seconds
    if (type === 'success') {
        setTimeout(() => {
            messageEl.classList.add('d-none');
        }, 5000);
    }
}


// REGISTER USER FUNCTION
async function registerUser(event) {
    if (event) {
        event.preventDefault();
    }

    console.log('='.repeat(60));
    console.log('REGISTRATION FORM SUBMITTED');
    console.log('='.repeat(60));

    // Clear previous messages
    const messageEl = document.getElementById('message');
    if (messageEl) {
        messageEl.classList.add('d-none');
    }

    // Get form values
    const firstName = document.getElementById('firstName')?.value?.trim();
    const lastName = document.getElementById('lastName')?.value?.trim();
    const email = document.getElementById('email')?.value?.trim().toLowerCase();
    const gender = document.getElementById('gender')?.value;
    const password = document.getElementById('password')?.value;
    const confirmPassword = document.getElementById('confirmPassword')?.value;
    const terms = document.getElementById('terms')?.checked;

    console.log('Form Data:');
    console.log('  First Name:', firstName);
    console.log('  Last Name:', lastName);
    console.log('  Email:', email);
    console.log('  Gender:', gender);
    console.log('  Password Length:', password?.length);
    console.log('  Terms Accepted:', terms);

    // CLIENT-SIDE VALIDATION
    if (!firstName || !lastName) {
        showMessage('First name and last name are required', 'error');
        return;
    }

    if (!email) {
        showMessage('Email is required', 'error');
        return;
    }

    // Email format validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        showMessage('Please enter a valid email address', 'error');
        return;
    }

    if (!gender) {
        showMessage('Please select your gender', 'error');
        return;
    }

    if (!password) {
        showMessage('Password is required', 'error');
        return;
    }

    if (password.length < 8) {
        showMessage('Password must be at least 8 characters long', 'error');
        return;
    }

    if (password !== confirmPassword) {
        showMessage('Passwords do not match!', 'error');
        return;
    }

    if (!terms) {
        showMessage('Please accept the Terms and Conditions to continue', 'error');
        return;
    }

    // Prepare registration data
    const registrationData = {
        firstName: firstName,
        lastName: lastName,
        email: email,
        gender: gender,
        password: password,
        confirmPassword: confirmPassword
    };

    console.log('Sending registration request...');

    // Get and disable submit button
    const submitBtn = document.querySelector('#registrationForm button[type="submit"]');
    const originalBtnText = submitBtn?.innerHTML;
    
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Creating Account...';
    }

    try {
        // Get CSRF token
        const csrfToken = getCookie('csrftoken');
        console.log('CSRF Token:', csrfToken ? '✓ Found' : '✗ NOT FOUND');

        if (!csrfToken) {
            console.error('CSRF token not found! Check if @ensure_csrf_cookie is on register_view');
        }

        // Send request to CORRECT URL (matches Django urls.py)
        const response = await fetch('/register-user/', {  //  CORRECT URL
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken || ''
            },
            credentials: 'same-origin',
            body: JSON.stringify(registrationData)
        });

        console.log('Response Status:', response.status, response.statusText);

        const data = await response.json();
        console.log('Response Data:', data);

        if (response.ok) {
            console.log('✓ Registration successful!');
            showMessage(data.message || 'Registration successful! Redirecting...', 'success');
            
            // Clear form
            const form = document.getElementById('registrationForm');
            if (form) form.reset();
            
            // Redirect to dashboard (user is logged in via Django)
            setTimeout(() => {
                console.log('Redirecting to:', data.redirect || '/dashboard/');
                window.location.href = data.redirect || '/dashboard/';
            }, 2000);
        } else {
            console.error('✗ Registration failed:', data);
            showMessage(data.message || 'Registration failed. Please try again.', 'error');
            
            // Re-enable button
            if (submitBtn && originalBtnText) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalBtnText;
            }
        }
    } catch (error) {
        console.error('✗ Network error:', error);
        showMessage('Network error. Please check your connection and try again.', 'error');
        
        // Re-enable button
        if (submitBtn && originalBtnText) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalBtnText;
        }
    }
}

// LOGIN USER FUNCTION
async function loginUser(event) {
    if (event) {
        event.preventDefault();
    }

    console.log('='.repeat(60));
    console.log('LOGIN FORM SUBMITTED');
    console.log('='.repeat(60));

    // Clear previous messages
    const messageEl = document.getElementById('message');
    if (messageEl) {
        messageEl.classList.add('d-none');
    }

    // Get form values
    const email = document.getElementById('email')?.value?.trim().toLowerCase();
    const password = document.getElementById('password')?.value;
    const rememberMe = document.getElementById('rememberMe')?.checked;

    console.log('Login Data:');
    console.log('  Email:', email);
    console.log('  Password Length:', password?.length);
    console.log('  Remember Me:', rememberMe);

    // CLIENT-SIDE VALIDATION
    if (!email) {
        showMessage('Email is required', 'error');
        return;
    }

    if (!password) {
        showMessage('Password is required', 'error');
        return;
    }

    console.log('Sending login request...');

    // Get and disable submit button
    const submitBtn = document.querySelector('#loginForm button[type="submit"]');
    const originalBtnText = submitBtn?.innerHTML;
    
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Logging in...';
    }

    try {
        // Get CSRF token
        const csrfToken = getCookie('csrftoken');
        console.log('CSRF Token:', csrfToken ? '✓ Found' : '✗ NOT FOUND');

        if (!csrfToken) {
            console.error('CSRF token not found! Check if @ensure_csrf_cookie is on login_view');
        }

        // Send request to CORRECT URL (matches Django urls.py)
        const response = await fetch('/login-user/', {  //  CORRECT URL
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken || ''
            },
            credentials: 'same-origin',
            body: JSON.stringify({ 
                email: email, 
                password: password 
            })
        });

        console.log('Response Status:', response.status, response.statusText);

        const data = await response.json();
        console.log('Response Data:', data);

        if (response.ok) {
            console.log('✓ Login successful!');
            showMessage(data.message || 'Login successful! Redirecting...', 'success');
            
            // Note: Django handles session management
            // No need for localStorage - Django creates secure session cookie
            
            // Redirect to dashboard
            setTimeout(() => {
                console.log('Redirecting to:', data.redirect || '/dashboard/');
                window.location.href = data.redirect || '/dashboard/';
            }, 1000);
        } else {
            console.error('✗ Login failed:', data);
            showMessage(data.message || 'Invalid email or password. Please try again.', 'error');
            
            // Re-enable button
            if (submitBtn && originalBtnText) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalBtnText;
            }
        }
    } catch (error) {
        console.error('✗ Network error:', error);
        showMessage('Network error. Please check your connection and try again.', 'error');
        
        // Re-enable button
        if (submitBtn && originalBtnText) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalBtnText;
        }
    }
}

async function logoutUser() {
    console.log('Logging out...');
    
    try {
        const csrfToken = getCookie('csrftoken');
        
        const response = await fetch('/logout/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken || ''
            },
            credentials: 'same-origin'
        });
        
        console.log('Logout response:', response.status);
        
        // Redirect to home
        window.location.href = '/';
    } catch (error) {
        console.error('Logout error:', error);
        // Still redirect even if error
        window.location.href = '/';
    }
}


function initPasswordValidation() {
    const passwordInput = document.getElementById('password');
    const confirmPasswordInput = document.getElementById('confirmPassword');
    
    if (passwordInput) {
        passwordInput.addEventListener('input', function() {
            const value = this.value;
            
            if (value.length === 0) {
                this.classList.remove('is-valid', 'is-invalid');
            } else if (value.length < 8) {
                this.classList.add('is-invalid');
                this.classList.remove('is-valid');
            } else {
                this.classList.add('is-valid');
                this.classList.remove('is-invalid');
            }
        });
    }
    
    if (confirmPasswordInput && passwordInput) {
        confirmPasswordInput.addEventListener('input', function() {
            const value = this.value;
            const passwordValue = passwordInput.value;
            
            if (value.length === 0) {
                this.classList.remove('is-valid', 'is-invalid');
            } else if (value !== passwordValue) {
                this.classList.add('is-invalid');
                this.classList.remove('is-valid');
            } else {
                this.classList.add('is-valid');
                this.classList.remove('is-invalid');
            }
        });
    }
}

document.addEventListener('DOMContentLoaded', function() {
    console.log('='.repeat(60));
    console.log('FitZone JavaScript Loaded Successfully');
    console.log('Version: 2.0 (Fixed & Secure)');
    console.log('='.repeat(60));
    
    // Check for CSRF token
    const csrfToken = getCookie('csrftoken');
    console.log('CSRF Token on page load:', csrfToken ? '✓ Available' : '✗ Not available');
    
    if (!csrfToken) {
        console.warn('⚠ CSRF token not found! Forms may fail to submit.');
        console.warn('⚠ Make sure @ensure_csrf_cookie is added to your views.');
    }
    
    // Initialize password validation
    initPasswordValidation();
    
    // Log available forms
    if (document.getElementById('registrationForm')) {
        console.log('✓ Registration form found');
    }
    if (document.getElementById('loginForm')) {
        console.log('✓ Login form found');
    }
    
    console.log('='.repeat(60));
});