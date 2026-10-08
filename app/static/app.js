/**
 * Pragya GPT By Shantikunj - Frontend Application Logic
 * WhatsApp style chat interface communicating with /api/chat
 */

document.addEventListener("DOMContentLoaded", () => {
  // Elements
  const deviceFrame = document.getElementById("deviceFrame");
  const togglePhoneBtn = document.getElementById("togglePhoneBtn");
  const toggleFullBtn = document.getElementById("toggleFullBtn");
  const toggleThemeBtn = document.getElementById("toggleThemeBtn");
  const currentTimeEl = document.getElementById("currentTime");
  const headerStatusEl = document.getElementById("headerStatus");
  const chatArea = document.getElementById("chatArea");
  const messagesContainer = document.getElementById("messagesContainer");
  const typingIndicator = document.getElementById("typingIndicator");
  const messageInput = document.getElementById("messageInput");
  const sendBtn = document.getElementById("sendBtn");
  const suggestionItems = document.querySelectorAll(".suggestion-item");

  let conversationId = "conv_" + Math.random().toString(36).substring(2, 10);
  let isSending = false;

  // Set Emerald Theme by default matching reference artwork & screenshot
  document.body.classList.add("emerald-theme");

  // 1. Time Update
  function updateClock() {
    const now = new Date();
    const hours = now.getHours().toString().padStart(2, "0");
    const minutes = now.getMinutes().toString().padStart(2, "0");
    if (currentTimeEl) {
      currentTimeEl.textContent = `${hours}:${minutes}`;
    }
  }
  updateClock();
  setInterval(updateClock, 30000);

  function getFormattedTime() {
    const now = new Date();
    let hours = now.getHours();
    let minutes = now.getMinutes();
    const ampm = hours >= 12 ? "PM" : "AM";
    hours = hours % 12;
    hours = hours ? hours : 12;
    minutes = minutes < 10 ? "0" + minutes : minutes;
    return `${hours}:${minutes} ${ampm}`;
  }

  // 2. View Mode & Theme Toggling
  if (toggleThemeBtn) {
    toggleThemeBtn.addEventListener("click", () => {
      const isEmerald = document.body.classList.toggle("emerald-theme");
      toggleThemeBtn.textContent = isEmerald ? "🌿 Emerald Theme" : "☀️ Classic Theme";
      toggleThemeBtn.classList.toggle("active", isEmerald);
    });
  }

  if (togglePhoneBtn && toggleFullBtn && deviceFrame) {
    togglePhoneBtn.addEventListener("click", () => {
      deviceFrame.classList.remove("full-view");
      togglePhoneBtn.classList.add("active");
      toggleFullBtn.classList.remove("active");
    });

    toggleFullBtn.addEventListener("click", () => {
      deviceFrame.classList.add("full-view");
      toggleFullBtn.classList.add("active");
      togglePhoneBtn.classList.remove("active");
    });
  }

  // 3. Smooth Auto-Scroll
  function scrollToBottom() {
    setTimeout(() => {
      chatArea.scrollTop = chatArea.scrollHeight;
    }, 50);
  }

  // 4. Format Text (Markdown-like bold & linebreaks, structured reflection)
  function formatText(text) {
    if (!text) return "";
    let safe = text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");

    // Replace **bold** with <strong>bold</strong>
    safe = safe.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");

    // Split paragraphs
    const paragraphs = safe.split(/\n\s*\n/);
    return paragraphs
      .map((p) => {
        let trimmed = p.trim();
        if (trimmed.startsWith("📜 ANSWER:") || trimmed.startsWith("📜 उत्तर:")) {
          const lines = trimmed.split(/\n/);
          const header = lines[0];
          const rest = lines.slice(1).join("<br>");
          return `<div class="answer-header">${header}</div>` + (rest ? `<p class="reflection-p">${rest}</p>` : "");
        }
        return `<p class="reflection-p">${trimmed.replace(/\n/g, "<br>")}</p>`;
      })
      .join("");
  }

  // 5. Append User Message
  function appendUserMessage(text) {
    const bubble = document.createElement("div");
    bubble.className = "message-bubble outgoing";
    bubble.innerHTML = `
      <div class="bubble-content">
        <p>${text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")}</p>
      </div>
      <div class="bubble-meta">
        <span class="message-time">${getFormattedTime()}</span>
        <span class="message-status-ticks">✓✓</span>
      </div>
    `;
    messagesContainer.appendChild(bubble);
    scrollToBottom();
  }

  // 6. Append Bot Message & Source Cards
  function appendBotMessage(answerText, sources = []) {
    // Message Bubble
    const bubble = document.createElement("div");
    bubble.className = "message-bubble incoming";
    bubble.innerHTML = `
      <div class="bubble-content">
        ${formatText(answerText)}
      </div>
      <div class="bubble-meta">
        <span class="message-time">${getFormattedTime()}</span>
      </div>
    `;
    messagesContainer.appendChild(bubble);

    // Sources Card if any
    if (sources && sources.length > 0) {
      const sourceCard = document.createElement("div");
      sourceCard.className = "sources-card";

      const coverClasses = ["", "alt-1", "alt-2"];
      const coverIcons = ["📖", "🪔", "🌿", "📜", "🕊️"];

      const itemsHtml = sources
        .map((s, index) => {
          const coverClass = coverClasses[index % coverClasses.length];
          const icon = coverIcons[index % coverIcons.length];
          const bookTitle = s.book || "विचार क्रांति अभियान";
          const author = "पं. श्रीराम शर्मा आचार्य";
          const chapterText = s.chapter ? `अध्याय: ${s.chapter}` : "";
          const pageRange =
            s.page_start === s.page_end
              ? `पृष्ठ ${s.page_start}`
              : `पृष्ठ ${s.page_start}-${s.page_end}`;

          return `
            <div class="source-item">
              <div class="source-book-cover ${coverClass}">
                <span>${icon}</span>
              </div>
              <div class="source-details">
                <div class="source-book-title" title="${bookTitle}">${bookTitle}</div>
                <div class="source-author">${author}</div>
                ${chapterText ? `<div class="source-chapter">${chapterText}</div>` : ""}
              </div>
              <div class="source-page-badge">${pageRange}</div>
            </div>
          `;
        })
        .join("");

      sourceCard.innerHTML = `
        <div class="sources-header">
          <span>📖 स्रोत (Sources)</span>
        </div>
        <div class="sources-list">
          ${itemsHtml}
        </div>
      `;

      messagesContainer.appendChild(sourceCard);
    }

    scrollToBottom();
  }

  // 7. Send Query to Backend API
  async function handleSendMessage(queryText) {
    const text = (queryText || messageInput.value || "").trim();
    if (!text || isSending) return;

    isSending = true;
    messageInput.value = "";
    messageInput.focus();

    // Add user message bubble
    appendUserMessage(text);

    // Update Header Status & Typing Indicator
    if (headerStatusEl) headerStatusEl.textContent = "typing...";
    if (typingIndicator) typingIndicator.style.display = "flex";
    scrollToBottom();

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          question: text,
          language: "hi",
          conversation_id: conversationId,
        }),
      });

      if (!response.ok) {
        throw new Error(`Server returned HTTP ${response.status}`);
      }

      const data = await response.json();
      const answer = data.answer || "वर्तमान में उत्तर प्राप्त नहीं हो सका।";
      const sources = data.sources || [];

      // Render response
      appendBotMessage(answer, sources);
    } catch (err) {
      console.error("Chat error:", err);
      appendBotMessage(
        "क्षमा करें, सेवा से जुड़ने में व्यवधान हुआ। कृपया कुछ क्षण बाद पुनः प्रयास करें।\n\n(Error: " +
          err.message +
          ")"
      );
    } finally {
      isSending = false;
      if (headerStatusEl) headerStatusEl.textContent = "online";
      if (typingIndicator) typingIndicator.style.display = "none";
      scrollToBottom();
    }
  }

  // 8. Event Listeners
  if (sendBtn) {
    sendBtn.addEventListener("click", () => handleSendMessage());
  }

  if (messageInput) {
    messageInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSendMessage();
      }
    });
  }

  // Quick suggestion chips
  suggestionItems.forEach((btn) => {
    btn.addEventListener("click", () => {
      const query = btn.getAttribute("data-query");
      if (query) {
        handleSendMessage(query);
      }
    });
  });
});
