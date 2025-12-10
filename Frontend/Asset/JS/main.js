// Save logged-in user in localStorage
function setUser(username) {
    localStorage.setItem("gym_user", username);
}

function getUser() {
    return localStorage.getItem("gym_user");
}

async function registerUser() {
    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;
    const res = await fetch("http://127.0.0.1:8000/api/register/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password })
    });
    const data = await res.json();
    document.getElementById("message").innerText = data.message;
}

async function loginUser() {
    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;
    const res = await fetch("http://127.0.0.1:8000/api/login/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password })
    });
    const data = await res.json();
    document.getElementById("message").innerText = data.message;

    if (res.ok) {
        setUser(username);
        window.location.href = "dashboard.html";
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
