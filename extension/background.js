// =============================================================================
// background.js — JobPilot Extension Service Worker
// =============================================================================
// The background service worker handles:
//   1. Listening for messages from popup/content scripts
//   2. Managing extension lifecycle events
//   3. Optional: periodic checks or badge updates
// =============================================================================

// Listen for installation
chrome.runtime.onInstalled.addListener((details) => {
  if (details.reason === "install") {
    console.log("[JobPilot] Extension installed!");
  } else if (details.reason === "update") {
    console.log("[JobPilot] Extension updated to version", chrome.runtime.getManifest().version);
  }
});

// Listen for messages from popup or content scripts
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "GET_AUTH_TOKEN") {
    // Return stored auth token
    chrome.storage.local.get("jobpilot_token", (data) => {
      sendResponse({ token: data.jobpilot_token || null });
    });
    return true; // Keep message channel open for async response
  }

  if (message.type === "CHECK_API_HEALTH") {
    fetch("http://localhost:8000/health")
      .then((res) => res.json())
      .then((data) => sendResponse({ ok: true, data }))
      .catch((err) => sendResponse({ ok: false, error: err.message }));
    return true;
  }
});

// Update badge when auth state changes
chrome.storage.onChanged.addListener((changes, area) => {
  if (area === "local" && changes.jobpilot_token) {
    if (changes.jobpilot_token.newValue) {
      chrome.action.setBadgeText({ text: "✓" });
      chrome.action.setBadgeBackgroundColor({ color: "#22c55e" });
    } else {
      chrome.action.setBadgeText({ text: "" });
    }
  }
});
