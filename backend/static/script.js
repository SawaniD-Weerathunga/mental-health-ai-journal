async function analyzeEmotion() {
    const text = document.getElementById("journalEntry").value;
    const resultDiv = document.getElementById("result");
    const emotionResult = document.getElementById("emotionResult");
    const suggestionText = document.getElementById("suggestionText");

    if (!text) {
        alert("Please enter some text!");
        return;
    }

    try {
        const response = await fetch("/analyze", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text: text })
        });

        // Check if user is not logged in (Unauthorized)
        if (response.status === 401 || response.type === 'opaqueredirect' || response.redirected) {
             window.location.href = "/login";
             return;
        }

        const data = await response.json();

        // Show Result
        emotionResult.innerText = `Emotion: ${data.emotion}`;
        suggestionText.innerText = `💡 ${data.suggestion}`;
        resultDiv.style.display = "block";

        // Refresh History
        loadHistory(); 

    } catch (error) {
        console.error("Error:", error);
        // If the server sends HTML (login page) instead of JSON, catch it here
        window.location.href = "/login";
    }
}

async function loadHistory() {
    try {
        const response = await fetch("/history");
        
        if (response.status === 401 || response.redirected) {
            return; // Stop loading if not logged in
        }

        const history = await response.json();
        
        const list = document.getElementById("historyList");
        list.innerHTML = ""; // Clear list

        history.forEach(entry => {
            const li = document.createElement("li");
            li.className = `history-item ${entry.emotion}`;
            li.innerHTML = `
                <strong>${entry.emotion.toUpperCase()}</strong>: ${entry.content} <br>
                <span class="history-date">${entry.timestamp}</span>
            `;
            list.appendChild(li);
        });
    } catch (error) {
        console.error("Error loading history:", error);
    }
}

// Load history when page starts
window.onload = loadHistory;