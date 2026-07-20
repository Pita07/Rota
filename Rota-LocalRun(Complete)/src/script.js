buildTable(taskSchedules);

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

    // Build list of people based on `originalWorkerOrder` 
    let people;
    if (typeof originalWorkerOrder !== 'undefined' && Array.isArray(originalWorkerOrder) && originalWorkerOrder.length > 0) {
        people = originalWorkerOrder.slice();
    } else if (typeof allPeople !== 'undefined' && Array.isArray(allPeople)) {
        people = allPeople.slice();
    } else {
        people = getPeople(data);
    }
    // Maintain the provided original order; do not sort alphabetically
    const dayParts = 14;

    // Header row
    const thead = document.createElement("thead");

    const days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

    // Empty Month cell + Days + Comments
    const row1 = document.createElement("tr");
    // Leave the month cell editable but empty; add name-sep to separate names column
    row1.innerHTML = `<th rowspan="2" contenteditable="true" class="name-sep"></th>`;

    days.forEach(day => {
        // add a vertical separator at the end of each day block
        row1.innerHTML += `<th class="day-sep" colspan="2">${day}</th>`;
    });

    row1.innerHTML += `<th rowspan="2" style="min-width:300px;">Comments</th>`;
    thead.appendChild(row1);

    // AM / PM
    const row2 = document.createElement("tr");
    days.forEach(() => {
        // PM column keeps the vertical separator class
        row2.innerHTML += `<th>AM</th><th class="day-sep">PM</th>`;
    });
    // thick separator after AM/PM header
    row2.classList.add('row-sep');
    thead.appendChild(row2);

    table.appendChild(thead);

    // tbody to hold person rows
    const tbody = document.createElement("tbody");

    // Rows per person
    people.forEach((person, idx) => {
        const row = document.createElement("tr");
        // add name column separator class
        row.innerHTML = `<th class="name-sep" style="text-align:left;">${person}</th>`;

        for (let i = 0; i < dayParts; i++) {
            const assignments = [];
            for (const task in data) {
                if (data[task][i].includes(person)) {
                    assignments.push(task);
                }
            }

            // add day-sep class to PM columns so the vertical separator spans the whole column
            if (i % 2 === 1) {
                row.innerHTML += `<td class="day-sep" contenteditable="true">${assignments.join(", ")}</td>`;
            } else {
                row.innerHTML += `<td contenteditable="true">${assignments.join(", ")}</td>`;
            }
        }

        // Comments cell (wide and editable)
        row.innerHTML += `<td contenteditable="true" style="min-width:300px; white-space:pre-wrap;"></td>`;

        // Add horizontal separators after specified rows
        if (typeof lastPhysioIndex !== 'undefined' && idx === lastPhysioIndex) {
            row.classList.add('row-sep');
        }
        if (typeof lastAssistIndex !== 'undefined' && idx === lastAssistIndex) {
            row.classList.add('row-sep');
        }

        tbody.appendChild(row);
    });

    // Append tbody after building all person rows
    table.appendChild(tbody);

}


