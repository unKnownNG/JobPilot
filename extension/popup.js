// =============================================================================
// popup.js — JobPilot Extension Popup Logic
// =============================================================================
// This file handles:
//   1. Login / logout (stores JWT token in chrome.storage)
//   2. Scanning form fields on the active tab (via content script)
//   3. Sending fields to backend for AI analysis
//   4. Triggering the content script to fill the form
//   5. Logging the application to the dashboard
// =============================================================================

const API_BASE = "http://localhost:8000/api";

// ─── DOM Elements ──────────────────────────────────────────────────────────
const $ = (id) => document.getElementById(id);
const loginScreen  = $("login-screen");
const mainScreen   = $("main-screen");
const loginForm    = $("login-form");
const loginBtn     = $("login-btn");
const loginError   = $("login-error");
const userEmail    = $("user-email");
const logoutBtn    = $("logout-btn");
const pageTitle    = $("page-title");
const pageUrl      = $("page-url");
const scanBtn      = $("scan-btn");
const scanResult   = $("scan-result");
const fieldCount   = $("field-count");
const scanStatus   = $("scan-status");
const fieldsPreview = $("fields-preview");
const fillBtn      = $("fill-btn");
const fillResult   = $("fill-result");
const fillSummary  = $("fill-summary");
const fillDetails  = $("fill-details");
const logBtn       = $("log-btn");
const statusBar    = $("status-bar");
const statusMsg    = $("status-message");

// ─── State ─────────────────────────────────────────────────────────────────
let authToken = null;
let scannedFields = [];
let lastFillResult = null;
let currentTabInfo = { url: "", title: "" };


// ─── Helpers ───────────────────────────────────────────────────────────────

function showStatus(message, type = "info") {
  statusMsg.textContent = message;
  statusBar.className = `status-bar ${type}`;
  statusBar.classList.remove("hidden");
  setTimeout(() => statusBar.classList.add("hidden"), 4000);
}

function setButtonLoading(btn, loading) {
  const text = btn.querySelector(".btn-text");
  const load = btn.querySelector(".btn-loading");
  if (text) text.classList.toggle("hidden", loading);
  if (load) load.classList.toggle("hidden", !loading);
  btn.disabled = loading;
}

async function apiRequest(endpoint, options = {}) {
  const headers = {
    "Content-Type": "application/json",
    ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}),
  };
  const res = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });
  if (res.status === 401) {
    // Token expired — force re-login
    await chrome.storage.local.remove("jobpilot_token");
    authToken = null;
    showScreen("login");
    throw new Error("Session expired. Please sign in again.");
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `API error ${res.status}`);
  }
  // Handle 204 No Content
  if (res.status === 204) return null;
  return res.json();
}


// ─── Screen Management ─────────────────────────────────────────────────────

function showScreen(screen) {
  loginScreen.classList.toggle("hidden", screen !== "login");
  mainScreen.classList.toggle("hidden", screen !== "main");
}


// ─── Auth ──────────────────────────────────────────────────────────────────

async function checkAuth() {
  const data = await chrome.storage.local.get("jobpilot_token");
  if (data.jobpilot_token) {
    authToken = data.jobpilot_token;
    try {
      // Verify token is still valid
      const me = await apiRequest("/auth/me");
      userEmail.textContent = me.email;
      showScreen("main");
      loadCurrentTab();
    } catch {
      authToken = null;
      showScreen("login");
    }
  } else {
    showScreen("login");
  }
}

loginForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  loginError.classList.add("hidden");
  setButtonLoading(loginBtn, true);

  try {
    const email = $("email").value;
    const password = $("password").value;

    const res = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Login failed");
    }

    const data = await res.json();
    authToken = data.access_token;
    await chrome.storage.local.set({ jobpilot_token: authToken });

    userEmail.textContent = email;
    showScreen("main");
    loadCurrentTab();
  } catch (err) {
    loginError.textContent = err.message;
    loginError.classList.remove("hidden");
  } finally {
    setButtonLoading(loginBtn, false);
  }
});

logoutBtn.addEventListener("click", async () => {
  await chrome.storage.local.remove("jobpilot_token");
  authToken = null;
  showScreen("login");
});


// ─── Tab Info ──────────────────────────────────────────────────────────────

async function loadCurrentTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (tab) {
    currentTabInfo = { url: tab.url || "", title: tab.title || "" };
    pageTitle.textContent = tab.title || "Unknown Page";
    pageUrl.textContent = tab.url || "";
  }
}


// ─── Scan Form Fields ──────────────────────────────────────────────────────

scanBtn.addEventListener("click", async () => {
  scanBtn.disabled = true;
  scanBtn.textContent = "Scanning...";
  scanBtn.classList.add("loading");

  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

    // Inject and run the content script's scan function
    const results = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: scanFormFields,
    });

    const fields = results[0]?.result || [];
    scannedFields = fields;

    if (fields.length === 0) {
      showStatus("No form fields found on this page.", "error");
      scanBtn.disabled = false;
      scanBtn.textContent = "Scan Form Fields";
      scanBtn.classList.remove("loading");
      return;
    }

    // Show results
    fieldCount.textContent = `${fields.length} fields`;
    scanStatus.textContent = "Scanned ✓";
    fieldsPreview.innerHTML = fields
      .map((f) => `<span class="field-tag">${f.label || f.name || f.selector}</span>`)
      .join("");
    scanResult.classList.remove("hidden");
    fillBtn.classList.remove("hidden");
    fillBtn.disabled = false;

    showStatus(`Found ${fields.length} form fields!`, "success");
  } catch (err) {
    showStatus(`Scan failed: ${err.message}`, "error");
  } finally {
    scanBtn.disabled = false;
    scanBtn.innerHTML = `
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
        <circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/>
      </svg>
      Scan Form Fields
    `;
    scanBtn.classList.remove("loading");
  }
});


// ─── Auto-Fill Form ────────────────────────────────────────────────────────

fillBtn.addEventListener("click", async () => {
  setButtonLoading(fillBtn, true);

  try {
    // Extract job context from page title/URL
    const jobTitle = currentTabInfo.title || "";
    const company = extractCompany(currentTabInfo.url);

    // Send to backend for AI analysis
    const result = await apiRequest("/agents/applier/analyze-form", {
      method: "POST",
      body: JSON.stringify({
        form_fields: scannedFields,
        job_url: currentTabInfo.url,
        job_title: jobTitle,
        company: company,
        job_description: "",
      }),
    });

    lastFillResult = result;

    if (result.error) {
      showStatus(`AI analysis failed: ${result.summary || "Unknown error"}`, "error");
      return;
    }

    const mappings = result.field_mappings || [];
    if (mappings.length === 0) {
      showStatus("AI could not map any fields.", "error");
      return;
    }

    // Send fill instructions to the content script
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: fillFormFields,
      args: [mappings],
    });

    // Show fill results
    fillSummary.textContent = result.summary || `Filled ${mappings.length} fields`;
    fillDetails.innerHTML = mappings
      .map(
        (m) => `
        <div class="fill-row">
          <span class="fill-confidence ${m.confidence || "medium"}"></span>
          <span class="fill-field">${m.selector}</span>
          <span class="fill-value">${truncate(String(m.value || ""), 30)}</span>
        </div>`
      )
      .join("");
    fillResult.classList.remove("hidden");

    showStatus(`Filled ${mappings.length} fields! Review and submit.`, "success");
  } catch (err) {
    showStatus(`Fill failed: ${err.message}`, "error");
  } finally {
    setButtonLoading(fillBtn, false);
  }
});


// ─── Log Application ──────────────────────────────────────────────────────

logBtn.addEventListener("click", async () => {
  logBtn.disabled = true;
  logBtn.textContent = "Logging...";

  try {
    const filledFields = (lastFillResult?.field_mappings || [])
      .filter((m) => m.value)
      .map((m) => m.selector);

    await apiRequest("/agents/applier/log", {
      method: "POST",
      body: JSON.stringify({
        job_url: currentTabInfo.url,
        job_title: currentTabInfo.title,
        company: extractCompany(currentTabInfo.url),
        status: "applied",
        fields_filled: filledFields,
        notes: lastFillResult?.summary || "Applied via Chrome Extension",
      }),
    });

    showStatus("Application logged to dashboard! ✅", "success");
    logBtn.textContent = "Logged ✓";
  } catch (err) {
    showStatus(`Log failed: ${err.message}`, "error");
    logBtn.disabled = false;
    logBtn.textContent = "Log Application";
  }
});


// ─── Utility Functions ─────────────────────────────────────────────────────

function extractCompany(url) {
  try {
    const host = new URL(url).hostname;
    // Try to extract company from common job site URL patterns
    if (host.includes("greenhouse.io")) return host.split(".greenhouse.io")[0];
    if (host.includes("lever.co")) return host.split(".lever.co")[0];
    if (host.includes("workday.com")) return host.split(".")[0];
    if (host.includes("myworkdayjobs.com")) return host.split(".")[0];
    return host.replace("www.", "").split(".")[0];
  } catch {
    return "";
  }
}

function truncate(str, len) {
  return str.length > len ? str.substring(0, len) + "…" : str;
}


// =============================================================================
// Functions injected into the active tab via chrome.scripting.executeScript
// These run in the PAGE context, not the extension context.
// =============================================================================

/**
 * Scans the active page for all form fields and returns a structured array.
 * This function is injected into the tab — it reads the DOM directly.
 */
function scanFormFields() {
  const fields = [];
  const seen = new Set();

  // Find all interactive form elements
  const elements = document.querySelectorAll(
    'input:not([type="hidden"]):not([type="submit"]):not([type="button"]):not([type="reset"]), ' +
    'select, textarea'
  );

  elements.forEach((el, i) => {
    // Skip invisible elements
    const rect = el.getBoundingClientRect();
    if (rect.width === 0 && rect.height === 0) return;
    const style = window.getComputedStyle(el);
    if (style.display === "none" || style.visibility === "hidden") return;

    // Build a robust CSS selector
    let selector = "";
    if (el.id) {
      selector = `#${el.id}`;
    } else if (el.name) {
      selector = `[name="${el.name}"]`;
    } else {
      selector = `${el.tagName.toLowerCase()}:nth-of-type(${i + 1})`;
    }

    if (seen.has(selector)) return;
    seen.add(selector);

    // Find the label
    let label = "";
    if (el.id) {
      const labelEl = document.querySelector(`label[for="${el.id}"]`);
      if (labelEl) label = labelEl.textContent.trim();
    }
    if (!label && el.closest("label")) {
      label = el.closest("label").textContent.trim();
    }
    if (!label && el.getAttribute("aria-label")) {
      label = el.getAttribute("aria-label");
    }
    if (!label && el.placeholder) {
      label = el.placeholder;
    }

    // Get options for select elements
    let options = null;
    if (el.tagName === "SELECT") {
      options = Array.from(el.options).map((opt) => ({
        value: opt.value,
        label: opt.textContent.trim(),
      }));
    }

    // Determine field type
    let fieldType = el.tagName.toLowerCase();
    if (fieldType === "input") {
      fieldType = el.type || "text";
    }

    fields.push({
      selector,
      field_type: fieldType,
      name: el.name || "",
      label: label.substring(0, 100), // Truncate long labels
      placeholder: el.placeholder || "",
      required: el.required || el.getAttribute("aria-required") === "true",
      options,
    });
  });

  return fields;
}


/**
 * Fills form fields using the AI-generated mappings.
 * This function is injected into the tab.
 * @param {Array} mappings - Array of {selector, field_type, value}
 */
function fillFormFields(mappings) {
  let filled = 0;

  mappings.forEach((mapping) => {
    if (!mapping.value || mapping.value === "__RESUME_UPLOAD__") return;

    try {
      const el = document.querySelector(mapping.selector);
      if (!el) return;

      const fieldType = mapping.field_type || "text";

      if (fieldType === "select" || el.tagName === "SELECT") {
        // Handle dropdown
        el.value = mapping.value;
        el.dispatchEvent(new Event("change", { bubbles: true }));
      } else if (fieldType === "radio") {
        // Handle radio buttons
        const radio = document.querySelector(
          `input[type="radio"][name="${el.name}"][value="${mapping.value}"]`
        );
        if (radio) {
          radio.checked = true;
          radio.dispatchEvent(new Event("change", { bubbles: true }));
        }
      } else if (fieldType === "checkbox") {
        // Handle checkboxes
        if (mapping.value === "true" || mapping.value === true) {
          el.checked = true;
        }
        el.dispatchEvent(new Event("change", { bubbles: true }));
      } else {
        // Handle text inputs and textareas
        // Use the native input value setter to work with React/Angular
        const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
          window.HTMLInputElement.prototype, "value"
        )?.set;
        const nativeTextareaValueSetter = Object.getOwnPropertyDescriptor(
          window.HTMLTextAreaElement.prototype, "value"
        )?.set;

        if (el.tagName === "TEXTAREA" && nativeTextareaValueSetter) {
          nativeTextareaValueSetter.call(el, mapping.value);
        } else if (nativeInputValueSetter) {
          nativeInputValueSetter.call(el, mapping.value);
        } else {
          el.value = mapping.value;
        }

        // Dispatch events that React/Angular/Vue listen for
        el.dispatchEvent(new Event("input", { bubbles: true }));
        el.dispatchEvent(new Event("change", { bubbles: true }));
        el.dispatchEvent(new Event("blur", { bubbles: true }));
      }

      // Visual feedback: briefly highlight filled fields
      const origBg = el.style.backgroundColor;
      el.style.backgroundColor = "rgba(34, 197, 94, 0.15)";
      el.style.transition = "background-color 0.3s";
      setTimeout(() => {
        el.style.backgroundColor = origBg;
      }, 2000);

      filled++;
    } catch (err) {
      console.warn(`[JobPilot] Failed to fill ${mapping.selector}:`, err);
    }
  });

  return filled;
}


// ─── Init ──────────────────────────────────────────────────────────────────
checkAuth();
