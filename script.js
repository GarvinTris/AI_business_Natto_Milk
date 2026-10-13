/* ═══════════════════════════════════════════════════════════
   NOIR CAFÉ — Main Script
   Features:
   · Navbar scroll effect
   · Hero particle system
   · Scroll reveal animations
   · Langflow chatbot integration
   · Chat UI interactions
   · Contact form handler
   · Toast notifications
═══════════════════════════════════════════════════════════ */

'use strict';

/* ─── LANGFLOW CONFIG ────────────────────────────────────── */
const LANGFLOW_CONFIG = {
  apiKey:  'sk-Z-LDoaHU93JaOPP9LR8xiG54A2Lj2ljq6CTGzH8hFKw',
  baseUrl: 'http://localhost:7860',
  flowId:  'a0694fe1-6a89-4a7e-9342-3e939f206fd5',
  get endpoint() {
    return `${this.baseUrl}/api/v1/run/${this.flowId}`;
  },
};

/* ─── STATE ──────────────────────────────────────────────── */
const state = {
  chatOpen:   false,
  isTyping:   false,
  sessionId:  generateSessionId(),
  msgCount:   0,
};

/* ─── UTILS ──────────────────────────────────────────────── */
function generateSessionId() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
    const r = (Math.random() * 16) | 0;
    return (c === 'x' ? r : (r & 0x3) | 0x8).toString(16);
  });
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/* ─── NAVBAR ─────────────────────────────────────────────── */
(function initNavbar() {
  const navbar = document.getElementById('navbar');
  if (!navbar) return;

  const onScroll = () => {
    navbar.classList.toggle('scrolled', window.scrollY > 60);
  };

  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll(); // run once on load

  // Hamburger (mobile)
  const hamburger = document.getElementById('hamburger');
  if (hamburger) {
    hamburger.addEventListener('click', () => {
      const links = document.querySelector('.nav-links');
      const cta   = document.querySelector('.nav-cta');
      if (!links) return;
      const open = links.style.display === 'flex';
      links.style.cssText = open ? '' : 'display:flex;flex-direction:column;position:fixed;top:72px;left:0;right:0;background:rgba(13,13,13,0.97);padding:24px 40px;gap:20px;border-bottom:1px solid #2A2A2A;z-index:899;backdrop-filter:blur(20px)';
      if (cta) cta.style.cssText = open ? '' : 'display:block;margin:0 40px 24px;';
    });
  }
})();

/* ─── HERO PARTICLES ─────────────────────────────────────── */
(function initParticles() {
  const container = document.getElementById('particles');
  if (!container) return;

  const COUNT = 28;
  const particles = [];

  for (let i = 0; i < COUNT; i++) {
    const el = document.createElement('div');
    el.className = 'particle';
    const size  = Math.random() * 3 + 1;
    const left  = Math.random() * 100;
    const delay = Math.random() * 12;
    const dur   = Math.random() * 12 + 8;
    const bot   = Math.random() * 60;

    el.style.cssText = `
      width:${size}px;height:${size}px;
      left:${left}%;bottom:${bot}%;
      animation-duration:${dur}s;
      animation-delay:${delay}s;
      opacity:0;
    `;
    container.appendChild(el);
    particles.push(el);
  }
})();

/* ─── SCROLL REVEAL ──────────────────────────────────────── */
(function initReveal() {
  const targets = document.querySelectorAll('[data-reveal]');
  if (!targets.length) return;

  const observer = new IntersectionObserver(
    entries => {
      entries.forEach((entry, idx) => {
        if (entry.isIntersecting) {
          // Stagger cards in the same parent
          const siblings = Array.from(
            entry.target.parentElement.querySelectorAll('[data-reveal]')
          );
          const order = siblings.indexOf(entry.target);
          setTimeout(() => {
            entry.target.classList.add('revealed');
          }, order * 80);
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.12, rootMargin: '0px 0px -40px 0px' }
  );

  targets.forEach(el => observer.observe(el));
})();

/* ─── ACTIVE NAV LINK (scroll spy) ──────────────────────── */
(function initScrollSpy() {
  const sections = document.querySelectorAll('section[id]');
  const links    = document.querySelectorAll('.nav-links a');
  if (!sections.length || !links.length) return;

  const observer = new IntersectionObserver(
    entries => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          links.forEach(a => {
            a.classList.toggle(
              'active',
              a.getAttribute('href') === `#${entry.target.id}`
            );
          });
        }
      });
    },
    { threshold: 0.4 }
  );

  sections.forEach(s => observer.observe(s));
})();

/* ─── TOAST ──────────────────────────────────────────────── */
function showToast(msg, duration = 3000) {
  const el = document.getElementById('toast');
  if (!el) return;
  el.textContent = msg;
  el.classList.add('show');
  setTimeout(() => el.classList.remove('show'), duration);
}

/* ─── CONTACT FORM ───────────────────────────────────────── */
function handleFormSubmit(e) {
  e.preventDefault();
  const btn = e.target.querySelector('button[type="submit"]');
  const orig = btn.textContent;
  btn.textContent = 'Confirming…';
  btn.disabled = true;

  setTimeout(() => {
    btn.textContent = '✓ Reservation Confirmed';
    btn.style.background = '#4CAF9A';
    showToast('🎉 Your reservation has been received. We\'ll see you soon!');
    setTimeout(() => {
      btn.textContent = orig;
      btn.style.background = '';
      btn.disabled = false;
      e.target.reset();
    }, 3000);
  }, 1200);
}

/* ═══════════════════════════════════════════════════════════
   CHATBOT
═══════════════════════════════════════════════════════════ */

/* ─── TOGGLE CHAT WINDOW ─────────────────────────────────── */
function toggleChat() {
  state.chatOpen = !state.chatOpen;
  const win  = document.getElementById('chatWindow');
  const fab  = document.getElementById('chatFab');
  const iconClosed = fab.querySelector('.chat-icon-closed');
  const iconOpen   = fab.querySelector('.chat-icon-open');
  const pulse      = fab.querySelector('.chat-fab-pulse');
  const label      = fab.querySelector('.chat-fab-label');

  if (state.chatOpen) {
    win.classList.add('open');
    win.setAttribute('aria-hidden', 'false');
    iconClosed.style.display = 'none';
    iconOpen.style.display   = 'flex';
    label.textContent = 'Close';
    if (pulse) pulse.style.display = 'none';
    // Focus input
    setTimeout(() => document.getElementById('chatInput')?.focus(), 350);
  } else {
    win.classList.remove('open');
    win.setAttribute('aria-hidden', 'true');
    iconClosed.style.display = 'flex';
    iconOpen.style.display   = 'none';
    label.textContent = 'Ask NOIR';
    if (pulse) pulse.style.display = 'block';
  }
}

/* ─── OPEN CHAT WITH PRE-FILLED MESSAGE ──────────────────── */
function openChat(message) {
  if (!state.chatOpen) toggleChat();
  if (message) {
    setTimeout(() => {
      const input = document.getElementById('chatInput');
      if (input) {
        input.value = message;
        input.focus();
        // Auto-send after short delay for UX feel
        setTimeout(() => sendMessage(), 400);
      }
    }, 400);
  }
}

/* ─── QUICK PROMPT BUTTON ────────────────────────────────── */
function sendQuick(text) {
  // Remove quick prompt buttons after first use
  const prompts = document.querySelector('.chat-quick-prompts');
  if (prompts) {
    prompts.style.opacity = '0';
    prompts.style.transition = 'opacity 0.3s';
    setTimeout(() => prompts.remove(), 300);
  }
  appendUserMessage(text);
  callLangflow(text);
}

/* ─── KEY HANDLER ────────────────────────────────────────── */
function handleChatKey(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
}

/* ─── SEND MESSAGE ───────────────────────────────────────── */
function sendMessage() {
  const input = document.getElementById('chatInput');
  if (!input) return;
  const text = input.value.trim();
  if (!text || state.isTyping) return;

  input.value = '';
  input.focus();

  appendUserMessage(text);
  callLangflow(text);
}

/* ─── APPEND USER MESSAGE ────────────────────────────────── */
function appendUserMessage(text) {
  const container = document.getElementById('chatMessages');
  if (!container) return;

  const msg = document.createElement('div');
  msg.className = 'chat-msg user';
  msg.innerHTML = `
    <div class="msg-avatar">U</div>
    <div class="msg-bubble">${escapeHtml(text)}</div>
  `;
  container.appendChild(msg);
  scrollToBottom();
}

/* ─── APPEND BOT MESSAGE ─────────────────────────────────── */
function appendBotMessage(html) {
  const container = document.getElementById('chatMessages');
  if (!container) return;

  const msg = document.createElement('div');
  msg.className = 'chat-msg bot';
  msg.innerHTML = `
    <div class="msg-avatar">N</div>
    <div class="msg-bubble">${html}</div>
  `;
  container.appendChild(msg);
  scrollToBottom();
}

/* ─── TYPING INDICATOR ───────────────────────────────────── */
function showTyping() {
  const container = document.getElementById('chatMessages');
  if (!container) return;

  const indicator = document.createElement('div');
  indicator.className = 'chat-msg bot typing-indicator';
  indicator.id = 'typingIndicator';
  indicator.innerHTML = `
    <div class="msg-avatar">N</div>
    <div class="msg-bubble">
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>
    </div>
  `;
  container.appendChild(indicator);
  scrollToBottom();
}

function hideTyping() {
  const el = document.getElementById('typingIndicator');
  if (el) el.remove();
}

/* ─── SCROLL TO BOTTOM ───────────────────────────────────── */
function scrollToBottom() {
  const container = document.getElementById('chatMessages');
  if (container) {
    requestAnimationFrame(() => {
      container.scrollTop = container.scrollHeight;
    });
  }
}

/* ─── ESCAPE HTML ────────────────────────────────────────── */
function escapeHtml(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

/* ─── FORMAT BOT RESPONSE ────────────────────────────────── */
function formatBotResponse(text) {
  if (!text) return '<p>Maaf, saya tidak dapat memproses pesan Anda saat ini.</p>';

  // Convert markdown-like formatting to HTML
  let html = escapeHtml(text);

  // Bold **text**
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

  // Italic *text*
  html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');

  // Bullet points
  const lines = html.split('\n');
  const formatted = [];
  let inList = false;

  for (const line of lines) {
    const trimmed = line.trim();
    if (trimmed.startsWith('- ') || trimmed.startsWith('• ')) {
      if (!inList) { formatted.push('<ul style="margin:6px 0;padding-left:18px;list-style:none;">'); inList = true; }
      formatted.push(`<li style="margin:3px 0;padding-left:12px;position:relative;"><span style="color:var(--gold);position:absolute;left:0;">·</span>${trimmed.slice(2)}</li>`);
    } else {
      if (inList) { formatted.push('</ul>'); inList = false; }
      if (trimmed) formatted.push(`<p>${trimmed}</p>`);
    }
  }
  if (inList) formatted.push('</ul>');

  return formatted.join('') || `<p>${html}</p>`;
}

/* ─── CALL LANGFLOW API ──────────────────────────────────── */
async function callLangflow(userMessage) {
  if (state.isTyping) return;
  state.isTyping = true;

  // Disable send button
  const sendBtn = document.querySelector('.chat-send-btn');
  if (sendBtn) sendBtn.disabled = true;

  showTyping();

  const payload = {
    output_type: 'chat',
    input_type:  'chat',
    input_value: userMessage,
    session_id:  state.sessionId,
  };

  try {
    const response = await fetch(LANGFLOW_CONFIG.endpoint, {
      method:  'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key':    LANGFLOW_CONFIG.apiKey,
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();
    const botText = extractLangflowText(data);

    hideTyping();
    appendBotMessage(formatBotResponse(botText));

  } catch (error) {
    console.error('Langflow API Error:', error);
    hideTyping();

    // Friendly fallback based on user message
    const fallback = getFallbackResponse(userMessage);
    appendBotMessage(formatBotResponse(fallback));
  } finally {
    state.isTyping = false;
    if (sendBtn) sendBtn.disabled = false;
    document.getElementById('chatInput')?.focus();
  }
}

/* ─── EXTRACT TEXT FROM LANGFLOW RESPONSE ─────────────────── */
function extractLangflowText(data) {
  try {
    // Try common Langflow response paths
    const paths = [
      data?.outputs?.[0]?.outputs?.[0]?.results?.message?.text,
      data?.outputs?.[0]?.outputs?.[0]?.results?.message?.data?.text,
      data?.outputs?.[0]?.outputs?.[0]?.messages?.[0]?.message,
      data?.outputs?.[0]?.outputs?.[0]?.artifacts?.message,
      data?.result,
      data?.output,
      data?.text,
      data?.message,
    ];

    for (const path of paths) {
      if (typeof path === 'string' && path.trim()) return path.trim();
    }

    // Deep search
    const str = JSON.stringify(data);
    const match = str.match(/"text"\s*:\s*"((?:[^"\\]|\\.)*)"/);
    if (match) return match[1].replace(/\\n/g, '\n').replace(/\\"/g, '"');

    return 'Terima kasih atas pesan Anda! Bagaimana lagi saya bisa membantu Anda hari ini?';
  } catch {
    return 'Maaf, terjadi kesalahan dalam memproses respons. Silakan coba lagi.';
  }
}

/* ─── FALLBACK RESPONSES (when API unreachable) ──────────── */
function getFallbackResponse(msg) {
  const lower = msg.toLowerCase();

  const responses = [
    {
      keywords: ['espresso', 'noir espresso', 'kopi hitam'],
      reply: `**Noir Espresso** adalah signature kami yang paling dicintai! ☕\n\nDiseduh dari biji **Ethiopia Yirgacheffe** pilihan dengan dark roast, menghadirkan:\n- Intensitas bold yang memanjakan\n- Rasa dark chocolate yang kaya\n- Aroma smoked cedar yang elegan\n- Sentuhan brown sugar yang lembut\n\nHarga: **Rp 42.000**. Ingin memesan atau ada yang ingin Anda tanyakan?`,
    },
    {
      keywords: ['cold brew', 'velvet', 'iced'],
      reply: `**Velvet Cold Brew** adalah pilihan premium kami! 🧊\n\nDibuat dari biji **Flores Bajawa** dengan proses cold steep **20 jam penuh** untuk mengekstrak rasa sempurna:\n- Rasa caramel yang naturally sweet\n- Nuansa hazelnut yang halus\n- Vanilla finish yang memikat\n\nHarga: **Rp 52.000**. Sangat cocok untuk menemani siang hari Anda!`,
    },
    {
      keywords: ['latte', 'golden', 'susu', 'oat'],
      reply: `**Golden Latte** adalah pilihan dengan nuansa lembut! ✨\n\nDibuat dari biji **Toraja Sapan** dan steamed oat milk premium:\n- Rasa citrus zest yang segar\n- Manisnya honey yang alami\n- Creamy oak yang memanjakan\n\nLengkap dengan latte art buatan barista kami. Harga: **Rp 58.000**`,
    },
    {
      keywords: ['pour over', 'manual brew', 'filter'],
      reply: `**Pour Over Reserve** adalah pengalaman kopi tertinggi di NOIR! 🫗\n\nDiseduh manual satu per satu dari biji **Aceh Gayo** dengan washed process:\n- Floral jasmine yang mempesona\n- Red apple yang cerah\n- Earl grey yang sophisticated\n\nSetiap cangkir adalah karya seni. Harga: **Rp 68.000**`,
    },
    {
      keywords: ['croissant', 'pastry'],
      reply: `**Butter Croissant** kami adalah keajaiban 72 lapisan! 🥐\n\nDibuat dengan laminated dough berkualitas tinggi:\n- Eksterior: renyah & bersisik sempurna\n- Interior: lembut, buttery, & mengepul hangat\n\nHarga: **Rp 38.000**. Sempurna dipasangkan dengan espresso kami!`,
    },
    {
      keywords: ['tiramisu', 'dessert', 'kue'],
      reply: `**Tiramisu Noir** adalah chef's pick kami! 🍮\n\nDibuat dengan:\n- Ladyfingers rendaman espresso single origin\n- House-made mascarpone cream premium\n- Tabur single-origin cocoa pilihan\n\nHarga: **Rp 62.000**. Kombinasi sempurna dengan Noir Espresso kami!`,
    },
    {
      keywords: ['menu', 'harga', 'price', 'list'],
      reply: `Berikut highlight menu NOIR CAFÉ:\n\n**☕ Signature Coffee**\n- Noir Espresso — Rp 42.000\n- Velvet Cold Brew — Rp 52.000\n- Golden Latte — Rp 58.000\n- Pour Over Reserve — Rp 68.000\n\n**🍽️ Artisan Snacks**\n- Butter Croissant — Rp 38.000\n- Tiramisu Noir — Rp 62.000\n- Belgian Waffle — Rp 55.000\n- Canelé Bordelais — Rp 45.000\n- Earl Grey Tart — Rp 58.000\n- Chocolate Éclair — Rp 48.000\n\nAda yang ingin Anda coba?`,
    },
    {
      keywords: ['jam', 'buka', 'tutup', 'hours', 'open'],
      reply: `Jam operasional **NOIR CAFÉ**:\n\n- **Senin – Jumat**: 07.00 – 22.00 WIB\n- **Sabtu – Minggu**: 08.00 – 23.00 WIB\n\nKami berlokasi di **Jl. Kemang Raya No. 42, Jakarta Selatan**. Reservasi tersedia melalui form di halaman ini atau hubungi **+62 21 7890 1234**.`,
    },
    {
      keywords: ['lokasi', 'alamat', 'where', 'location', 'kemang'],
      reply: `NOIR CAFÉ berlokasi di:\n\n📍 **Jl. Kemang Raya No. 42**\nKemang, Jakarta Selatan 12730\n\nMudah dijangkau dari area Kemang dan sekitarnya. Parkir tersedia. Untuk reservasi, silakan gunakan form di halaman ini atau hubungi kami di **+62 21 7890 1234**.`,
    },
    {
      keywords: ['reservasi', 'reservation', 'booking', 'book', 'meja'],
      reply: `Untuk reservasi meja di **NOIR CAFÉ**, Anda bisa:\n\n1. **Isi form** di bagian "Visit Us" di halaman ini\n2. **Hubungi kami** di +62 21 7890 1234\n3. **Email** hello@noircafe.id\n\nKami menyarankan reservasi untuk grup 3+ orang, terutama pada akhir pekan. Ada tanggal yang Anda inginkan?`,
    },
    {
      keywords: ['sourcing', 'origin', 'farm', 'petani', 'biji'],
      reply: `NOIR CAFÉ bermitra langsung dengan **7 farm pilihan** di Indonesia:\n\n- **Aceh Gayo** — Sumatera\n- **Toraja Sapan** — Sulawesi\n- **Flores Bajawa** — NTT\n- **Flores Manggarai** — NTT\n- **Java Preanger** — Jawa Barat\n- **Papua Wamena** — Papua\n- **Bali Kintamani** — Bali\n\nSemua biji di-roast in-house untuk menjaga kesegaran dan karakter terbaik.`,
    },
    {
      keywords: ['hello', 'hi', 'halo', 'hai', 'hey', 'selamat'],
      reply: `Selamat datang di **NOIR CAFÉ**! ☕\n\nSaya siap membantu Anda menemukan pengalaman kopi terbaik. Apa yang bisa saya bantu?\n\n- Info menu & harga\n- Rekomendasi kopi atau snack\n- Reservasi meja\n- Info lokasi & jam buka\n- Tentang kopi origin kami`,
    },
  ];

  for (const { keywords, reply } of responses) {
    if (keywords.some(k => lower.includes(k))) return reply;
  }

  // Default
  return `Terima kasih telah menghubungi **NOIR CAFÉ**! ☕\n\nSaya ada di sini untuk membantu Anda dengan:\n- Rekomendasi menu signature kami\n- Informasi reservasi\n- Jam & lokasi\n- Filosofi kopi kami\n\nApa yang ingin Anda ketahui?`;
}

/* ═══════════════════════════════════════════════════════════
   SMOOTH SCROLL FOR ANCHOR LINKS
═══════════════════════════════════════════════════════════ */
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener('click', function (e) {
    const target = document.querySelector(this.getAttribute('href'));
    if (!target) return;
    e.preventDefault();
    const offset = 80; // navbar height
    const top = target.getBoundingClientRect().top + window.scrollY - offset;
    window.scrollTo({ top, behavior: 'smooth' });
  });
});

/* ═══════════════════════════════════════════════════════════
   INIT ON DOM READY
═══════════════════════════════════════════════════════════ */
document.addEventListener('DOMContentLoaded', () => {
  // Set minimum date for reservation form to today
  const dateInput = document.getElementById('date');
  if (dateInput) {
    const today = new Date().toISOString().split('T')[0];
    dateInput.min = today;
    dateInput.value = today;
  }

  // Keyboard shortcut: Press '/' to open chat
  document.addEventListener('keydown', e => {
    if (
      e.key === '/' &&
      document.activeElement.tagName !== 'INPUT' &&
      document.activeElement.tagName !== 'TEXTAREA'
    ) {
      e.preventDefault();
      if (!state.chatOpen) toggleChat();
    }
    // Escape to close chat
    if (e.key === 'Escape' && state.chatOpen) toggleChat();
  });

  // Click outside chat to close (on mobile)
  document.addEventListener('click', e => {
    const win = document.getElementById('chatWindow');
    const fab = document.getElementById('chatFab');
    if (
      state.chatOpen &&
      win && !win.contains(e.target) &&
      fab && !fab.contains(e.target)
    ) {
      // Only close on mobile
      if (window.innerWidth < 768) toggleChat();
    }
  });

  console.log(
    '%c NOIR CAFÉ ',
    'background:#C9A84C;color:#0D0D0D;font-size:14px;font-weight:bold;padding:4px 12px;border-radius:4px;',
    '\nWelcome to NOIR CAFÉ — Premium Specialty Coffee\nPress "/" to open the chat assistant.'
  );
});
