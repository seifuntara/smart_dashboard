/* ============================
   SCREEN CONTEXT (PHASE 1)
============================ */

let currentView = "assistant";
let selectedRole = "agent";

document
  .querySelectorAll('button[data-bs-toggle="tab"]')
  .forEach(btn => {
    btn.addEventListener("shown.bs.tab", e => {
      currentView = e.target.textContent.trim().toLowerCase();
      console.log("Current view:", currentView);
    });
  });

// Role buttons rendered in the chat area
document.addEventListener("DOMContentLoaded", () => {
  const roleButtons = document.getElementById("roleButtons");
  if (!roleButtons) return;

  // Initialize visual selection
  roleButtons.querySelectorAll("button[data-role]").forEach(btn => {
    if (btn.getAttribute("data-role") === selectedRole) {
      btn.classList.remove("btn-outline-primary");
      btn.classList.add("btn-primary");
    }
  });

  roleButtons.querySelectorAll("button[data-role]").forEach(btn => {
    btn.addEventListener("click", (e) => {
      const role = e.currentTarget.getAttribute("data-role");
      selectedRole = role;
      console.log("Selected chat role:", selectedRole);

      // Update button styles
      roleButtons.querySelectorAll("button[data-role]").forEach(b => {
        b.classList.remove("btn-primary");
        b.classList.add("btn-outline-primary");
      });
      e.currentTarget.classList.remove("btn-outline-primary");
      e.currentTarget.classList.add("btn-primary");

      // Acknowledge selection in chat
      addBotMessage(`Role set to ${role.charAt(0).toUpperCase() + role.slice(1)}.`);
    });
  });
});

/* ============================
   CHAT INPUT HANDLERS
============================ */

function handleEnter(e) {
  if (e.key === "Enter") {
    e.preventDefault();
    sendMessage();
  }
}

function quickSend(text) {
  const input = document.getElementById("userInput");
  input.value = text;
  sendMessage();
}

/* ============================
   MESSAGE RENDERING
============================ */

function addUserMessage(text) {
  const messages = document.getElementById("messages");
  const div = document.createElement("div");
  div.className = "user-message";
  div.textContent = text;
  messages.appendChild(div);
  messages.scrollTop = messages.scrollHeight;
}

function addBotMessage(text) {
  const messages = document.getElementById("messages");
  const div = document.createElement("div");
  div.className = "bot-message";
  div.textContent = text;
  messages.appendChild(div);
  messages.scrollTop = messages.scrollHeight;
}

/* ============================
   SEND MESSAGE
============================ */

async function sendMessage() {
  const input = document.getElementById("userInput");
  const message = input.value.trim();
  if (!message) return;

  // Show user message
  addUserMessage(message);
  input.value = "";

  // Show typing indicator
  const typing = document.getElementById("typing");
  typing.classList.remove("d-none");

  try {
    const response = await fetch("/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        message: message,
        context: {
          view: currentView,
          role: selectedRole,
          what_if: window.currentWhatIf || null
        }
      })
    });

    const data = await response.json();

    // Hide typing indicator
    typing.classList.add("d-none");

    // Render bot reply
    if (data.reply) {
      addBotMessage(data.reply);
    } else {
      addBotMessage("I didn't understand that. Please try again.");
    }

  } catch (error) {
    typing.classList.add("d-none");
    console.error("Chat error:", error);
    addBotMessage("Something went wrong. Please try again.");
  }
}
