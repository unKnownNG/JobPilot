// =============================================================================
// content.js — JobPilot Content Script
// =============================================================================
// This script is injected into every web page. It stays mostly dormant until
// the popup sends a message asking it to scan or fill form fields.
//
// NOTE: The actual scan/fill logic is executed via chrome.scripting.executeScript
// from popup.js for better reliability. This content script serves as a
// communication bridge and provides visual feedback.
// =============================================================================

// Listen for messages from the popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "PING") {
    sendResponse({ status: "alive" });
    return;
  }

  if (message.type === "HIGHLIGHT_FIELDS") {
    // Highlight all form fields on the page for visual feedback
    const fields = document.querySelectorAll(
      'input:not([type="hidden"]):not([type="submit"]), select, textarea'
    );
    fields.forEach((el) => {
      el.style.outline = "2px solid rgba(99, 102, 241, 0.6)";
      el.style.outlineOffset = "2px";
      setTimeout(() => {
        el.style.outline = "";
        el.style.outlineOffset = "";
      }, 3000);
    });
    sendResponse({ highlighted: fields.length });
    return;
  }
});

// Notify that content script is loaded (useful for debugging)
console.log("[JobPilot] Content script loaded on:", window.location.href);
