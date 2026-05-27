

import gradio as gr
from rag_engine_v4 import handle_query, get_overview_success_message

# -------------------------------
# 💬 CHAT FUNCTION
# -------------------------------
def chat_fn(message, history, session_id):
    if not message.strip():
        return history, history, ""

    # Get grounded response from RAG engine
    response = handle_query(
        user_message=message,
        history=history,
        session_id=session_id
    )

    history = history + [
        {"role": "user", "content": message},
        {"role": "assistant", "content": response}
    ]

    return history, history, ""  # clear textbox after send


# --- Toggle chat visibility ---
def toggle_chat(current_state):
    new_state = not current_state
    return new_state, gr.update(visible=new_state)


# --- Load predefined query into textbox ---
def load_chip(chip_text):
    return chip_text


def overview_chip_fn(history, session_id):
    default_vendor = "vendor_1"
    action_message = f"Open the overview report for {default_vendor} and send the summary mail."
    handle_query(
        user_message=action_message,
        history=history,
        session_id=session_id
    )
    response = get_overview_success_message(default_vendor)

    history = history + [
        {"role": "user", "content": f"Overview report for {default_vendor}"},
        {"role": "assistant", "content": response}
    ]

    return history, history, ""


# -------------------------------
# 🎨 CSS
# -------------------------------
css = """
/* ── Fill the iframe viewport ── */
html, body {
    margin: 0 !important;
    padding: 0 !important;
    height: 100% !important;
    overflow: hidden !important;
}
.gradio-container {
    max-width: 100% !important;
    width: 100% !important;
    min-height: 100vh !important;
    padding: 0 !important;
    margin: 0 !important;
}
footer.svelte-1ax1toq, footer { display: none !important; }
#component-0 > .gap, .gap { gap: 0 !important; }

#float-btn {
    position: fixed !important;
    bottom: 25px !important;
    right: 25px !important;
    width: 60px !important;
    height: 60px !important;
    border-radius: 50% !important;
    font-size: 26px !important;
    background-color: #4285F4 !important;
    color: white !important;
    z-index: 9999 !important;
}

#chat-box {
    position: fixed;
    bottom: 100px;
    right: 25px;
    width: 380px;
    background: white;
    border-radius: 12px;
    box-shadow: 0px 6px 20px rgba(0,0,0,0.25);
    z-index: 9999;
    padding: 10px;
}

/* Chip buttons row */
.chip-row {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-bottom: 6px;
}

.chip-btn {
    font-size: 11px !important;
    padding: 4px 10px !important;
    border-radius: 20px !important;
    border: 1px solid #4285F4 !important;
    background: #f0f4ff !important;
    color: #4285F4 !important;
    cursor: pointer !important;
    white-space: nowrap !important;
    height: auto !important;
    min-width: unset !important;
}

.chip-btn:hover {
    background: #4285F4 !important;
    color: white !important;
}

/* Header row */
#chat-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 4px;
}

#min-btn {
    font-size: 18px !important;
    padding: 0 8px !important;
    background: transparent !important;
    border: none !important;
    color: #555 !important;
    cursor: pointer !important;
}
"""

# -------------------------------
# 🖥️ PREDEFINED CHIPS
# -------------------------------
CHIPS = [
    ("💰 Forecast", "What is my Forecast for may for vendor_1?"),
    ("🔄 Renewal Split", "Show renewal split for vendor_1 for may"),
    ("⚠️ Churn Users", "Who are my at-risk users for vendor_1?"),
    ("📊 Overview", "Give me a full overview for vendor_1 for may"),
    ("💡 Budget", "What would be my Budget forecast for vendor_1 for the upcoming quarter?"),
]

# -------------------------------
# 🖥️ UI
# -------------------------------

with gr.Blocks() as demo:
    chat_open = gr.State(False)
    state = gr.State([])
    session_id = gr.State("user_session_1")  # can be dynamic per user if needed

    # --- Dashboard (Tableau Embedding API v3 with multi-select Fiscal Year) ---

    gr.HTML("""
    <style>
      #fy-bar {
        display: flex; align-items: center; gap: 14px;
        padding: 8px 18px; background: #f0f4ff;
        border-bottom: 2px solid #d0d8f0;
        font-family: -apple-system, BlinkMacSystemFont, sans-serif;
        position: sticky; top: 0; z-index: 100;
      }
      #fy-bar .fy-title {
        font-weight: 800; font-size: 11px; color: #4b5563;
        text-transform: uppercase; letter-spacing: .08em;
      }
      .fy-label {
        display: flex; align-items: center; gap: 5px;
        font-size: 13px; color: #374151; cursor: pointer;
        padding: 3px 10px; border-radius: 20px;
        border: 1px solid #c7d2fe; background: #fff;
        transition: all .15s;
      }
      .fy-label:hover { background: #e0e7ff; }
      .fy-label input[type=checkbox] { cursor: pointer; accent-color: #4f46e5; }
      .fy-label.checked { background: #4f46e5; color: #fff; border-color: #4f46e5; }
      #fy-status { font-size: 11px; color: #9ca3af; margin-left: auto; }
      #tableau-wrap { width: 100%; height: calc(100vh - 52px); overflow: hidden; }
      #tViz { width: 100%; height: 100%; display: block; min-height: 900px; }
    </style>

    <div id="fy-bar">
      <span class="fy-title">Fiscal Year</span>
      <label class="fy-label" id="lbl-2024">
        <input type="checkbox" class="fy-cb" value="2024" onchange="applyFY(this)"> 2024
      </label>
      <label class="fy-label" id="lbl-2025">
        <input type="checkbox" class="fy-cb" value="2025" onchange="applyFY(this)"> 2025
      </label>
      <label class="fy-label checked" id="lbl-2026">
        <input type="checkbox" class="fy-cb" value="2026" checked onchange="applyFY(this)"> 2026
      </label>
      <span id="fy-status">⏳ Loading viz…</span>
    </div>

    <div id="tableau-wrap">
      <script type="module"
        src="https://public.tableau.com/javascripts/api/tableau.embedding.3.latest.min.js">
      </script>
      <tableau-viz id="tViz"
        src="https://public.tableau.com/views/SAFE_v3/SAFE"
        toolbar="hidden"
        hide-tabs
        width="100%"
        height="900">
      </tableau-viz>
    </div>

    <script>
      const vizEl = document.getElementById('tViz');
      let vizReady = false;

      // Sync chip highlight with checkbox state
      function syncChips() {
        document.querySelectorAll('.fy-cb').forEach(cb => {
          const lbl = document.getElementById('lbl-' + cb.value);
          if (lbl) lbl.classList.toggle('checked', cb.checked);
        });
      }

      // Apply multi-select filter to Tableau
      async function applyFY(changed) {
        syncChips();
        if (!vizReady) return;
        const years = [...document.querySelectorAll('.fy-cb:checked')].map(c => c.value);
        if (!years.length) {
          if (changed) changed.checked = true;   // prevent unchecking all
          syncChips();
          return;
        }
        try {
          const sheet = vizEl.workbook.activeSheet;
          await sheet.applyFilterAsync('Fiscal Year', years, 'replace');
          document.getElementById('fy-status').textContent = '✔ ' + years.join(', ');
        } catch(e) {
          console.error('Tableau filter error:', e);
          document.getElementById('fy-status').textContent = '⚠ filter error';
        }
      }

      // Wait for viz to be fully interactive before applying filters
      vizEl.addEventListener('firstinteractive', async () => {
        vizReady = true;
        document.getElementById('fy-status').textContent = '✔ 2026';
        await applyFY(null);
      });
    </script>
    """)

    # --- Floating button ---
    float_btn = gr.Button("🤖", elem_id="float-btn")

    # --- Chat popup ---
    with gr.Column(visible=False, elem_id="chat-box") as chat_panel:

        # Header
        with gr.Row(elem_id="chat-header"):
            gr.Markdown("#### 🤖Demand planning Ai")
            min_btn = gr.Button("—", elem_id="min-btn")

        # Chatbot display

        chatbot = gr.Chatbot(
        height="38vh",
        show_label=False,
        container=False
        )


        # --- Predefined chip buttons ---
        gr.Markdown("<small>**Quick queries — click to load:**</small>")
        with gr.Row(elem_classes="chip-row"):
            chip_btns = []
            overview_btn = None
            for label, query_text in CHIPS:
                btn = gr.Button(label, elem_classes="chip-btn", size="sm")
                if "Overview" in label:
                    overview_btn = btn
                else:
                    chip_btns.append((btn, query_text))

        # --- Input row ---
        with gr.Row():
            msg = gr.Textbox(
                placeholder="Ask anything or pick a query above...",
                label="",
                container=False,
                scale=4,
                lines=1
            )
            send_btn = gr.Button("Send", scale=1, variant="primary")

    # --------------------------------
    # ⚡ EVENT BINDINGS
    # --------------------------------

    # Open / close chat
    float_btn.click(toggle_chat, inputs=chat_open, outputs=[chat_open, chat_panel])
    min_btn.click(toggle_chat, inputs=chat_open, outputs=[chat_open, chat_panel])

    msg.submit(
        chat_fn,
        inputs=[msg, state, session_id],
        outputs=[chatbot, state, msg],
        show_progress="minimal",
        show_progress_on=[chatbot]
    )

    # Send button click
    send_btn.click(
        chat_fn,
        inputs=[msg, state, session_id],
        outputs=[chatbot, state, msg],
        show_progress="minimal",
        show_progress_on=[chatbot]
    )

    # Standard chips → load text into textbox (does NOT auto-send)
    for btn, query_text in chip_btns:
        btn.click(
            fn=lambda q=query_text: q,
            inputs=[],
            outputs=[msg]
        )

    # Overview chip → open report link and send overview email immediately
    if overview_btn is not None:
        overview_btn.click(
            fn=overview_chip_fn,
            inputs=[state, session_id],
            outputs=[chatbot, state, msg],
            show_progress="minimal",
            show_progress_on=[chatbot]
        )

# --- Launch ---

demo.launch(inbrowser=False, css=css, server_port=7860, server_name="127.0.0.1")
