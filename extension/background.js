/**
 * Background service worker - polls the local Python trigger server
 * and forwards trigger events to the content script on app.curala tabs.
 */

const POLL_URL = "http://127.0.0.1:59213/poll";
const POLL_INTERVAL_MS = 400;

let polling = false;
let pollTimer = null;

async function pollTrigger() {
  if (polling) return;
  polling = true;

  try {
    const response = await fetch(POLL_URL);
    const data = await response.json();

    if (data.triggered) {
      console.log("[MicButton] Trigger received! Sending to app.curala tabs...");

      const tabs = await chrome.tabs.query({ url: "*://app.curala/*" });
      for (const tab of tabs) {
        try {
          await chrome.tabs.sendMessage(tab.id, { action: "neue_konsultation" });
        } catch (e) {
          console.log("[MicButton] Could not reach tab", tab.id, e.message);
        }
      }

      // If no matching tab is open, open one
      if (tabs.length === 0) {
        console.log("[MicButton] No app.curala tab found, opening one...");
        chrome.tabs.create({ url: "https://app.curala" });
      }
    }
  } catch (e) {
    // Server not running - silently ignore
  } finally {
    polling = false;
  }
}

function startPolling() {
  if (pollTimer) return;
  pollTimer = setInterval(pollTrigger, POLL_INTERVAL_MS);
  console.log("[MicButton] Polling started:", POLL_URL);
}

// Start polling when service worker activates
startPolling();

// Use chrome.alarms to restart polling if service worker was suspended
chrome.alarms.create("keepalive", { periodInMinutes: 0.5 });
chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === "keepalive") {
    startPolling();
    pollTrigger();
  }
});
