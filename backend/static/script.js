// =========================================
// 1. EMOTION ANALYSIS
// =========================================
async function analyzeEmotion() {
    const text = document.getElementById("journalEntry").value;
    const resultDiv = document.getElementById("result");
    const emotionResult = document.getElementById("emotionResult");
    const suggestionText = document.getElementById("suggestionText");

    if (!text) { alert("Please enter some text!"); return; }

    try {
        const response = await fetch("/analyze", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text: text })
        });

        if (response.status === 401 || response.redirected) {
             window.location.href = "/login";
             return;
        }

        const data = await response.json();
        emotionResult.innerText = `Emotion: ${data.emotion}`;
        suggestionText.innerText = `💡 ${data.suggestion}`;
        resultDiv.style.display = "block";

        loadHistory(); 
        updateDashboard();
        loadGamification();
    } catch (error) { console.error("Error:", error); window.location.href = "/login"; }
}

// =========================================
// 2. HISTORY
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
        if (response.status === 401) return;

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
            item.innerHTML = `<strong>${entry.emotion.toUpperCase()}</strong>: ${entry.content} <br> <span class="history-date">${entry.timestamp}</span>`;
            list.appendChild(item);
        });
    } catch (error) { console.error("Error loading history:", error); }
}

// =========================================
// 3. CHART (ANIMATION DISABLED + FULL CIRCLE)
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
        option.text = (!includeDefault && i === 0) ? `Current Month (${label})` : label;
        picker.appendChild(option);
    }
}

async function loadChart() {
    try {
        const picker = document.getElementById('monthPicker');
        let selectedDate = picker ? picker.value : "";
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
                // DISABLE ANIMATION so PDF captures the full circle immediately
                animation: { duration: 0 }, 
                // ENSURE FULL CIRCLE (Standard Doughnut)
                cutout: '60%', 
                plugins: {
                    legend: { position: 'bottom' },
                    title: { display: true, text: `Stats for ${selectedDate}` }
                }
            }
        });
    } catch (error) { console.error("Error loading chart:", error); }
}

// =========================================
// 4. WORD CLOUD
// =========================================
async function loadWordCloud() {
    try {
        const response = await fetch('/api/wordcloud');
        if (!response.ok) return;
        const data = await response.json(); 
        const canvas = document.getElementById('wordCloudCanvas');
        if (data.length === 0) {
            const ctx = canvas.getContext('2d');
            ctx.clearRect(0, 0, canvas.width, canvas.height); 
            ctx.font = "20px Arial"; ctx.fillStyle = "#888"; ctx.fillText("Write more entries!", 50, 50);
            return;
        }
        const maxCount = data[0][1]; 
        const weightFactor = 40 / maxCount; 
        WordCloud(canvas, {
            list: data, gridSize: 8, weightFactor: function (size) { return Math.max(15, size * weightFactor * 3); },
            fontFamily: 'Segoe UI, sans-serif', color: 'random-dark', rotateRatio: 0.5, backgroundColor: 'transparent'
        });
    } catch (error) { console.error("Error loading word cloud:", error); }
}

// =========================================
// 5. CALENDAR
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

        for (let i = 0; i < firstDayIndex; i++) {
            const emptyDiv = document.createElement('div');
            emptyDiv.className = 'day-box empty';
            grid.appendChild(emptyDiv);
        }
        for (let day = 1; day <= daysInMonth; day++) {
            const dayDiv = document.createElement('div');
            dayDiv.innerText = day;
            const dateKey = `${year}-${("0" + month).slice(-2)}-${("0" + day).slice(-2)}`;
            let className = 'day-box';
            if (moodData[dateKey]) {
                className += ` ${moodData[dateKey]}`;
                dayDiv.title = `Mood: ${moodData[dateKey].toUpperCase()}`;
            }
            dayDiv.onclick = () => openDayStats(dateKey);
            dayDiv.style.cursor = "pointer";
            dayDiv.className = className;
            grid.appendChild(dayDiv);
        }
    } catch (error) { console.error("Error loading calendar:", error); }
}

async function openDayStats(dateStr) {
    try {
        const response = await fetch(`/api/day_stats?date=${dateStr}`);
        const data = await response.json(); 
        const total = data.positive + data.negative + data.neutral;
        if (total === 0) { alert("No entries found for this date."); return; }
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
    } catch (error) { console.error("Error opening day stats:", error); }
}

// =========================================
// 6. GAMIFICATION
// =========================================
async function loadGamification() {
    try {
        const response = await fetch('/api/gamification');
        const data = await response.json(); 
        const streakDisplay = document.getElementById('streakDisplay');
        const streakCount = document.getElementById('streakCount');
        if (data.streak > 0) {
            streakCount.innerText = data.streak;
            streakDisplay.style.display = "flex"; 
        } else { streakDisplay.style.display = "none"; }

        const grid = document.getElementById('badgesGrid');
        const noBadges = document.getElementById('noBadgesText');
        grid.innerHTML = ""; 
        if (data.badges.length === 0) { noBadges.style.display = "block"; return; } 
        else { noBadges.style.display = "none"; }
        data.badges.forEach(badge => {
            const card = document.createElement('div');
            card.className = 'badge-card';
            card.innerHTML = `<span class="badge-icon">${badge.icon}</span><span class="badge-name">${badge.name}</span><span class="badge-desc">${badge.desc}</span>`;
            grid.appendChild(card);
        });
    } catch (error) { console.error("Error loading gamification:", error); }
}

// =========================================
// 7. PDF GENERATOR (FINAL FIXED)
// =========================================
async function downloadPDF() {
    const userName = document.getElementById('userNameDisplay').innerText;
    const picker = document.getElementById('monthPicker');
    const periodText = picker.options[picker.selectedIndex].text;
    const todayStr = new Date().toLocaleDateString();

    let selectedDate = picker.value;
    if (!selectedDate) {
         const now = new Date();
         selectedDate = `${now.getFullYear()}-${("0" + (now.getMonth() + 1)).slice(-2)}`;
    }
    const [year, month] = selectedDate.split('-');
    
    const response = await fetch(`/api/stats?month=${month}&year=${year}`);
    const data = await response.json();
    
    const total = data.positive + data.negative + data.neutral;
    const posPct = total ? ((data.positive / total) * 100).toFixed(1) + '%' : "0%";
    const negPct = total ? ((data.negative / total) * 100).toFixed(1) + '%' : "0%";
    const neuPct = total ? ((data.neutral / total) * 100).toFixed(1) + '%' : "0%";

    document.getElementById('repName').innerText = userName;
    document.getElementById('repPeriod').innerText = periodText;
    document.getElementById('repDate').innerText = todayStr;
    document.getElementById('repPosCount').innerText = data.positive;
    document.getElementById('repPosPct').innerText = posPct;
    document.getElementById('repNegCount').innerText = data.negative;
    document.getElementById('repNegPct').innerText = negPct;
    document.getElementById('repNeuCount').innerText = data.neutral;
    document.getElementById('repNeuPct').innerText = neuPct;
    document.getElementById('repTotal').innerText = total;

    // Capture Chart
    const chartCanvas = document.getElementById('emotionChart');
    const chartImgData = chartCanvas.toDataURL("image/png");
    document.getElementById('repChartImg').src = chartImgData;

    // Show PDF Template
    const element = document.getElementById('pdfReportTemplate');
    element.style.display = 'block';

    // *** TIME DELAY (CRITICAL) ***
    await new Promise(resolve => setTimeout(resolve, 500));

    const opt = {
        margin:       0.3, 
        filename:     `Report_${year}_${month}.pdf`,
        image:        { type: 'jpeg', quality: 0.98 },
        html2canvas:  { scale: 2 },
        jsPDF:        { unit: 'in', format: 'a4', orientation: 'portrait' }
    };

    html2pdf().set(opt).from(element).save().then(() => {
        element.style.display = 'none';
    });
}

// =========================================
// 8. INITIALIZATION
// =========================================
function updateDashboard() {
    loadChart();
    loadWordCloud();
    loadCalendar();
}

window.onload = function() {
    createMonthOptions('monthPicker', false);
    createMonthOptions('historyMonthPicker', true);
    loadHistory();
    updateDashboard();
    loadGamification();
};