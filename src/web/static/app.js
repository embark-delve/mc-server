"use strict";
const $ = (id) => document.getElementById(id);
const fragment = new URLSearchParams(location.hash.slice(1));
let token =
  fragment.get("token") || sessionStorage.getItem("clubhouse-token") || "";
if (fragment.has("token")) {
  sessionStorage.setItem("clubhouse-token", token);
  history.replaceState(null, "", location.pathname);
}
let state = null;
let pending = false;
let view = "world";
function notice(message) {
  $("notice").textContent = message;
  $("notice").hidden = !message;
}
function navigate(next) {
  if (["care", "players"].includes(next) && state?.role !== "admin") return;
  view = next;
  if (next === "players") loadUsers();
  document.querySelectorAll("[data-panel]").forEach((el) => {
    el.hidden = el.dataset.panel !== next;
  });
  document.querySelectorAll(".nav").forEach((el) => {
    const active = el.dataset.view === next;
    el.classList.toggle("active", active);
    if (active) el.setAttribute("aria-current", "page");
    else el.removeAttribute("aria-current");
  });
}
document
  .querySelectorAll("[data-view]")
  .forEach((el) =>
    el.addEventListener("click", () => navigate(el.dataset.view)),
  );
function inventory(id, items, empty) {
  const list = $(id);
  list.replaceChildren();
  for (const text of items.length ? items : [empty]) {
    const li = document.createElement("li");
    li.textContent = text;
    if (!items.length) li.className = "empty";
    list.append(li);
  }
}
async function api(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: { Authorization: `Bearer ${token}`, ...options.headers },
    signal: AbortSignal.timeout(70000),
    cache: "no-store",
  });
  const data = await response.json();
  if (!response.ok) {
    if (response.status === 401) {
      token = "";
      sessionStorage.removeItem("clubhouse-token");
    }
    throw new Error(data.error || "Something went wrong. Please try again.");
  }
  return data;
}
function render(s) {
  state = s;
  $("setup-card").hidden = s.initialized;
  $("role").textContent =
    s.role === "admin" ? "Server manager" : "Server manager";
  $("care-nav").hidden = s.role !== "admin";
  $("players-nav").hidden = s.role !== "admin";
  if (["care", "players"].includes(view) && s.role !== "admin")
    navigate("world");
  $("world-name").textContent =
    s.profile === "forge" ? "The Overworld" : s.profile;
  $("version").textContent = `Minecraft ${s.version}`;
  $("forge").textContent = `Forge ${s.forge}`;
  $("join-version").textContent = s.version;
  $("join-forge").textContent = s.forge;
  $("address").textContent = s.connection;
  const busy = s.operation.state === "working";
  const ready = s.running && s.health === "healthy" && s.security_verified;
  $("access-status").textContent = s.security_verified
    ? "Account + allowlist checks passed"
    : "Account + allowlist checks configured";
  $("world-status").textContent = busy
    ? "An adventure is in the making…"
    : !s.initialized
      ? "Ready for your first setup"
      : !s.available
        ? "Docker needs a little help"
        : ready
          ? "Ready to explore"
          : s.security_error
            ? "Access needs a quick check"
            : s.running
              ? "Waking up…"
              : "Resting until your next adventure";
  $("start").disabled =
    pending || busy || s.running || !s.available || !s.initialized;
  $("start").textContent = ready
    ? "✓ World is ready"
    : busy
      ? "Working on your world…"
      : s.running
        ? "World is waking up…"
        : "▶  Start adventure  ↗";
  $("start-hint").textContent = ready
    ? "Head to How to join. Your adventure awaits."
    : "Your world stays on your laptop.";
  $("stop").disabled = pending || busy || !s.running;
  $("backup").disabled =
    pending || busy || s.running || !s.available || !s.initialized;
  $("check-setup").textContent = s.initialized ? "✓" : "○";
  $("check-docker").textContent = s.available ? "✓" : "○";
  $("check-ready").textContent = ready ? "✓" : "○";
  inventory(
    "backups",
    s.backups.map(
      (x) => `${x.name} · ${(x.bytes / 1024 / 1024).toFixed(1)} MB`,
    ),
    "No recovery copies yet. Stop the world, then create your first backup.",
  );
  renderMods(s);
  notice(
    s.security_error ||
      s.operation.message ||
      (!s.initialized
        ? "Create your world using the setup form. Add your Minecraft name and review the EULA."
        : !s.available
          ? "Open Docker Desktop and check that its engine is running. The world controls will become available when it is ready."
          : s.inventory_error || ""),
  );
}
async function refresh() {
  $("locked").hidden = !!token;
  $("dashboard").hidden = !token;
  if (!token) {
    $("role").textContent = "Private access";
    $("care-nav").hidden = true;
    $("players-nav").hidden = true;
    return;
  }
  try {
    render(await api("/api/status"));
  } catch (err) {
    notice(err.message);
    $("start").disabled = true;
    $("stop").disabled = true;
    $("backup").disabled = true;
    if (!token) {
      $("locked").hidden = false;
      $("dashboard").hidden = true;
    }
  }
}
async function act(action) {
  if (pending || !state) return;
  pending = true;
  render(state);
  try {
    const op = await api(`/api/actions/${action}`, {
      method: "POST",
      headers: { "X-Confirm-Profile": state.profile },
    });
    state.operation = op;
  } catch (err) {
    notice(err.message);
  } finally {
    pending = false;
    await refresh();
  }
}
$("start").addEventListener("click", () => act("start"));
let confirmAction;
for (const action of ["stop", "backup"])
  $(action).addEventListener("click", () => {
    confirmAction = action;
    $("confirm-title").textContent =
      action === "stop"
        ? "Time for a little break?"
        : "Keep a copy of this world?";
    $("confirm-copy").textContent =
      action === "stop"
        ? `Everyone on ${state.profile} will be disconnected after the world saves. Make sure they know first.`
        : `Create a recovery copy of ${state.profile}. The world must stay stopped until the copy is complete.`;
    $("confirm").showModal();
  });
$("confirm").addEventListener("close", () => {
  if ($("confirm").returnValue === "confirm") {
    if (confirmAction === "user") changeUser(userAction);
    else if (confirmAction === "mod") changeMod(modAction);
    else act(confirmAction);
  }
});
$("copy").addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(state.connection);
    notice(
      "Server address copied. Paste it into Minecraft → Multiplayer → Add Server.",
    );
  } catch {
    notice(`Copy this address into Minecraft: ${state.connection}`);
  }
});
$("lock").addEventListener("click", async () => {
  await api("/api/logout", { method: "POST" }).catch(() => {});
  token = "";
  state = null;
  sessionStorage.removeItem("clubhouse-token");
  navigate("world");
  notice("Clubhouse locked. Sign in to come back.");
  refresh();
});
async function poll() {
  await refresh();
  setTimeout(poll, 5000);
}
poll();

$("login-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = event.submitter;
  button.disabled = true;
  try {
    const result = await api("/api/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        username: $("login-name").value,
        password: $("login-password").value,
      }),
    });
    token = result.token;
    sessionStorage.setItem("clubhouse-token", token);
    $("login-password").value = "";
    notice("");
    await refresh();
  } catch (err) {
    notice(err.message);
  } finally {
    button.disabled = false;
  }
});
async function loadUsers() {
  try {
    const result = await api("/api/players");
    const list = $("users");
    list.replaceChildren();
    for (const player of result.players) {
      const li = document.createElement("li");
      const label = document.createElement("strong");
      label.textContent = player.minecraft;
      li.append(label);
      const detail = document.createElement("p");
      detail.textContent = player.status;
      li.append(detail);
      const actions =
        player.status === "banned"
          ? ["unban", "remove"]
          : player.status === "removed"
            ? ["add"]
            : ["ban", "remove"];
      for (const action of actions) {
        const button = document.createElement("button");
        button.className = "secondary";
        button.textContent = {
          add: "Allow again",
          ban: "Ban player",
          unban: "Unban",
          remove: "Remove access",
        }[action];
        button.addEventListener("click", () => {
          userAction = { action, minecraft: player.minecraft };
          confirmAction = "user";
          $("confirm-title").textContent = `${button.textContent}?`;
          $("confirm-copy").textContent =
            `This changes game access for ${player.minecraft} on ${state.profile}. Bans and removals disconnect them when the game is running. Their builds are kept.`;
          $("confirm").showModal();
        });
        li.append(button);
      }
      list.append(li);
    }
    if (!result.players.length)
      inventory(
        "users",
        [],
        "No players yet. Add your Minecraft username to get started.",
      );
  } catch (err) {
    notice(err.message);
  }
}
let userAction = null;
async function changeUser(data) {
  try {
    await api("/api/players", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Confirm-Profile": state.profile,
      },
      body: JSON.stringify(data),
    });
    notice("Player access updated.");
    await loadUsers();
  } catch (err) {
    notice(err.message);
  }
}
$("player-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = event.submitter;
  button.disabled = true;
  try {
    await changeUser({ action: "add", minecraft: $("player-name").value });
  } finally {
    button.disabled = false;
  }
});
$("setup-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = event.submitter;
  button.disabled = true;
  try {
    await api("/api/setup", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        minecraft: $("setup-name").value,
        accept_eula: $("setup-eula").checked ? "true" : "false",
      }),
    });
    await refresh();
  } catch (err) {
    notice(err.message);
  } finally {
    button.disabled = false;
  }
});

let modAction = null;
function renderMods(s) {
  const list = $("mods");
  list.replaceChildren();
  for (const mod of s.mods) {
    const li = document.createElement("li");
    const label = document.createElement("span");
    label.textContent = mod.name;
    li.append(label);
    const button = document.createElement("button");
    button.className = "secondary";
    button.setAttribute("role", "switch");
    button.setAttribute("aria-checked", String(mod.enabled));
    button.setAttribute(
      "aria-label",
      `${mod.name}: ${mod.enabled ? "enabled" : "disabled"}`,
    );
    button.textContent = mod.enabled ? "Enabled ✓" : "Disabled";
    button.disabled =
      s.running || !s.available || s.operation.state === "working";
    button.addEventListener("click", () => {
      modAction = { filename: mod.id, enabled: mod.enabled ? "false" : "true" };
      confirmAction = "mod";
      $("confirm-title").textContent =
        `${mod.enabled ? "Disable" : "Enable"} this mod?`;
      $("confirm-copy").textContent =
        `${mod.name}. Changes apply on the next start. Other mods may depend on it; back up the world before changing content mods.`;
      $("confirm").showModal();
    });
    li.append(button);
    list.append(li);
  }
  if (!s.mods.length)
    inventory(
      "mods",
      [],
      "No mods installed yet. Installed server mods are enabled by default.",
    );
}
async function changeMod(data) {
  try {
    await api("/api/mods", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Confirm-Profile": state.profile,
      },
      body: JSON.stringify(data),
    });
    await refresh();
    notice("Mod updated. Check dependencies before starting the world.");
  } catch (err) {
    notice(err.message);
  }
}
