/**
 * Content script - runs on app.curala pages.
 * Listens for trigger messages from the background script
 * and clicks the "Neue Konsultation" button.
 */

function clickNeueKonsultation() {
  // Find button by text content
  const buttons = document.querySelectorAll('button[data-slot="button"]');
  for (const btn of buttons) {
    if (btn.textContent.trim().includes("Neue Konsultation")) {
      btn.click();
      console.log("[MicButton] 'Neue Konsultation' button clicked!");
      return true;
    }
  }

  // Fallback: find any button with plus icon and matching text
  const allButtons = document.querySelectorAll("button");
  for (const btn of allButtons) {
    if (btn.textContent.trim().includes("Neue Konsultation")) {
      btn.click();
      console.log("[MicButton] 'Neue Konsultation' button clicked (fallback)!");
      return true;
    }
  }

  console.warn("[MicButton] 'Neue Konsultation' button not found on this page.");
  return false;
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === "neue_konsultation") {
    console.log("[MicButton] Trigger received, clicking button...");
    const success = clickNeueKonsultation();
    sendResponse({ success });
  }
});

console.log("[MicButton] Content script loaded on", window.location.href);
