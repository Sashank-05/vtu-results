 function createTableFromData(columns, data) {
        if (!Array.isArray(columns) || !Array.isArray(data)) {
          console.error("Invalid columns or data format");
          return null;
        }

        let table = document.createElement("table");
        table.border = "1";

        let thead = document.createElement("thead");
        let headerRow = document.createElement("tr");
        columns.forEach((colName) => {
          let th = document.createElement("th");
          th.textContent = colName;
          headerRow.appendChild(th);
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
          row.forEach((cellData) => {
            let td = document.createElement("td");
            td.textContent = cellData;
            tr.appendChild(td);
          });
          tbody.appendChild(tr);
        });
        table.appendChild(tbody);

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
                resultsDiv.innerHTML += `<br><strong>Semester ${
                  index + 1
                }</strong><br>`;
                // Append the HTML content for the semester (assuming it's valid HTML)
                resultsDiv.innerHTML += semesterData;
                resultsDiv.innerHTML += `<h4> Total marks: ${data[1][index][0]}</h4> <p>      <\p>
                  <h4> cgpa: ${data[1][index][1]}</h4>`;
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