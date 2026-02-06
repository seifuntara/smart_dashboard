/* ============================
   SCREEN CONTEXT (PHASE 1)
============================ */

let currentView = "assistant";

document
  .querySelectorAll('button[data-bs-toggle="tab"]')
  .forEach(btn => {
    btn.addEventListener("shown.bs.tab", e => {
      currentView = e.target.textContent.trim().toLowerCase();
      console.log("Current view:", currentView);
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
          view: currentView
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
