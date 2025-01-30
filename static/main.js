
const chartConfig = {
    maintainAspectRatio: false,
    responsive: true,
    plugins: {
        legend: {
            labels: {
                color: '#fff'
            }
        }
    },
    scales: {
        x: {
            grid: {color: 'rgba(255,255,255,0.1)'},
            ticks: {color: '#fff'}
        },
        y: {
            grid: {color: 'rgba(255,255,255,0.1)'},
            ticks: {color: '#fff'}
        }
    }
};

let performanceChart = null;
let cgpaTrendChart = null;

function destroyCharts() {
    if (performanceChart) {
        performanceChart.destroy();
        performanceChart = null;
    }
    if (cgpaTrendChart) {
        cgpaTrendChart.destroy();
        cgpaTrendChart = null;
    }
}



function createTableFromData(columns, data) {
    if (!Array.isArray(columns) || !Array.isArray(data)) {
        console.error("Invalid columns or data format");
        return null;
    }

    const table = document.createElement("table");
    table.className = "responsive-table";

    // Create Table Header
    const thead = document.createElement("thead");
    const headerRow = document.createElement("tr");

    // Add USN and Name headers
    headerRow.innerHTML = '<th>USN</th><th>Name</th>';

    // Add Subject Headers
    const subjectHeaders = columns.slice(2, -3); // Exclude first two and last three
    for (let i = 0; i < subjectHeaders.length; i += 2) {
        const subject = subjectHeaders[i].split('_')[0];
        headerRow.innerHTML += `<th>${subject} Total</th>`;
    }

    // Add Last Three Headers
    columns.slice(-3).forEach(header => {
        headerRow.innerHTML += `<th>${header}</th>`;
    });

    thead.appendChild(headerRow);
    table.appendChild(thead);

    // Create Table Body
    const tbody = document.createElement("tbody");
    data.forEach((row) => {
        if (!Array.isArray(row)) {
            console.error("Invalid row format:", row);
            return;
        }

        const tr = document.createElement("tr");

        // Add USN and Name
        tr.innerHTML = `<td>${row[0]}</td><td>${row[1]}</td>`;

        // Add Subject Totals
        for (let i = 2; i < row.length - 3; i += 2) {
            const internal = parseFloat(row[i]) || 0;
            const external = parseFloat(row[i + 1]) || 0;
            const total = internal + external;
            const td = document.createElement('td');
            td.textContent = total.toFixed(2);
            td.setAttribute('data-internal', internal.toFixed(2));
            td.setAttribute('data-external', external.toFixed(2));
            td.className = 'hoverable';
            tr.appendChild(td);
        }

        // Add Last Three Columns
        row.slice(-3).forEach(value => {
            tr.innerHTML += `<td>${value}</td>`;
        });

        tbody.appendChild(tr);
    });
    table.appendChild(tbody);

    // Add Tooltip Interaction
    const tooltip = document.getElementById('tooltip');
    table.addEventListener('mouseover', function (e) {
        if (e.target.classList.contains('hoverable')) {
            const internal = e.target.getAttribute('data-internal');
            const external = e.target.getAttribute('data-external');
            tooltip.textContent = `Internal: ${internal}, External: ${external}`;
            tooltip.style.display = 'block';
        }
    });

    table.addEventListener('mousemove', function (e) {
        if (e.target.classList.contains('hoverable')) {
            tooltip.style.left = `${e.pageX + 10}px`;
            tooltip.style.top = `${e.pageY + 10}px`;
        }
    });

    table.addEventListener('mouseout', function (e) {
        if (e.target.classList.contains('hoverable')) {
            tooltip.style.display = 'none';
        }
    });

    return table;
}

function createCGPAChart(cgpaData) {
    const ctx = document.getElementById('cgpaChart').getContext('2d');
    cgpaTrendChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: cgpaData.map((_, index) => `Sem ${index + 1}`),
            datasets: [{
                label: 'CGPA Trend',
                data: cgpaData,
                borderColor: '#2997ff',
                tension: 0.4,
                fill: true,
                backgroundColor: 'rgba(41, 151, 255, 0.1)'
            }]
        },
        options: chartConfig
    });
}

function handleCommonInput() {
    const input = document.getElementById("usnInput").value.trim();

    // Check if the input is a USN (e.g., 1BI23CD055)
    if (/^\d[A-Za-z]{2}\d{2}[A-Za-z]{2}\d{3}$/.test(input)) {
        getStudentMarks(input);
    }
    // Check if the input is a semester number (e.g.,1BI23CD etc.)
    else if (/^\d[A-Za-z]{2}\d{1,2}[A-Za-z]{2}$/.test(input)) {
        getSemMarks(input);
    }
    // Handle invalid input
    else {
        console.error("Invalid input. Please enter a valid USN or semester number.");
        const resultsDiv = document.getElementById("results");
        resultsDiv.innerHTML = `<p class="error">Invalid input. Please enter a valid USN or semester number.</p>`;
    }
}

function createSubjectChart(subjectData) {
    let ctx = document.getElementById('subjectChart').getContext('2d');
    console.log("Subject Data:", subjectData);
    console.log("Canvas Context:", ctx);
    destroyCharts();
    performanceChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: subjectData.map(item => item.subject),
            datasets: [{
                label: 'Marks Distribution',
                data: subjectData.map(item => item.average),
                backgroundColor: 'rgba(41, 151, 255, 0.5)',
                borderColor: '#2997ff',
                borderWidth: 1
            }]
        },
        options: chartConfig
    });
}

// Modified getStudentMarks function
function getStudentMarks() {
    const usn = document.getElementById("usnInput").value;
    const apiUrl = `/api/v1/student/${usn}`;

    destroyCharts(); // Clear previous charts

    fetch(apiUrl)
        .then((response) => response.json())
        .then((data) => {
            const resultsDiv = document.getElementById("results");
            resultsDiv.innerHTML = `
                <div class="chart-container">
                    <canvas id="cgpaChart"></canvas>
                </div>
                <div class="data-table">
                    <h3>Student Marks</h3>
                    <div class="table-container"></div>
                </div>
            `;

            // Process CGPA data for chart
            const cgpaData = data[1].map(sem => sem[1]);
            createCGPAChart(cgpaData);

            // Process subject data for table
            const tableContainer = resultsDiv.querySelector('.table-container');
            if (Array.isArray(data[0])) {
                data[0].forEach((semesterData, index) => {
                    const semDiv = document.createElement('div');
                    semDiv.innerHTML = `
                        <h4>Semester ${index + 1}</h4>
                        ${semesterData}
                        <p>Total marks: ${data[1][index][0]}</p>
                        <p>CGPA: ${data[1][index][1]}</p>
                    `;
                    tableContainer.appendChild(semDiv);
                });
            }
        })
        .catch((error) => {
            console.error("Error fetching student marks:", error);
            const resultsDiv = document.getElementById("results");
            resultsDiv.innerHTML = "An error occurred while fetching the data.";
        });
}


function getSemMarks() {
    //const sem = document.getElementById("semInput").value;
    let sem;
    console.log(document.getElementById("seminput").style.visibility)
    if (document.getElementById("seminput").style.visibility === "hidden" || document.getElementById("seminput").style.visibility === "") {
        console.log("made visible");
        document.getElementById("seminput").style.visibility = "visible";
        return;
    } else {
         sem = document.getElementById("semInput").value;
    }

    const usnprefix = document.getElementById("usnInput").value;
    const branchCode = usnprefix.slice(0, 7); // 1CR15CD

    let apiUrl;
    try {
        apiUrl = `/api/v1/X${branchCode}/${sem}`;
    } catch (error) {
        console.log("Error:", error);
        document.getElementById("seminput").style.visibility = "visible";
        return
    }
    destroyCharts();

    fetch(apiUrl)
        .then((response) => response.json())
        .then((data) => {
            const resultsDiv = document.getElementById("results");
            resultsDiv.innerHTML = `
                <div class="chart-container">
                    <canvas id="subjectChart"></canvas>
                </div>
                <div class="data-table">
                    <h3>Semester Marks</h3>
                    <div class="table-container"></div>
                </div>
            `;
            console.log(data);
            // Create table
            const table = createTableFromData(data[1], data[0]);
            resultsDiv.querySelector('.table-container').appendChild(table);

            // Process data for subject chart
            const subjectData = processSubjectData(data);
            createSubjectChart(subjectData);
        })
        .catch(handleError);
}

function processSubjectData(data) {
    // Implement your data processing logic here
    // Example: return array of { subject: 'Math', average: 85 }
    const columns = data[1].slice(2, -3);
    const subjectAverages = [];

    for (let i = 0; i < columns.length; i += 2) {
        const subject = columns[i].split('_')[0];
        const totalMarks = data[0].reduce((sum, row) => {
            return sum + (parseFloat(row[i + 2]) + parseFloat(row[i + 3]));
        }, 0);

        subjectAverages.push({
            subject: subject,
            average: totalMarks / data[0].length
        });
    }

    return subjectAverages;
}

function handleError(error) {
    console.error("Error:", error);
    const resultsDiv = document.getElementById("results");
    resultsDiv.innerHTML = `<p class="error">Error: ${error.message}</p>`;
}