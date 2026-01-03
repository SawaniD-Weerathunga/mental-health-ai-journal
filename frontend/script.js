function analyzeJournal() {
    // 1. Get the text from the input box
    const userText = document.getElementById("journalInput").value;
    const resultBox = document.getElementById("result");
    const emotionSpan = document.getElementById("emotionValue");
    const suggestionSpan = document.getElementById("suggestionValue");

    // Simple validation: Don't send empty text
    if (!userText.trim()) {
        alert("Please write something in your journal first!");
        return;
    }

    // 2. Send the text to the Backend (Flask)
    // We use the 'fetch' command to talk to the API
    fetch("http://127.0.0.1:5000/analyze", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ text: userText })
    })
    .then(response => response.json())
    .then(data => {
        // 3. Show the results on the screen
        console.log("Success:", data);
        
        // Update the text
        emotionSpan.innerText = data.emotion;
        suggestionSpan.innerText = data.suggestion;

        // Make the result box visible
        resultBox.style.display = "block";
    })
    .catch((error) => {
        console.error("Error:", error);
        alert("Error connecting to the server. Is your Python backend running?");
    });
}