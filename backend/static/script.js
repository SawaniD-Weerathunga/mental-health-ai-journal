// =========================================
// 1. EMOTION ANALYSIS LOGIC
// =========================================
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

        // Refresh History & Chart immediately so the new entry shows up
        loadHistory(); 
        loadChart();

    } catch (error) {
        console.error("Error:", error);
        window.location.href = "/login";
    }
}

// =========================================
// 2. HISTORY LOADING LOGIC (UPDATED WITH FILTER)
// =========================================
async function loadHistory() {
    try {
        // 1. Check the dropdown inside the modal
        const picker = document.getElementById('historyMonthPicker');
        let selectedDate = picker ? picker.value : ""; 
        
        // 2. Build the URL based on selection
        let url = "/history";
        
        // If a specific month is selected (value is not empty)
        if (selectedDate) {
            const [year, month] = selectedDate.split('-');
            url += `?month=${month}&year=${year}`;
        }

        const response = await fetch(url);
        
        if (response.status === 401 || response.redirected) {
            return; // Stop loading if not logged in
        }

        const history = await response.json();
        
        // Target the div inside the modal
        const list = document.getElementById("historyList");
        list.innerHTML = ""; // Clear list

        // Handle case where no entries exist for that month
        if (history.length === 0) {
            list.innerHTML = "<p style='text-align:center; color:#777; padding:20px;'>No entries found for this period.</p>";
            return;
        }

        history.forEach(entry => {
            const item = document.createElement("div");
            item.className = `history-item ${entry.emotion}`; 
            
            item.innerHTML = `
                <strong>${entry.emotion.toUpperCase()}</strong>: ${entry.content} <br>
                <span class="history-date">${entry.timestamp}</span>
            `;
            list.appendChild(item);
        });
    } catch (error) {
        console.error("Error loading history:", error);
    }
}

// =========================================
// 3. MODAL (POP-UP) CONTROL LOGIC
// =========================================
function openHistory() {
    document.getElementById('historyModal').style.display = 'flex';
}

function closeHistory() {
    document.getElementById('historyModal').style.display = 'none';
}

window.onclick = function(event) {
    const modal = document.getElementById('historyModal');
    if (event.target == modal) {
        closeHistory();
    }
}

// =========================================
// 4. CHART & DROPDOWN LOGIC
// =========================================
let myChart = null; 

// A. Helper to create month options (Used for both Chart and History)
function createMonthOptions(selectElementId, includeDefault = false) {
    const picker = document.getElementById(selectElementId);
    if (!picker) return; // Guard clause in case element is missing

    const today = new Date();
    
    // Clear existing options first (optional, prevents duplicates if run twice)
    picker.innerHTML = "";

    if (includeDefault) {
        const defaultOption = document.createElement("option");
        defaultOption.value = "";
        defaultOption.text = "All Recent Entries";
        picker.appendChild(defaultOption);
    }

    for (let i = 0; i < 12; i++) {
        const d = new Date(today.getFullYear(), today.getMonth() - i, 1);
        
        const year = d.getFullYear();
        const month = ("0" + (d.getMonth() + 1)).slice(-2); 
        const value = `${year}-${month}`;
        const label = d.toLocaleString('default', { month: 'long', year: 'numeric' });

        const option = document.createElement("option");
        option.value = value;
        // Logic: specific text for the first item if needed
        if (!includeDefault && i === 0) {
            option.text = `Current Month (${label})`;
        } else {
            option.text = label;
        }
        
        picker.appendChild(option);
    }
}

// B. Load Chart function
async function loadChart() {
    try {
        const picker = document.getElementById('monthPicker');
        let selectedDate = picker ? picker.value : "";
        
        if (!selectedDate) selectedDate = ""; 
        
        const [year, month] = selectedDate.split('-');

        let url = '/api/stats';
        if (year && month) {
            url += `?month=${month}&year=${year}`;
        }

        const response = await fetch(url);
        if (!response.ok) return; 

        const data = await response.json();
        const ctx = document.getElementById('emotionChart').getContext('2d');

        if (myChart) {
            myChart.destroy();
        }

        myChart = new Chart(ctx, {
            type: 'doughnut', 
            data: {
                labels: ['Positive', 'Negative', 'Neutral'],
                datasets: [{
                    label: 'Entries',
                    data: [data.positive, data.negative, data.neutral],
                    backgroundColor: ['#2ecc71', '#e74c3c', '#f1c40f'],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false, 
                plugins: {
                    legend: { position: 'bottom' },
                    title: {
                        display: true,
                        text: `Stats for ${selectedDate || 'Current Month'}`
                    }
                }
            }
        });

    } catch (error) {
        console.error("Error loading chart:", error);
    }
}

// =========================================
// 5. INITIALIZATION
// =========================================
window.onload = function() {
    // 1. Setup the Dropdown for the CHART (Main Dashboard)
    createMonthOptions('monthPicker', false);

    // 2. Setup the Dropdown for the HISTORY (Modal)
    createMonthOptions('historyMonthPicker', true);

    // 3. Load Data
    loadHistory();
    loadChart();
};