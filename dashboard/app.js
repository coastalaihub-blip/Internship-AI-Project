// ============================================================
// Dashboard — Internship AI Project
// Paste your Supabase credentials below to connect
// ============================================================

const SUPABASE_URL = "";      // e.g. "https://abcxyz.supabase.co"
const SUPABASE_ANON_KEY = ""; // e.g. "eyJhbGci..."

// ── Init ──────────────────────────────────────────────────────────────────────

if (!SUPABASE_URL || !SUPABASE_ANON_KEY) {
  document.body.innerHTML = `
    <div style="padding:40px;font-family:sans-serif;color:#f87171;background:#0f1117;min-height:100vh;">
      <h2>Configuration Required</h2>
      <p style="margin-top:12px;color:#94a3b8;">
        Open <code>dashboard/app.js</code> and paste your Supabase URL and anon key at the top of the file.
      </p>
      <pre style="margin-top:16px;background:#1e2130;padding:16px;border-radius:8px;color:#e2e8f0;">
const SUPABASE_URL = "https://your-project.supabase.co";
const SUPABASE_ANON_KEY = "eyJhbGci...";
      </pre>
    </div>`;
  throw new Error("Supabase credentials not configured");
}

const { createClient } = supabase;
const db = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

// ── State ─────────────────────────────────────────────────────────────────────

let currentBotFilter = "all";
let conversationFeed = [];
let actionsFeed = [];

// ── DOM refs ──────────────────────────────────────────────────────────────────

const convFeedEl    = document.getElementById("conv-feed");
const actionsFeedEl = document.getElementById("actions-feed");
const botFilterEl   = document.getElementById("bot-filter");
const refreshBtnEl  = document.getElementById("refresh-btn");

const statMessages   = document.getElementById("stat-messages");
const statBookings   = document.getElementById("stat-bookings");
const statOrders     = document.getElementById("stat-orders");
const statEscalations = document.getElementById("stat-escalations");

// ── Helpers ───────────────────────────────────────────────────────────────────

function formatTime(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  return d.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit", hour12: true });
}

function formatDate(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  return d.toLocaleDateString("en-IN", { day: "numeric", month: "short" });
}

function truncate(str, n = 120) {
  if (!str) return "";
  return str.length > n ? str.slice(0, n) + "…" : str;
}

function escapeHtml(str) {
  if (!str) return "";
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

// ── Render Conversations ──────────────────────────────────────────────────────

function renderConversations(items, isNew = false) {
  if (!items.length) {
    convFeedEl.innerHTML = `
      <div class="empty-state">
        <div class="icon">💬</div>
        <p>No conversations yet. Start chatting with any bot!</p>
      </div>`;
    return;
  }

  const filtered = currentBotFilter === "all"
    ? items
    : items.filter(c => c.bot_id === currentBotFilter);

  convFeedEl.innerHTML = filtered.map((c, idx) => `
    <div class="conv-card ${isNew && idx === 0 ? 'new' : ''}">
      <div class="conv-header">
        <div class="conv-meta">
          <span class="bot-tag ${escapeHtml(c.bot_id)}">${escapeHtml(c.bot_id?.replace("_", " "))}</span>
          <span class="conv-username">@${escapeHtml(c.telegram_username || "anonymous")}</span>
          <span class="intent-tag ${escapeHtml(c.intent || '')}">${escapeHtml(c.intent || 'unknown')}</span>
        </div>
        <span class="conv-time">${formatTime(c.created_at)}</span>
      </div>
      <div class="conv-messages">
        <div class="msg-row user">
          <span class="label">You</span>
          <span class="text">${escapeHtml(truncate(c.user_message))}</span>
        </div>
        <div class="msg-row bot">
          <span class="label">Bot</span>
          <span class="text">${escapeHtml(truncate(c.bot_response))}</span>
        </div>
      </div>
    </div>
  `).join("");
}

// ── Render Actions ────────────────────────────────────────────────────────────

function renderActions(appointments, bookings, orders) {
  const all = [
    ...appointments.map(a => ({ type: "appointment", data: a, time: a.created_at })),
    ...bookings.map(b => ({ type: "room_booking", data: b, time: b.created_at })),
    ...orders.map(o => ({ type: "food_order", data: o, time: o.created_at }))
  ].sort((a, b) => new Date(b.time) - new Date(a.time));

  if (!all.length) {
    actionsFeedEl.innerHTML = `
      <div class="empty-state">
        <div class="icon">📋</div>
        <p>No actions taken yet.</p>
      </div>`;
    return;
  }

  actionsFeedEl.innerHTML = all.map(item => {
    const d = item.data;
    let details = "";

    if (item.type === "appointment") {
      details = `
        <strong>${escapeHtml(d.patient_name || "Unknown")}</strong><br>
        📅 ${escapeHtml(d.appointment_datetime || "TBC")} · Dr. ${escapeHtml(d.doctor || "Any")}<br>
        📞 ${escapeHtml(d.phone || "Not provided")}
        ${d.notes ? `<br>📝 ${escapeHtml(d.notes)}` : ""}`;
    } else if (item.type === "room_booking") {
      details = `
        <strong>${escapeHtml(d.guest_name || "Unknown")}</strong><br>
        🛏️ ${escapeHtml(d.room_type || "Standard")} · ${escapeHtml(d.check_in || "")} → ${escapeHtml(d.check_out || "")}<br>
        👥 ${d.guests_count || 1} guest(s)
        ${d.total_amount ? ` · ₹${d.total_amount}` : ""}`;
    } else if (item.type === "food_order") {
      const items = Array.isArray(d.items) ? d.items : [];
      const itemList = items.map(i => `${i.name} ×${i.qty}`).join(", ") || "—";
      details = `
        <strong>Room ${escapeHtml(d.room_number || "Takeaway")}</strong><br>
        🍽️ ${escapeHtml(itemList)}<br>
        💰 ₹${d.total_amount || 0} · Status: ${escapeHtml(d.status || "pending")}`;
    }

    return `
      <div class="action-card">
        <div class="action-card-header">
          <span class="action-type-tag ${item.type}">${item.type.replace("_", " ")}</span>
          <span class="conv-time">${formatDate(item.time)} ${formatTime(item.time)}</span>
        </div>
        <div class="action-details">${details}</div>
      </div>`;
  }).join("");
}

// ── Stats ─────────────────────────────────────────────────────────────────────

async function loadStats() {
  try {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const todayIso = today.toISOString();

    const [msgs, appts, orders, escl] = await Promise.all([
      db.from("conversations").select("id", { count: "exact", head: true }).gte("created_at", todayIso),
      db.from("appointments").select("id", { count: "exact", head: true }).gte("created_at", todayIso),
      db.from("food_orders").select("id", { count: "exact", head: true }).gte("created_at", todayIso),
      db.from("conversations").select("id", { count: "exact", head: true }).eq("intent", "escalate").gte("created_at", todayIso)
    ]);

    statMessages.textContent    = msgs.count  ?? 0;
    statBookings.textContent    = appts.count ?? 0;
    statOrders.textContent      = orders.count ?? 0;
    statEscalations.textContent = escl.count  ?? 0;
  } catch (e) {
    console.error("Stats error:", e);
  }
}

// ── Load Data ─────────────────────────────────────────────────────────────────

async function loadAll() {
  try {
    const [convRes, apptRes, bookRes, orderRes] = await Promise.all([
      db.from("conversations").select("*").order("created_at", { ascending: false }).limit(50),
      db.from("appointments").select("*").order("created_at", { ascending: false }).limit(20),
      db.from("hotel_bookings").select("*").order("created_at", { ascending: false }).limit(20),
      db.from("food_orders").select("*").order("created_at", { ascending: false }).limit(20)
    ]);

    conversationFeed = convRes.data || [];
    renderConversations(conversationFeed);
    renderActions(apptRes.data || [], bookRes.data || [], orderRes.data || []);
    await loadStats();
  } catch (e) {
    console.error("Load error:", e);
    convFeedEl.innerHTML = `<div class="empty-state"><p style="color:#f87171;">Error loading data: ${e.message}</p></div>`;
  }
}

// ── Realtime ──────────────────────────────────────────────────────────────────

function setupRealtime() {
  db.channel("dashboard-live")
    .on("postgres_changes", { event: "INSERT", schema: "public", table: "conversations" }, (payload) => {
      conversationFeed.unshift(payload.new);
      if (conversationFeed.length > 50) conversationFeed.pop();
      renderConversations(conversationFeed, true);
      loadStats();
    })
    .on("postgres_changes", { event: "INSERT", schema: "public", table: "appointments" }, () => loadAll())
    .on("postgres_changes", { event: "INSERT", schema: "public", table: "hotel_bookings" }, () => loadAll())
    .on("postgres_changes", { event: "INSERT", schema: "public", table: "food_orders" }, () => loadAll())
    .subscribe();
}

// ── Events ────────────────────────────────────────────────────────────────────

botFilterEl.addEventListener("change", () => {
  currentBotFilter = botFilterEl.value;
  renderConversations(conversationFeed);
});

refreshBtnEl.addEventListener("click", loadAll);

// ── Init ──────────────────────────────────────────────────────────────────────

loadAll();
setupRealtime();
