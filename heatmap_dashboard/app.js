async function loadHeatmap() {

    console.log("Loading heatmap...");

    const response = await fetch("http://localhost:8000/heatmap/");

    const data = await response.json();
    const details = data.details || {};

console.log("Heatmap data:", data);
console.log("Details:", details);

    const div = document.getElementById("heatmap");

    div.innerHTML = "";

    // Add empty top-left corner
    const blank = document.createElement("div");
    blank.className = "cell";
    blank.style.background = "white";
    blank.style.border = "none";
    div.appendChild(blank);

    // Add column labels
    for (let i = 0; i < data.cols; i++) {

    const label = document.createElement("div");

    label.className = "cell";

    label.innerHTML = "<b>P" + (i + 1) + "</b>";

    label.style.background = "white";
    label.style.border = "none";

    div.appendChild(label);

}

    data.grid.forEach((row, rowIndex) => {

    const rowLabel = document.createElement("div");

    rowLabel.className = "cell";

    rowLabel.innerHTML = "<b>R" + (rowIndex + 1) + "</b>";

    rowLabel.style.background = "white";
    rowLabel.style.border = "none";

    div.appendChild(rowLabel);

        row.forEach((value, colIndex) => {

            const cell = document.createElement("div");

            cell.className = "cell";

            cell.innerHTML = "🌱";

            cell.title = "Severity : " + value.toFixed(1) + "%";

            cell.addEventListener("click", () => {

    const key = `${rowIndex}_${colIndex}`;
const info = details[key];

console.log("Clicked:", key);
console.log("Info:", info);

    let status = "";

    if (value === 0)
        status = "Healthy";
    else if (value <= 30)
        status = "Mild Infection";
    else if (value <= 60)
        status = "Moderate Infection";
    else
        status = "Severe Infection";

    document.getElementById("infoBox").innerHTML = `
    <h2>🌱 Plant Information</h2>

    <p><b>Plant ID:</b> R${rowIndex + 1} - P${colIndex + 1}</p>

    <p><b>Disease:</b> ${info ? info.disease : "Healthy"}</p>

    <p><b>Confidence:</b> ${info ? info.confidence.toFixed(2) + "%" : "--"}</p>

    <p><b>Severity:</b> ${value.toFixed(1)}%</p>

    <p><b>Status:</b> ${status}</p>

    <p><b>Image:</b> ${info && info.image ? "Available" : "Not Available"}</p>
`;

});

            if (value === 0) {
                cell.style.background = "#4CAF50";
            }
            else if (value <= 30) {
                cell.style.background = "#FFD54F";
            }
            else if (value <= 60) {
                cell.style.background = "#FB8C00";
            }
            else {
                cell.style.background = "#E53935";
            }

            cell.style.color = "black";
            cell.style.fontWeight = "bold";

            div.appendChild(cell);

        });

    });

}

loadHeatmap();