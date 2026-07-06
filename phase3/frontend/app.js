const state = {
  backendUrl: localStorage.getItem("phase3_backend_url") || "http://localhost:8000",
  token: sessionStorage.getItem("phase3_token") || "",
  inventory: [],
  importRows: [],
};

const els = {
  backendUrl: document.getElementById("backendUrl"),
  username: document.getElementById("username"),
  password: document.getElementById("password"),
  loginButton: document.getElementById("loginButton"),
  connectionStatus: document.getElementById("connectionStatus"),
  totalItems: document.getElementById("totalItems"),
  lowStockItems: document.getElementById("lowStockItems"),
  expiredItems: document.getElementById("expiredItems"),
  nearExpiryItems: document.getElementById("nearExpiryItems"),
  inventoryForm: document.getElementById("inventoryForm"),
  itemId: document.getElementById("itemId"),
  medicineName: document.getElementById("medicineName"),
  stockQuantity: document.getElementById("stockQuantity"),
  pricePerKg: document.getElementById("pricePerKg"),
  expiryDate: document.getElementById("expiryDate"),
  formTitle: document.getElementById("formTitle"),
  resetFormButton: document.getElementById("resetFormButton"),
  searchInput: document.getElementById("searchInput"),
  refreshButton: document.getElementById("refreshButton"),
  inventoryTable: document.getElementById("inventoryTable"),
  csvFile: document.getElementById("csvFile"),
  importButton: document.getElementById("importButton"),
  importPreview: document.getElementById("importPreview"),
  downloadSampleButton: document.getElementById("downloadSampleButton"),
  activityLog: document.getElementById("activityLog"),
};

els.backendUrl.value = state.backendUrl;

function normalizeName(value) {
  return value.trim().toLowerCase().replace(/\s+/g, " ");
}

function log(message) {
  const timestamp = new Date().toLocaleTimeString();
  els.activityLog.textContent = `[${timestamp}] ${message}\n${els.activityLog.textContent}`;
}

function setStatus(text, kind = "") {
  els.connectionStatus.textContent = text;
  els.connectionStatus.className = `status-pill ${kind}`.trim();
}

function backendUrl() {
  return els.backendUrl.value.trim().replace(/\/$/, "");
}

async function api(path, options = {}) {
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };
  if (state.token) {
    headers.Authorization = `Bearer ${state.token}`;
  }
  const response = await fetch(`${backendUrl()}${path}`, {
    ...options,
    headers,
  });
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const payload = await response.json();
      detail = payload.detail || JSON.stringify(payload);
    } catch {
      detail = await response.text();
    }
    throw new Error(`${response.status} ${detail}`);
  }
  if (response.status === 204) {
    return null;
  }
  return response.json();
}

async function login() {
  state.backendUrl = backendUrl();
  localStorage.setItem("phase3_backend_url", state.backendUrl);
  const payload = {
    username: els.username.value.trim(),
    password: els.password.value,
  };
  const result = await api("/auth/login", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  state.token = result.access_token;
  sessionStorage.setItem("phase3_token", state.token);
  setStatus(`Connected as ${result.role}`, "ok");
  log("Login successful.");
  await refreshInventory();
}

function itemStatus(item) {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const expiry = new Date(`${item.expiry_date}T00:00:00`);
  const days = Math.ceil((expiry - today) / 86400000);
  if (days < 0) {
    return { text: "Expired", className: "danger" };
  }
  if (days <= 30) {
    return { text: "Near expiry", className: "warn" };
  }
  if (Number(item.stock_quantity_kg) <= 1) {
    return { text: "Low stock", className: "warn" };
  }
  return { text: "Ready", className: "ok" };
}

function renderSummary() {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  let lowStock = 0;
  let expired = 0;
  let nearExpiry = 0;
  for (const item of state.inventory) {
    const expiry = new Date(`${item.expiry_date}T00:00:00`);
    const days = Math.ceil((expiry - today) / 86400000);
    if (Number(item.stock_quantity_kg) <= 1) {
      lowStock += 1;
    }
    if (days < 0) {
      expired += 1;
    } else if (days <= 30) {
      nearExpiry += 1;
    }
  }
  els.totalItems.textContent = state.inventory.length;
  els.lowStockItems.textContent = lowStock;
  els.expiredItems.textContent = expired;
  els.nearExpiryItems.textContent = nearExpiry;
}

function renderInventory() {
  const query = normalizeName(els.searchInput.value);
  const rows = state.inventory.filter((item) =>
    normalizeName(item.medicine_name).includes(query),
  );
  els.inventoryTable.innerHTML = "";
  for (const item of rows) {
    const status = itemStatus(item);
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${escapeHtml(item.medicine_name)}</td>
      <td>${Number(item.stock_quantity_kg).toFixed(2)}</td>
      <td>INR ${Number(item.price_per_kg).toFixed(2)}</td>
      <td>${item.expiry_date}</td>
      <td><span class="status ${status.className}">${status.text}</span></td>
      <td>
        <div class="row-actions">
          <button type="button" class="secondary" data-action="edit" data-id="${item.id}">Edit</button>
          <button type="button" class="secondary" data-action="delete" data-id="${item.id}">Delete</button>
        </div>
      </td>
    `;
    els.inventoryTable.appendChild(row);
  }
  if (rows.length === 0) {
    const row = document.createElement("tr");
    row.innerHTML = `<td colspan="6">No inventory items found.</td>`;
    els.inventoryTable.appendChild(row);
  }
  renderSummary();
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function refreshInventory() {
  state.inventory = await api("/inventory");
  state.inventory.sort((a, b) => a.medicine_name.localeCompare(b.medicine_name));
  renderInventory();
  log(`Loaded ${state.inventory.length} inventory item(s).`);
}

function readForm() {
  return {
    medicine_name: els.medicineName.value.trim(),
    stock_quantity_kg: Number(els.stockQuantity.value),
    price_per_kg: Number(els.pricePerKg.value),
    expiry_date: els.expiryDate.value,
  };
}

function fillForm(item) {
  els.itemId.value = item.id;
  els.medicineName.value = item.medicine_name;
  els.stockQuantity.value = item.stock_quantity_kg;
  els.pricePerKg.value = item.price_per_kg;
  els.expiryDate.value = item.expiry_date;
  els.formTitle.textContent = "Edit medicine";
  els.medicineName.focus();
}

function clearForm() {
  els.itemId.value = "";
  els.inventoryForm.reset();
  els.formTitle.textContent = "Add medicine";
}

async function saveForm(event) {
  event.preventDefault();
  const payload = readForm();
  const itemId = els.itemId.value;
  if (itemId) {
    await api(`/inventory/${itemId}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    });
    log(`Updated ${payload.medicine_name}.`);
  } else {
    await api("/inventory", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    log(`Added ${payload.medicine_name}.`);
  }
  clearForm();
  await refreshInventory();
}

async function deleteItem(id) {
  const item = state.inventory.find((candidate) => String(candidate.id) === String(id));
  if (!item) {
    return;
  }
  const confirmed = window.confirm(`Delete ${item.medicine_name}?`);
  if (!confirmed) {
    return;
  }
  await api(`/inventory/${id}`, { method: "DELETE" });
  log(`Deleted ${item.medicine_name}.`);
  await refreshInventory();
}

function parseDelimited(text) {
  const lines = text
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);
  if (lines.length < 2) {
    return [];
  }
  const delimiter = lines[0].includes("\t") ? "\t" : ",";
  const headers = splitRow(lines[0], delimiter).map((header) => normalizeName(header));
  return lines.slice(1).map((line, index) => {
    const values = splitRow(line, delimiter);
    const row = {};
    headers.forEach((header, columnIndex) => {
      row[header] = values[columnIndex] ? values[columnIndex].trim() : "";
    });
    return {
      rowNumber: index + 2,
      medicine_name: row.medicine_name || "",
      stock_quantity_kg: Number(row.stock_quantity_kg),
      price_per_kg: Number(row.price_per_kg),
      expiry_date: row.expiry_date || "",
    };
  });
}

function splitRow(line, delimiter) {
  const values = [];
  let current = "";
  let quoted = false;
  for (let index = 0; index < line.length; index += 1) {
    const char = line[index];
    if (char === '"') {
      quoted = !quoted;
    } else if (char === delimiter && !quoted) {
      values.push(current);
      current = "";
    } else {
      current += char;
    }
  }
  values.push(current);
  return values;
}

function validateImportRows(rows) {
  const errors = [];
  for (const row of rows) {
    if (!row.medicine_name) {
      errors.push(`Row ${row.rowNumber}: medicine_name is required.`);
    }
    if (!Number.isFinite(row.stock_quantity_kg) || row.stock_quantity_kg < 0) {
      errors.push(`Row ${row.rowNumber}: stock_quantity_kg must be 0 or greater.`);
    }
    if (!Number.isFinite(row.price_per_kg) || row.price_per_kg < 0) {
      errors.push(`Row ${row.rowNumber}: price_per_kg must be 0 or greater.`);
    }
    if (!/^\d{4}-\d{2}-\d{2}$/.test(row.expiry_date)) {
      errors.push(`Row ${row.rowNumber}: expiry_date must use YYYY-MM-DD.`);
    }
  }
  return errors;
}

async function handleCsvFile() {
  const file = els.csvFile.files[0];
  if (!file) {
    state.importRows = [];
    els.importPreview.textContent = "No file selected.";
    return;
  }
  const text = await file.text();
  const rows = parseDelimited(text);
  const errors = validateImportRows(rows);
  state.importRows = rows;
  if (errors.length > 0) {
    els.importPreview.textContent = errors.join("\n");
    return;
  }
  els.importPreview.textContent = rows
    .slice(0, 8)
    .map((row) => `${row.medicine_name} | ${row.stock_quantity_kg} kg | INR ${row.price_per_kg} | ${row.expiry_date}`)
    .join("\n") || "No rows found.";
}

async function importRows() {
  const errors = validateImportRows(state.importRows);
  if (errors.length > 0) {
    els.importPreview.textContent = errors.join("\n");
    return;
  }
  if (state.importRows.length === 0) {
    log("No CSV rows to import.");
    return;
  }
  let created = 0;
  let updated = 0;
  for (const row of state.importRows) {
    const existing = state.inventory.find(
      (item) => normalizeName(item.medicine_name) === normalizeName(row.medicine_name),
    );
    const payload = {
      medicine_name: row.medicine_name,
      stock_quantity_kg: row.stock_quantity_kg,
      price_per_kg: row.price_per_kg,
      expiry_date: row.expiry_date,
    };
    if (existing) {
      await api(`/inventory/${existing.id}`, {
        method: "PUT",
        body: JSON.stringify(payload),
      });
      updated += 1;
    } else {
      await api("/inventory", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      created += 1;
    }
  }
  log(`Import finished. Created ${created}, updated ${updated}.`);
  await refreshInventory();
}

function downloadSampleCsv() {
  const csv = [
    "medicine_name,stock_quantity_kg,price_per_kg,expiry_date",
    "Mancozeb 75% WP,15,220,2026-11-05",
    "Metalaxyl + Mancozeb,8,460,2026-12-15",
    "Neem Cake,40,45,2027-05-01",
  ].join("\n");
  const url = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
  const link = document.createElement("a");
  link.href = url;
  link.download = "inventory_sample.csv";
  link.click();
  URL.revokeObjectURL(url);
}

els.loginButton.addEventListener("click", () => {
  login().catch((error) => {
    setStatus("Connection failed", "error");
    log(`Login failed: ${error.message}`);
  });
});

els.refreshButton.addEventListener("click", () => {
  refreshInventory().catch((error) => log(`Refresh failed: ${error.message}`));
});

els.inventoryForm.addEventListener("submit", (event) => {
  saveForm(event).catch((error) => log(`Save failed: ${error.message}`));
});

els.resetFormButton.addEventListener("click", clearForm);
els.searchInput.addEventListener("input", renderInventory);
els.csvFile.addEventListener("change", () => {
  handleCsvFile().catch((error) => log(`CSV read failed: ${error.message}`));
});
els.importButton.addEventListener("click", () => {
  importRows().catch((error) => log(`Import failed: ${error.message}`));
});
els.downloadSampleButton.addEventListener("click", downloadSampleCsv);

els.inventoryTable.addEventListener("click", (event) => {
  const button = event.target.closest("button[data-action]");
  if (!button) {
    return;
  }
  if (button.dataset.action === "edit") {
    const item = state.inventory.find((candidate) => String(candidate.id) === button.dataset.id);
    if (item) {
      fillForm(item);
    }
  }
  if (button.dataset.action === "delete") {
    deleteItem(button.dataset.id).catch((error) => log(`Delete failed: ${error.message}`));
  }
});

if (state.token) {
  setStatus("Token restored", "ok");
  refreshInventory().catch(() => setStatus("Login required", ""));
}
