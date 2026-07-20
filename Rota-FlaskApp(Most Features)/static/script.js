fetch("/api/schedule")
  .then(res => res.json())
  .then(data => buildTable(data));
  
// Extract unique people from the schedule data and assign Bleep task
function getPeople(data) {
    const people = new Set();

    // Change Reviewing to Reviewingᴮ (assign Bleep task)
    data["Reviewingᴮ"] = data["Reviewing"];
    delete data["Reviewing"];

    // If Reviewingᴮ is empty, add one random person from Ip Echo to Ip Echoᴮ
    data["IP Echoᴮ"] = Array.from({ length: 14 }, () => []); // Create Ip Echoᴮ task with empty arrays for each day part

    // Assign random Ip Echo person to empty Reviewingᴮ slots
    for (let i = 0; i < data["Reviewingᴮ"].length; i++) {
        // Ensure day part is an array
        const dayPart = Array.isArray(data["Reviewingᴮ"][i]) ? data["Reviewingᴮ"][i] : [];
        if (dayPart.length === 0 && data["IP Echo"].length > 0) {
            // Obtain random person from IP Echo for this day part
            const ipEchoDayPart = data["IP Echo"][i];
            if (ipEchoDayPart.length > 0) {
                const randomIndex = Math.floor(Math.random() * ipEchoDayPart.length);
                const selectedPerson = ipEchoDayPart[randomIndex];
                // Remove selected person from IP Echo day part
                data["IP Echo"][i] = ipEchoDayPart.filter(person => person !== selectedPerson);
                // Assign selected person to IP Echoᴮ day part
                data["IP Echoᴮ"][i].push(selectedPerson);
            }
        }
    }

    // Collect unique people
    for (const task in data) {
        data[task].forEach(dayPart => {
            dayPart.forEach(person => people.add(person));
        });
    }

    return Array.from(people);
}

// Build the schedule table
function buildTable(data) {
    const table = document.getElementById("schedule-table");
    table.innerHTML = "";

    const people = getPeople(data);
    // Sort people alphabetically (case-insensitive)
    people.sort((a, b) => a.localeCompare(b, undefined, { sensitivity: 'base' }));
    const dayParts = 14;

    // Header row
    const thead = document.createElement("thead");

    // Get current month
    const currentMonth = new Date().toLocaleString('default', { month: 'long' });
    const days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

    // ---- Row 1: Month + Days + Comments ----
    const row1 = document.createElement("tr");
    row1.innerHTML = `<th rowspan="2" contenteditable="true">${currentMonth}</th>`;

    days.forEach(day => {
        row1.innerHTML += `<th colspan="2">${day}</th>`;
    });

    row1.innerHTML += `<th rowspan="2" style="min-width:300px;">Comments</th>`;
    thead.appendChild(row1);

    // ---- Row 2: AM / PM ----
    const row2 = document.createElement("tr");
    days.forEach(() => {
        row2.innerHTML += `<th>AM</th><th>PM</th>`;
    });
    thead.appendChild(row2);

    table.appendChild(thead);

    // Rows per person
    people.forEach(person => {
        const row = document.createElement("tr");
        row.innerHTML = `<th style="text-align:left;">${person}</th>`;

        for (let i = 0; i < dayParts; i++) {
            const assignments = [];

            for (const task in data) {
                if (data[task][i].includes(person)) {
                    assignments.push(task);
                }
            }

            // Editable for possible changes
            row.innerHTML += `<td contenteditable="true">${assignments.join(", ")}</td>`;
        }

        // Comments cell: make it reasonably wide and editable
        row.innerHTML += `<td contenteditable="true" style="min-width:300px; white-space:pre-wrap;"></td>`;

        table.appendChild(row);
    });

    // Wire placeholders for contenteditable comment cells
    wirePlaceholders();
}

// Toggle a visual placeholder for empty contenteditable cells
function wirePlaceholders() {
    document.querySelectorAll('td[contenteditable="true"]').forEach(td => {
        const update = () => {
            // normalize non-breaking spaces and whitespace
            const text = td.textContent.replace(/\u00A0/g, '').trim();
            if (text === '') td.setAttribute('data-empty', '');
            else td.removeAttribute('data-empty');
        };
        update();
        td.addEventListener('input', update);
        td.addEventListener('blur', update);
        td.addEventListener('paste', () => setTimeout(update, 0));
    });
}
