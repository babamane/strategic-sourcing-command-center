

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

    # --- Dashboard ---

    gr.HTML("""
    <iframe src="https://public.tableau.com/views/SAFE_v3/SAFE?:embed=true&:showVizHome=no&:toolbar=no"
            width="100%" height="800" frameborder="0"></iframe>
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

demo.launch(inbrowser=True, css=css)
