// ------------------------------
// JS LOADED CHECK
// ------------------------------
console.log('JS loaded successfully');

// ------------------------------
// SELECT ELEMENTS (SAFE)
// ------------------------------
const searchBtn = document.getElementById("search-button");
const input = document.querySelector(".search-box-input input");

const trustPercent = document.getElementById("trustPercent");
const positiveValue = document.getElementById("positiveValue");
const negativeValue = document.getElementById("negativeValue");

const positiveBar = document.getElementById("positiveBar");
const negativeBar = document.getElementById("negativeBar");

const resultContainer = document.querySelector(".result-container");
const resultCard = document.getElementById("resultCard");

const recommendText = document.getElementById("recommendText");
const loadingbox = document.getElementById("loading");

// ------------------------------
// SEARCH FUNCTION (SAFE)
// ------------------------------
if (searchBtn && input) {

    searchBtn.addEventListener("click", async () => {

        console.log("Search button clicked");

        const product = input.value.trim();
        const userId = localStorage.getItem('userId');

        console.log("User ID:", userId);

        // Optional login check
        if (!userId) {
            alert("Please login first");
            return;
        }

        if (product === "") {
            alert("Enter a product name or keyword");
            return;
        }

        try {
            loadingbox.style.display = "block";
            resultContainer.classList.remove("show");

            const response = await fetch("/analyze", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ product: product, userId: userId })
            });

            const data = await response.json();
            loadingbox.style.display = "none";

            console.log(data);

            if (data.error) {
                alert(data.error);
                return;
            }

            // Update UI
            trustPercent.innerText = data.trust + "%";
            positiveValue.innerText = data.positive + "%";
            negativeValue.innerText = data.negative + "%";

            document.getElementById("fakeCount").innerText = data.fake_reviews;
            document.getElementById("realCount").innerText = data.real_reviews;

            positiveBar.style.width = data.positive + "%";
            negativeBar.style.width = data.negative + "%";

            resultContainer.classList.add("show");
            resultCard.classList.add("show");

            // Recommendation logic
            if (data.trust >= 80) {
                recommendText.innerHTML = "✅ Highly Recommended";
            } else if (data.trust >= 60) {
                recommendText.innerHTML = "✅ Recommended to Buy";
            } else if (data.trust >= 40) {
                recommendText.innerHTML = "⚠️ Mixed Reviews";
            } else {
                recommendText.innerHTML = "❌ Not Recommended";
            }

        } catch (error) {
            loadingbox.style.display = "none";
            console.error("Error:", error);
            alert("Server connection error");
        }
    });

    // ENTER KEY SUPPORT
    input.addEventListener("keypress", function (e) {
        if (e.key === "Enter") {
            searchBtn.click();
        }
    });
}

// ------------------------------
// SIGNUP FUNCTION
// ------------------------------
async function signup() {

    const name = document.getElementById('name')?.value;
    const email = document.getElementById('email')?.value;
    const password = document.getElementById('password')?.value;

    if (!name || !email || !password) {
        alert("Please fill all fields");
        return;
    }

    const res = await fetch("/signup", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ name, email, password })
    });

    const data = await res.json();
    document.getElementById('authMessage').innerText = data.message || data.error;
}

// ------------------------------
// LOGIN FUNCTION
// ------------------------------
async function login() {

    const email = document.getElementById('email')?.value;
    const password = document.getElementById('password')?.value;

    if (!email || !password) {
        alert("Enter email and password");
        return;
    }

    const res = await fetch("/login", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ email, password })
    });

    const data = await res.json();
    console.log("Login response:", data);

    if (data.userId) {
        localStorage.setItem("userId", data.userId);

        document.getElementById('authMessage').innerText = "Login Successful ✅";

        // Redirect to main page
        window.location.href = "/home";
    } else {
        document.getElementById('authMessage').innerText = data.error;
    }
}

// ------------------------------
// SKIP LOGIN
// ------------------------------
// function skipLogin() {
//     console.log("Skipping login");
//     window.location.href = "/home";
// }

// ------------------------------
// PAGE PROTECTION (ONLY INDEX)
// ------------------------------
window.onload = function () {

    const userId = localStorage.getItem("userId");

    // Protect only main page
    if (!userId && window.location.pathname === "/") {
        window.location.href = "/login-page";
    }
};

function toggleProfile() {
    const panel = document.getElementById("profilePanel");

    if (panel.style.display === "none" || panel.style.display === "") {
        panel.style.display = "block";
    } else {
        panel.style.display = "none";
    }
}
function goToProfile() {
    window.location.href = '/profile';
}
function logout() {
    window.location.href = '/logout';
}