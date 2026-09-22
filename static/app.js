const state = {
  conversationId: localStorage.getItem("conversation_id") || crypto.randomUUID(),
  consent: localStorage.getItem("consent") === "yes"
};
localStorage.setItem("conversation_id", state.conversationId);

const chat = document.querySelector("#chat");
const privacy = document.querySelector("#privacy");
const consent = document.querySelector("#consent");
const composer = document.querySelector("#composer");
const message = document.querySelector("#message");
const adapterVersion = document.querySelector("#adapterVersion");
const deleteConversation = document.querySelector("#deleteConversation");

deleteConversation.addEventListener("click", async () => {
  await fetch("/api/conversations/" + state.conversationId, {method: "DELETE"});
  localStorage.removeItem("conversation_id");
  localStorage.removeItem("consent");
  location.reload();
});

consent.checked = state.consent;
if (state.consent) privacy.hidden = true;

function addMessage(id, role, text) {
  const wrapper = document.createElement("article");
  wrapper.className = "msg " + role;
  wrapper.dataset.id = id;

  const body = document.createElement("div");
  body.textContent = text;
  wrapper.appendChild(body);

  const meta = document.createElement("div");
  meta.className = "meta";
  meta.textContent = role === "assistant" ? "assistant" : "you";
  wrapper.appendChild(meta);

  if (role === "assistant") {
    const actions = document.createElement("div");
    actions.className = "actions";
    for (const pair of [["1",1],["2",2],["3",3],["4",4],["5",5]]) {
      const label = pair[0], value = pair[1];
      const b = document.createElement("button");
      b.className = "small";
      b.textContent = "★ " + label;
      b.onclick = async () => {
        await fetch("/api/rating", {
          method: "POST",
          headers: {"Content-Type":"application/json"},
          body: JSON.stringify({conversation_id: state.conversationId, message_id: id, rating: value})
        });
      };
      actions.appendChild(b);
    }
    const edit = document.createElement("button");
    edit.className = "small";
    edit.textContent = "edit";
    edit.onclick = () => makeEditable(wrapper, id, text);
    actions.appendChild(edit);
    wrapper.appendChild(actions);
  }
  chat.appendChild(wrapper);
  chat.scrollTop = chat.scrollHeight;
}

function makeEditable(wrapper, id, oldText) {
  const textarea = document.createElement("textarea");
  textarea.value = oldText;
  textarea.rows = 4;
  const save = document.createElement("button");
  save.textContent = "Save edit";
  save.onclick = async () => {
    const response = await fetch("/api/edit", {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify({conversation_id: state.conversationId, message_id: id, new_content: textarea.value})
    });
    if (!response.ok) return;
    const data = await response.json();
    wrapper.firstChild.textContent = data.content;
    textarea.remove();
    save.remove();
  };
  wrapper.insertBefore(textarea, wrapper.firstChild);
  wrapper.insertBefore(save, wrapper.firstChild);
}

consent.addEventListener("change", () => {
  state.consent = consent.checked;
  localStorage.setItem("consent", state.consent ? "yes" : "no");
  privacy.hidden = state.consent;
});

composer.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!state.consent) {
    alert("Please accept the data-use warning first.");
    return;
  }
  const text = message.value.trim();
  if (!text) return;
  message.value = "";
  addMessage(crypto.randomUUID(), "user", text);

  const response = await fetch("/api/chat", {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({conversation_id: state.conversationId, message: text, consent: true})
  });
  const data = await response.json();
  if (!response.ok) {
    addMessage(crypto.randomUUID(), "assistant", data.detail || "The model backend is unavailable.");
    return;
  }
  adapterVersion.textContent = "adapter: " + data.adapter_version;
  addMessage(data.message_id, "assistant", data.reply);
});

(async () => {
  try {
    const response = await fetch("/api/conversations/" + state.conversationId);
    const data = await response.json();
    for (const item of (data.messages || [])) addMessage(item.id, item.role, item.content);
  } catch (_) {}
})();
