function createTableFromData(columns, data) {
    if (!Array.isArray(columns) || !Array.isArray(data)) {
        console.error("Invalid columns or data format");
        return null;
    }

    let table = document.createElement("table");
    table.className = "responsive-table striped";

    let thead = document.createElement("thead");
    let headerRow = document.createElement("tr");

    // Add USN and Name headers
    headerRow.innerHTML = '<th>USN</th><th>Name</th>';

    // Process other headers
    const subjectHeaders = columns.slice(2, -3);  // Exclude first two and last three
    for (let i = 0; i < subjectHeaders.length; i += 2) {
        const subject = subjectHeaders[i].split('_')[0];
        headerRow.innerHTML += `<th>${subject} Total</th>`;
    }

    // Add last three headers
    columns.slice(-3).forEach(header => {
        headerRow.innerHTML += `<th>${header}</th>`;
    });

    thead.appendChild(headerRow);
    table.appendChild(thead);

    let tbody = document.createElement("tbody");
    data.forEach((row) => {
        if (!Array.isArray(row)) {
            console.error("Invalid row format:", row);
            return;
        }
        let tr = document.createElement("tr");

        // Add USN and Name
        tr.innerHTML = `<td>${row[0]}</td><td>${row[1]}</td>`;

        // Process and add subject totals
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

        // Add last three columns
        row.slice(-3).forEach(value => {
            tr.innerHTML += `<td>${value}</td>`;
        });

        tbody.appendChild(tr);
    });
    table.appendChild(tbody);

    const tooltip = document.getElementById('tooltip');

    /*table.addEventListener('mouseover', function(e) {
      if (e.target.classList.contains('hoverable')) {
        const internal = e.target.getAttribute('data-internal');
        const external = e.target.getAttribute('data-external');
        e.target.setAttribute('title', `Internal: ${internal}, External: ${external}`);
        tooltip.textContent = `Internal: ${internal}, External: ${external}`;
        tooltip.style.display = 'block';
        tooltip.style.left = `${e.pageX + 10}px`; // Offset by 10px to avoid overlapping
        tooltip.style.top = `${e.pageY + 10}px`;
      }
    });

     */
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
            const tooltipRect = tooltip.getBoundingClientRect();


            let left = e.pageX + 10;
            let top = e.pageY + 10;

            // Ensure tooltip is within table boundaries
            const tableRect = table.getBoundingClientRect();
            const tableRight = tableRect.right;
            const tableBottom = tableRect.bottom;


            tooltip.style.left = `${left}px`;
            tooltip.style.top = `${top}px`;
        }
    });

    table.addEventListener('mouseout', function (e) {
        if (e.target.classList.contains('hoverable')) {
            tooltip.style.display = 'none';
        }
    });

    console.log("Created Table:", table);

    return table;
}

function getSemMarks() {
    const branchCode = document.getElementById("branchDropdown").value;
    const sem = document.getElementById("semDropdown").value;
    const apiUrl = `/api/v1/${branchCode}/${sem}`;

    fetch(apiUrl)
        .then((response) => response.json())
        .then((data) => {
            const resultsDiv = document.getElementById("results");
            resultsDiv.innerHTML = "<h3>Semester Marks:</h3>";
            const table = createTableFromData(data[1], data[0]);
            resultsDiv.appendChild(table);
            console.log(data[1]);
        })
        .catch((error) => {
            const resultsDiv = document.getElementById("results");
            resultsDiv.innerHTML = `<p class="error">Error: ${error.message}</p>`;
            console.error("Error making API request:", error);
        });
}

function getStudentMarks() {
    const usn = document.getElementById("usnInput").value;
    const apiUrl = `/api/v1/student/${usn}`;

    fetch(apiUrl)
        .then((response) => response.json())
        .then((data) => {
            const resultsDiv = document.getElementById("results");
            resultsDiv.innerHTML = "<h3>Student Marks:</h3>";

            // Ensure data[0] exists and is an array
            if (Array.isArray(data[0])) {
                data[0].forEach((semesterData, index) => {
                    // Append semester heading
                    resultsDiv.innerHTML += `<br><strong>Semester ${index + 1}</strong><br>`;
                    // Append the HTML content for the semester (assuming it's valid HTML)
                    resultsDiv.innerHTML += semesterData;
                    resultsDiv.innerHTML += `<h4>Total marks: ${data[1][index][0]}</h4>
            <h4>CGPA: ${data[1][index][1]}</h4><br>`;
                });
            } else {
                resultsDiv.innerHTML += "No data found for this student.";
            }

            console.log("API Response 1:", data[0]);
            console.log("API RESPONSE 2:", data[1]);
        })
        .catch((error) => {
            console.error("Error fetching student marks:", error);
            const resultsDiv = document.getElementById("results");
            resultsDiv.innerHTML = "An error occurred while fetching the data.";
        });
}

// Initialize Materialize components
document.addEventListener('DOMContentLoaded', function () {
    var elems = document.querySelectorAll('select');
    var instances = M.FormSelect.init(elems);
});