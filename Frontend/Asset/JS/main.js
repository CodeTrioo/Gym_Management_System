// Save logged-in user in localStorage
function setUser(username) {
    localStorage.setItem("gym_user", username);
}

function getUser() {
    return localStorage.getItem("gym_user");
}

async function registerUser(event) {
    if (event) {
        event.preventDefault();
    }

    const messageEl = document.getElementById("message");
    messageEl.className = "alert d-none";
    messageEl.innerHTML = "";

    // Get all form values
    const firstName = document.getElementById("firstName")?.value;
    const lastName = document.getElementById("lastName")?.value;
    const email = document.getElementById("email")?.value;
    const phone = document.getElementById("phone")?.value;
    const dateOfBirth = document.getElementById("dateOfBirth")?.value;
    const gender = document.getElementById("gender")?.value;
    const address = document.getElementById("address")?.value;
    const password = document.getElementById("password")?.value;
    const confirmPassword = document.getElementById("confirmPassword")?.value;
    const terms = document.getElementById("terms")?.checked;

    // Validate password match
    if (password !== confirmPassword) {
        messageEl.className = "alert alert-danger";
        messageEl.innerHTML = "<strong>Error!</strong> Passwords do not match!";
        messageEl.classList.remove("d-none");
        return;
    }

    // Validate terms acceptance
    if (!terms) {
        messageEl.className = "alert alert-danger";
        messageEl.innerHTML = "<strong>Error!</strong> Please accept the Terms and Conditions to continue.";
        messageEl.classList.remove("d-none");
        return;
    }

    // Prepare registration data
    const registrationData = {
        password,
        firstName,
        lastName,
        email,
        phone,
        dateOfBirth,
        gender,
        address
    };

    try {
        const res = await fetch("http://127.0.0.1:8000/api/register/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(registrationData)
        });

        const data = await res.json();
        
        if (res.ok) {
            messageEl.className = "alert alert-success";
            messageEl.innerHTML = "<strong>Success!</strong> " + (data.message || "Registration successful! Redirecting to login...");
            messageEl.classList.remove("d-none");
            
            // Redirect to login after 2 seconds
            setTimeout(() => {
                window.location.href = "login.html";
            }, 2000);
        } else {
            messageEl.className = "alert alert-danger";
            messageEl.innerHTML = "<strong>Error!</strong> " + (data.message || data.error || "Registration failed. Please try again.");
            messageEl.classList.remove("d-none");
        }
    } catch (error) {
        messageEl.className = "alert alert-danger";
        messageEl.innerHTML = "<strong>Error!</strong> Network error. Please check your connection and try again.";
        messageEl.classList.remove("d-none");
        console.error("Registration error:", error);
    }
}

async function loginUser(event) {
    if (event) {
        event.preventDefault();
    }

    const messageEl = document.getElementById("message");
    messageEl.className = "alert d-none";
    messageEl.innerHTML = "";

    const username = document.getElementById("username")?.value;
    const password = document.getElementById("password")?.value;
    const rememberMe = document.getElementById("rememberMe")?.checked;

    // Basic validation
    if (!username || !password) {
        messageEl.className = "alert alert-danger";
        messageEl.innerHTML = "<strong>Error!</strong> Please enter both username and password.";
        messageEl.classList.remove("d-none");
        return;
    }

    try {
        const res = await fetch("http://127.0.0.1:8000/api/login/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password })
        });

        const data = await res.json();

        if (res.ok) {
            // Save user to localStorage
            setUser(username);
            
            // If remember me is checked, also save to sessionStorage or extend localStorage
            if (rememberMe) {
                localStorage.setItem("rememberMe", "true");
            }

            messageEl.className = "alert alert-success";
            messageEl.innerHTML = "<strong>Success!</strong> " + (data.message || "Login successful! Redirecting...");
            messageEl.classList.remove("d-none");

            // Redirect to dashboard or profile page
            setTimeout(() => {
                // Check if profile.html exists, otherwise redirect to dashboard.html
                window.location.href = "profile.html";
            }, 1500);
        } else {
            messageEl.className = "alert alert-danger";
            messageEl.innerHTML = "<strong>Error!</strong> " + (data.message || data.error || "Invalid username or password. Please try again.");
            messageEl.classList.remove("d-none");
        }
    } catch (error) {
        messageEl.className = "alert alert-danger";
        messageEl.innerHTML = "<strong>Error!</strong> Network error. Please check your connection and try again.";
        messageEl.classList.remove("d-none");
        console.error("Login error:", error);
    }
}

async function logoutUser() {
    await fetch("http://127.0.0.1:8000/api/logout/");
    localStorage.removeItem("gym_user");
    document.getElementById("message").innerText = "Logged out successfully";
    window.location.href = "login.html";
}

// Show username on dashboard
if (document.getElementById("user")) {
    const user = getUser();
    if (user) {
        document.getElementById("user").innerText = user;
    } else {
        // redirect to login if not logged in
        window.location.href = "login.html";
    }
}
