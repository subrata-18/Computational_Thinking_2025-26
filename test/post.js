const url = "http://127.0.0.1:5000/NewUser_login";

const newUserData = {
    Username: "Subrata11xyz",
    NewPassword: "securepassword123"
};

async function createUser() {
    try {
        const response = await fetch(url, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(newUserData)
        });

        const data = await response.json();

        console.log("Status:", response.status);
        console.log("Response:", data);

    } catch (error) {
        console.error("Request failed:", error);
    }
}

createUser();