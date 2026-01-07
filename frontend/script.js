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
        const response = await fetch("http://127.0.0.1:5000/analyze", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text: text })
        });

        const data = await response.json();

        // Show Result
        emotionResult.innerText = `Emotion: ${data.emotion}`;
        suggestionText.innerText = `💡 ${data.suggestion}`;
        resultDiv.style.display = "block";

        // Refresh History immediately so the new entry shows up
        loadHistory(); 

    } catch (error) {
        console.error("Error:", error);
        alert("Something went wrong. Is the server running?");
    }
}

// --- NEW FUNCTION: Load History ---
async function loadHistory() {
    try {
        const response = await fetch("http://127.0.0.1:5000/history");
        const history = await response.json();
        
        const list = document.getElementById("historyList");
        list.innerHTML = ""; // Clear existing list

        history.forEach(entry => {
            const li = document.createElement("li");
            li.className = `history-item ${entry.emotion}`; // Adds color class
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

// Load history when the page starts
window.onload = loadHistory;