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

        if (response.status === 401 || response.type === 'opaqueredirect' || response.redirected) {
             window.location.href = "/login";
             return;
        }

        const data = await response.json();

        emotionResult.innerText = `Emotion: ${data.emotion}`;
        suggestionText.innerText = `💡 ${data.suggestion}`;
        resultDiv.style.display = "block";

        // Refresh Everything
        loadHistory(); 
        updateDashboard(); // Updates Chart, Cloud, and Calendar

    } catch (error) {
        console.error("Error:", error);
        window.location.href = "/login";
    }
}

// =========================================
// 2. HISTORY LOGIC
// =========================================
async function loadHistory() {
    try {
        const picker = document.getElementById('historyMonthPicker');
        let selectedDate = picker ? picker.value : ""; 
        
        let url = "/history";
        if (selectedDate) {
            const [year, month] = selectedDate.split('-');
            url += `?month=${month}&year=${year}`;
        }

        const response = await fetch(url);
        if (response.status === 401 || response.redirected) return;

        const history = await response.json();
        const list = document.getElementById("historyList");
        list.innerHTML = ""; 

        if (history.length === 0) {
            list.innerHTML = "<p style='text-align:center; color:#777; padding:20px;'>No entries found.</p>";
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

function openHistory() {
    document.getElementById('historyModal').style.display = 'flex';
}

function closeHistory() {
    document.getElementById('historyModal').style.display = 'none';
}

// =========================================
// 3. CHART & ANALYTICS HELPER
// =========================================
let myChart = null; 

function createMonthOptions(selectElementId, includeDefault = false) {
    const picker = document.getElementById(selectElementId);
    if (!picker) return;

    const today = new Date();
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
        if (!includeDefault && i === 0) {
            option.text = `Current Month (${label})`;
        } else {
            option.text = label;
        }
        picker.appendChild(option);
    }
}

// =========================================
// 4. CHART LOADING
// =========================================
async function loadChart() {
    try {
        const picker = document.getElementById('monthPicker');
        let selectedDate = picker ? picker.value : "";
        
        // Handle empty initial state
        if (!selectedDate) {
             const now = new Date();
             selectedDate = `${now.getFullYear()}-${("0" + (now.getMonth() + 1)).slice(-2)}`;
        }
        
        const [year, month] = selectedDate.split('-');

        let url = '/api/stats';
        if (year && month) url += `?month=${month}&year=${year}`;

        const response = await fetch(url);
        if (!response.ok) return; 

        const data = await response.json();
        const ctx = document.getElementById('emotionChart').getContext('2d');

        if (myChart) myChart.destroy();

        myChart = new Chart(ctx, {
            type: 'doughnut', 
            data: {
                labels: ['Positive', 'Negative', 'Neutral'],
                datasets: [{
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
                    title: { display: true, text: `Stats for ${selectedDate}` }
                }
            }
        });
    } catch (error) {
        console.error("Error loading chart:", error);
    }
}

// =========================================
// 5. WORD CLOUD LOGIC
// =========================================
async function loadWordCloud() {
    try {
        const response = await fetch('/api/wordcloud');
        if (!response.ok) return;

        const data = await response.json(); 
        const canvas = document.getElementById('wordCloudCanvas');

        if (data.length === 0) {
            const ctx = canvas.getContext('2d');
            ctx.clearRect(0, 0, canvas.width, canvas.height); // Clear previous
            ctx.font = "20px Arial";
            ctx.fillStyle = "#888";
            ctx.fillText("Write more entries to see your cloud!", 50, 50);
            return;
        }

        const maxCount = data[0][1]; 
        const weightFactor = 40 / maxCount; 

        WordCloud(canvas, {
            list: data,
            gridSize: 8,
            weightFactor: function (size) {
                return Math.max(15, size * weightFactor * 3); 
            },
            fontFamily: 'Segoe UI, sans-serif',
            color: 'random-dark',
            rotateRatio: 0.5,
            backgroundColor: 'transparent'
        });
    } catch (error) {
        console.error("Error loading word cloud:", error);
    }
}

// =========================================
// 6. CALENDAR & DAY STATS LOGIC
// =========================================
async function loadCalendar() {
    try {
        const picker = document.getElementById('monthPicker');
        let selectedDate = picker ? picker.value : "";
        
        if (!selectedDate) {
            const now = new Date();
            selectedDate = `${now.getFullYear()}-${("0" + (now.getMonth() + 1)).slice(-2)}`;
        }
        
        const [year, month] = selectedDate.split('-').map(Number);
        const response = await fetch(`/api/calendar?month=${("0" + month).slice(-2)}&year=${year}`);
        const moodData = await response.json(); 

        const grid = document.getElementById('calendarGrid');
        grid.innerHTML = ""; 

        const daysInMonth = new Date(year, month, 0).getDate();
        const firstDayIndex = new Date(year, month - 1, 1).getDay();

        // Empty slots
        for (let i = 0; i < firstDayIndex; i++) {
            const emptyDiv = document.createElement('div');
            emptyDiv.className = 'day-box empty';
            grid.appendChild(emptyDiv);
        }

        // Days
        for (let day = 1; day <= daysInMonth; day++) {
            const dayDiv = document.createElement('div');
            dayDiv.innerText = day;
            
            const dateKey = `${year}-${("0" + month).slice(-2)}-${("0" + day).slice(-2)}`;
            let className = 'day-box';
            
            if (moodData[dateKey]) {
                className += ` ${moodData[dateKey]}`;
                dayDiv.title = `Mood: ${moodData[dateKey].toUpperCase()}`;
            }

            // Click event to open Day Stats
            dayDiv.onclick = () => openDayStats(dateKey);
            dayDiv.style.cursor = "pointer";

            dayDiv.className = className;
            grid.appendChild(dayDiv);
        }
    } catch (error) {
        console.error("Error loading calendar:", error);
    }
}

// Function to open the Day Stats Modal
async function openDayStats(dateStr) {
    try {
        const response = await fetch(`/api/day_stats?date=${dateStr}`);
        const data = await response.json(); 

        const total = data.positive + data.negative + data.neutral;
        
        if (total === 0) {
            alert("No entries found for this date.");
            return;
        }

        const posPct = ((data.positive / total) * 100).toFixed(0);
        const negPct = ((data.negative / total) * 100).toFixed(0);
        const neuPct = ((data.neutral / total) * 100).toFixed(0);

        document.getElementById('dayModalTitle').innerText = `📅 Analysis for ${dateStr}`;
        
        document.getElementById('dayPosText').innerText = `${posPct}% (${data.positive})`;
        document.getElementById('dayPosBar').style.width = `${posPct}%`;

        document.getElementById('dayNegText').innerText = `${negPct}% (${data.negative})`;
        document.getElementById('dayNegBar').style.width = `${negPct}%`;

        document.getElementById('dayNeuText').innerText = `${neuPct}% (${data.neutral})`;
        document.getElementById('dayNeuBar').style.width = `${neuPct}%`;

        document.getElementById('dayTotalText').innerText = `Total Entries: ${total}`;
        document.getElementById('dayModal').style.display = 'flex';

    } catch (error) {
        console.error("Error opening day stats:", error);
    }
}

function closeDayModal() {
    document.getElementById('dayModal').style.display = 'none';
}

// =========================================
// 7. INITIALIZATION & UTILS
// =========================================
function updateDashboard() {
    loadChart();
    loadWordCloud();
    loadCalendar();
}

// Global click listener to close modals
window.onclick = function(event) {
    const hModal = document.getElementById('historyModal');
    const dModal = document.getElementById('dayModal');
    if (event.target == hModal) closeHistory();
    if (event.target == dModal) closeDayModal();
}

window.onload = function() {
    createMonthOptions('monthPicker', false);
    createMonthOptions('historyMonthPicker', true);

    loadHistory();
    // Load Dashboard (Chart, Cloud, Calendar)
    updateDashboard();
};