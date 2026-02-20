import streamlit as st
import time
import random
from models import CompletionResult, Classification

# Force stub mode - frontend only, no model calls
USE_STUB = False

# Try to import real implementations, fall back to stubs
try:
    from router import route
    from demo_prompts import DEMO_PROMPTS
except ImportError:
    pass

# Stub demo prompts
STUB_DEMO_PROMPTS = [
    {"label": "🟢 What year was the Eiffel Tower built?",
     "prompt": "What year was the Eiffel Tower built?"},
    {"label": "🟢 Find & replace foo → bar",
     "prompt": "Replace 'foo' with 'bar' in: def foo(): return foo()"},
    {"label": "🟢 Set a reminder",
     "prompt": "Remind me to call the dentist at 3pm tomorrow"},
    {"label": "🔴 Calendar + reminder (multi-step)",
     "prompt": "Check my calendar and find the next free 2-hour block, then set a dentist reminder in that slot"},
    {"label": "🔴 Generate unit tests",
     "prompt": "Generate comprehensive unit tests with edge cases for: def process_payment(user_id, amount, currency): pass"},
    {"label": "Custom...", "prompt": ""},
]

if USE_STUB:
    DEMO_PROMPTS = STUB_DEMO_PROMPTS


def stub_route(prompt: str, force_escalate: bool = False) -> CompletionResult:
    """Fake router — simulates the real three-step classify→route→execute flow."""
    is_hard = any(word in prompt.lower() for word in ["calendar", "test", "refactor", "complex", "find free"])
    escalated = force_escalate or is_hard

    # Simulate classification call (always haiku, always fast)
    time.sleep(0.1)
    classification_tokens_in = random.randint(60, 100)
    classification_tokens_out = random.randint(40, 80)
    classification_cost = (classification_tokens_in / 1_000_000 * 0.80 +
                           classification_tokens_out / 1_000_000 * 4.00)

    # Simulate execution call (haiku or sonnet depending on routing)
    time.sleep(0.2 if not escalated else 0.6)
    exec_tokens_in = random.randint(40, 120)
    exec_tokens_out = random.randint(50, 200)
    exec_cost = ((exec_tokens_in / 1_000_000 * (3.00 if escalated else 0.80)) +
                 (exec_tokens_out / 1_000_000 * (15.00 if escalated else 4.00)))

    return CompletionResult(
        response=f"{'[Large model] ' if escalated else '[Small model] '}Here is a response to: {prompt[:60]}...",
        model_used="large" if escalated else "small",
        model_id="sonnet" if escalated else "haiku",
        routing_reason="user forced escalation" if force_escalate else (
            "difficulty 0.75 >= 0.70 threshold" if escalated else "score 0.71 cleared threshold 0.69"
        ),
        escalated=escalated,
        input_tokens=classification_tokens_in + exec_tokens_in,
        output_tokens=classification_tokens_out + exec_tokens_out,
        cost_usd=classification_cost + exec_cost,
        latency_ms=random.uniform(900, 2200) if escalated else random.uniform(280, 700),
        classification=Classification(
            subtasks=["look up fact"] if not escalated else ["check calendar", "find slot", "set reminder"],
            task_categories={"general_qa": 0.9, "math": 0.0, "code_operation": 0.0,
                           "multi_step_reasoning": 0.1, "agentic_tool_use": 0.0, "long_context": 0.0},
            difficulty=0.75 if escalated else 0.20,
            dominant_category="agentic_tool_use" if escalated else "general_qa",
            escalate=escalated,
        )
    )


SONNET_PRICING = {"input": 3.00, "output": 15.00}  # per 1M tokens


def estimate_large_model_cost(result: CompletionResult) -> float:
    """Calculate what the request would have cost on the large model."""
    return (result.input_tokens / 1_000_000 * SONNET_PRICING["input"] +
            result.output_tokens / 1_000_000 * SONNET_PRICING["output"])


def model_badge(model_used: str, model_id: str) -> str:
    """Return colored badge for model tier."""
    if model_used == "small":
        return f"🟢 Small ({model_id})"
    return f"🔴 Large ({model_id})"


# Map UI slider names to router category names
SLIDER_TO_CATEGORY = {
    "Math": "math",
    "Code Operations": "code_operation",
    "Reasoning": "multi_step_reasoning",
    "Agentic Tool Use": "agentic_tool_use",
    "Long Context": "long_context",
    "General QA": "general_qa",
}


def handle_submit(prompt: str, force_escalate: bool):
    """Process a routing request and update session state."""
    if not prompt.strip():
        st.error("Please enter a prompt")
        return
    
    # Build ui_thresholds dict from session state sliders
    ui_thresholds = {
        SLIDER_TO_CATEGORY[name]: value 
        for name, value in st.session_state.sliders.items() 
        if name in SLIDER_TO_CATEGORY
    }
    
    with st.spinner("Routing..." if not force_escalate else "Sending to large model..."):
        if USE_STUB:
            result = stub_route(prompt, force_escalate)
        else:
            result = route(prompt, force_escalate, ui_thresholds=ui_thresholds)
    
    st.session_state.last_result = result
    st.session_state.session_cost += result.cost_usd
    st.session_state.history.append({
        "prompt": prompt[:40] + "..." if len(prompt) > 40 else prompt,
        "model": result.model_id,
        "model_used": result.model_used,
        "category": result.classification.dominant_category if result.classification else "—",
        "cost": f"${result.cost_usd:.6f}",
        "latency": f"{result.latency_ms:.0f}ms",
    })


def optimize_prompt(prompt: str) -> str:
    """Optimize the prompt using CopilotKit service."""
    try:
        import requests
        
        # Get threshold context from session state
        context = {
            "thresholds": st.session_state.sliders
        }
        
        # Call CopilotKit service
        response = requests.post(
            'http://localhost:3001/api/optimize-prompt',
            json={
                'prompt': prompt,
                'context': context
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('success') and result.get('optimized'):
                optimized = result['optimized'].strip()
                
                if optimized and len(optimized) > 10:
                    return optimized
                else:
                    return prompt
            else:
                return prompt
        else:
            return prompt
            
    except requests.exceptions.ConnectionError:
        # CopilotKit service not running - use Ollama fallback
        return _optimize_with_ollama(prompt)
    except requests.exceptions.Timeout:
        return prompt
    except Exception:
        return _optimize_with_ollama(prompt)


def _optimize_with_ollama(prompt: str) -> str:
    """Fallback: Direct Ollama optimization when CopilotKit service is unavailable."""
    try:
        import requests
        
        system_prompt = """You are an expert Prompt Engineer. Rewrite the user's input to be more detailed, structured, and effective. Improve clarity and add necessary constraints. Return ONLY the improved prompt text without any preamble or explanation."""
        
        # Call Ollama API directly
        response = requests.post(
            'http://localhost:11434/api/generate',
            json={
                'model': 'qwen2.5:1.5b',
                'prompt': f"{system_prompt}\n\nOriginal prompt: {prompt}\n\nImproved prompt:",
                'stream': False,
                'options': {
                    'temperature': 0.7,
                    'top_p': 0.9,
                }
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            optimized = result.get('response', '').strip()
            
            if optimized and len(optimized) > 10:
                return optimized
            else:
                return prompt
        else:
            return prompt
            
    except Exception:
        return _stub_optimize(prompt)


def _stub_optimize(prompt: str) -> str:
    """Fallback stub optimization when Ollama is not available."""
    # Simulate API call delay
    time.sleep(1.5)
    
    # Stub optimization logic
    if len(prompt) < 50:
        return f"{prompt}\n\nPlease provide a detailed response with specific examples and clear explanations."
    elif "test" in prompt.lower():
        return f"Generate comprehensive unit tests for the following code, including:\n- Edge cases\n- Error handling\n- Input validation\n- Expected outputs\n\n{prompt}"
    elif "?" in prompt:
        return f"Please provide a detailed answer to the following question, including:\n- Clear explanation\n- Relevant examples\n- Step-by-step breakdown if applicable\n\nQuestion: {prompt}"
    else:
        return f"Task: {prompt}\n\nRequirements:\n- Be specific and detailed\n- Include relevant context\n- Provide clear success criteria"


# Page config
st.set_page_config(
    page_title="Hybrid LLM Router",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Skip startup checks in stub mode
try:
    import startup
    startup.run()
except:
    pass

# Session state
if "history" not in st.session_state:
    st.session_state.history = []
if "session_cost" not in st.session_state:
    st.session_state.session_cost = 0.0
if "last_result" not in st.session_state:
    st.session_state.last_result = None
if "sidebar_copied_prompt" not in st.session_state:
    st.session_state.sidebar_copied_prompt = ""
if "selected_demo" not in st.session_state:
    st.session_state.selected_demo = 0
if "show_optimizer" not in st.session_state:
    st.session_state.show_optimizer = False
if "original_prompt" not in st.session_state:
    st.session_state.original_prompt = ""
if "optimizing" not in st.session_state:
    st.session_state.optimizing = False
if "sliders" not in st.session_state:
    st.session_state.sliders = {
        "Math": 0.5,
        "Code Operations": 0.5,
        "Reasoning": 0.5,
        "Agentic Tool Use": 0.5,
        "Long Context": 0.5,
        "General QA": 0.5,
    }

# Handle optimization completion BEFORE any widgets are created
if st.session_state.optimizing:
    optimized = optimize_prompt(st.session_state.original_prompt)
    
    # Update the session state
    st.session_state.sidebar_copied_prompt = optimized
    st.session_state.optimizing = False
    
    # Set to "Custom..." mode
    st.session_state.selected_demo = len(DEMO_PROMPTS) - 1
    
    # Directly update the text area value in session state
    st.session_state.main_prompt_input = optimized
    
    st.success(f"✨ Prompt optimized! (Length: {len(st.session_state.original_prompt)} → {len(optimized)})")
    time.sleep(1)
    st.rerun()

# Modern header with custom styling
st.markdown("""
    <style>
    /* ── Base & Layout ── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    .main { font-family: 'Inter', sans-serif; }

    .main .block-container {
        padding: 1rem 2rem 2rem;
        max-width: 100%;
    }

    /* ── Header ── */
    .custom-header {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 20px rgba(79,70,229,0.25);
        text-align: center;
    }
    .custom-header h1 {
        color: #fff; font-size: 2rem; font-weight: 700; margin: 0;
    }
    .custom-header p {
        color: rgba(255,255,255,0.9); font-size: 0.95rem;
        margin: 0.4rem auto 0; max-width: 820px; line-height: 1.5;
    }

    /* ── Section cards ── */
    .section-card {
        background: var(--background-color, #ffffff);
        border: 1px solid rgba(0,0,0,0.08);
        border-radius: 10px;
        padding: 1.25rem;
        margin-bottom: 1rem;
        box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    }
    .section-title {
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #6b7280;
        margin: 0 0 0.75rem 0;
    }

    /* ── Text areas: fill container width, consistent height ── */
    .stTextArea { width: 100% !important; }
    .stTextArea > div { width: 100% !important; }
    .stTextArea textarea {
        width: 100% !important;
        min-height: 180px !important;
        border-radius: 8px !important;
        font-size: 0.9rem !important;
        line-height: 1.55 !important;
        padding: 0.75rem !important;
        resize: vertical !important;
    }

    /* ── Select box full width ── */
    .stSelectbox { width: 100%; }
    .stSelectbox > div > div {
        border-radius: 8px !important;
    }

    /* ── Buttons ── */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        font-size: 0.875rem;
        padding: 0.5rem 1.25rem;
        letter-spacing: 0.01em;
        transition: all 0.2s ease;
        min-height: 42px;
    }
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    /* Primary button */
    .stButton > button[kind="primary"],
    .stButton > button[data-testid="stBaseButton-primary"] {
        background: #4f46e5 !important;
        color: #fff !important;
        border: none !important;
    }
    .stButton > button[kind="primary"]:hover,
    .stButton > button[data-testid="stBaseButton-primary"]:hover {
        background: #4338ca !important;
    }
    /* Secondary / default buttons */
    .stButton > button[kind="secondary"],
    .stButton > button[data-testid="stBaseButton-secondary"] {
        background: transparent !important;
        color: #4f46e5 !important;
        border: 1.5px solid #4f46e5 !important;
    }
    .stButton > button[kind="secondary"]:hover,
    .stButton > button[data-testid="stBaseButton-secondary"]:hover {
        background: rgba(79,70,229,0.06) !important;
    }

    /* ── Metrics ── */
    [data-testid="stMetricValue"] {
        font-size: 1.35rem;
        font-weight: 700;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        color: #6b7280;
    }

    /* ── Routing decision card ── */
    .routing-card {
        border-radius: 8px;
        padding: 1rem 1.25rem;
        margin-bottom: 0.75rem;
        font-size: 0.88rem;
        line-height: 1.6;
    }
    .routing-card.small {
        background: #ecfdf5;
        border: 1.5px solid #10b981;
    }
    .routing-card.large {
        background: #fff7ed;
        border: 1.5px solid #f59e0b;
    }
    .routing-card .label {
        color: #6b7280;
        font-weight: 500;
    }

    /* ── Progress bar ── */
    .stProgress > div > div { border-radius: 8px; }

    /* ── Dataframe ── */
    .stDataFrame { border-radius: 8px; overflow: hidden; }

    /* ── Optimizer dialog ── */
    .optimizer-dialog {
        background: #f5f3ff;
        border: 1.5px solid #7c3aed;
        border-radius: 10px;
        padding: 1rem 1.25rem;
        margin-bottom: 0.75rem;
    }
    .optimizer-dialog h4 { margin-top: 0; color: #7c3aed; font-size: 0.95rem; }
    .optimizer-dialog p  { font-size: 0.88rem; margin-bottom: 0; }

    /* ── Dividers ── */
    hr { border: none; border-top: 1px solid rgba(0,0,0,0.06); margin: 1rem 0; }
    </style>

    <div class="custom-header">
        <h1>Hybrid LLM Router</h1>
        <p>Route prompts between a small local model and a large cloud model.
        Simple tasks stay fast and free; complex queries automatically escalate.</p>
    </div>
""", unsafe_allow_html=True)

# Layout — input takes 70%, scales take 30%
left_col, right_col = st.columns([7, 3], gap="medium")

# Get current prompt value (needed for both columns)
selected = 0
if "selected_demo" in st.session_state:
    selected = st.session_state.selected_demo

is_custom = DEMO_PROMPTS[selected]["label"] == "Custom..."
prompt_value = st.session_state.get("sidebar_copied_prompt") or ("" if is_custom else DEMO_PROMPTS[selected]["prompt"])

with left_col:
    # ── Input section ──
    st.markdown('<p class="section-title">Input</p>', unsafe_allow_html=True)

    # Use session state for selectbox to control it programmatically
    if "selected_demo" not in st.session_state:
        st.session_state.selected_demo = 0
    
    selected = st.selectbox(
        "Demo prompt",
        options=range(len(DEMO_PROMPTS)),
        format_func=lambda i: DEMO_PROMPTS[i]["label"],
        label_visibility="collapsed",
        key="demo_selector",
        index=st.session_state.selected_demo
    )
    
    # Detect when user changes the selectbox
    if selected != st.session_state.selected_demo:
        st.session_state.selected_demo = selected
        st.session_state.sidebar_copied_prompt = ""
        
        # Update the text area value directly in session state
        is_custom = DEMO_PROMPTS[selected]["label"] == "Custom..."
        if is_custom:
            st.session_state.main_prompt_input = ""
        else:
            st.session_state.main_prompt_input = DEMO_PROMPTS[selected]["prompt"]
        st.rerun()

    is_custom = DEMO_PROMPTS[st.session_state.selected_demo]["label"] == "Custom..."
    
    # Calculate the initial value for the text area
    # This only matters on first render or after widget state is deleted
    if st.session_state.get("sidebar_copied_prompt"):
        prompt_value = st.session_state.sidebar_copied_prompt
    elif "main_prompt_input" in st.session_state:
        # Use existing widget state
        prompt_value = st.session_state.main_prompt_input
    elif is_custom:
        prompt_value = ""
    else:
        prompt_value = DEMO_PROMPTS[st.session_state.selected_demo]["prompt"]

    prompt = st.text_area(
        "Prompt",
        value=prompt_value,
        height=220,
        placeholder="Type or choose a demo prompt above...",
        key="main_prompt_input",
        label_visibility="collapsed",
    )

    # Toolbar row: Optimize / Undo
    tool_cols = st.columns([1, 1, 4])
    with tool_cols[0]:
        if not st.session_state.optimizing:
            if st.button("Optimize", key="show_optimizer_btn", help="Rewrite this prompt with the local LLM", use_container_width=True):
                current_text = st.session_state.get("main_prompt_input", "")
                if current_text.strip():
                    st.session_state.show_optimizer = True
                    st.session_state.original_prompt = current_text
                else:
                    st.warning("Enter a prompt first.")
        else:
            st.caption("Optimizing...")
    with tool_cols[1]:
        if st.session_state.get("original_prompt"):
            if st.button("Undo", use_container_width=True, key="undo_optimize", help="Restore the original prompt"):
                st.session_state.sidebar_copied_prompt = st.session_state.original_prompt
                st.session_state.original_prompt = ""
                st.rerun()

    # Optimizer confirmation
    if st.session_state.show_optimizer:
        st.markdown("""
            <div class="optimizer-dialog">
                <h4>Prompt Optimizer</h4>
                <p>Rewrite this prompt using the local LLM to improve clarity and detail?</p>
            </div>
        """, unsafe_allow_html=True)
        col_yes, col_no = st.columns(2)
        with col_yes:
            if st.button("Yes, Optimize", type="primary", use_container_width=True, key="confirm_optimize"):
                st.session_state.show_optimizer = False
                st.session_state.optimizing = True
                st.rerun()
        with col_no:
            if st.button("Cancel", use_container_width=True, key="cancel_optimize"):
                st.session_state.show_optimizer = False
                st.rerun()

    # Action buttons
    btn_cols = st.columns([1, 1])
    with btn_cols[0]:
        submit = st.button("Route & Submit", type="primary", use_container_width=True)
    with btn_cols[1]:
        escalate = st.button("Force Large Model", use_container_width=True)

    if submit:
        handle_submit(st.session_state.get("main_prompt_input", ""), force_escalate=False)
    if escalate:
        handle_submit(st.session_state.get("main_prompt_input", ""), force_escalate=True)

    # ── Response section ──
    if st.session_state.last_result:
        st.markdown("---")
        st.markdown('<p class="section-title">Response</p>', unsafe_allow_html=True)
        st.text_area(
            "Response",
            value=st.session_state.last_result.response,
            height=250,
            disabled=True,
            label_visibility="collapsed",
        )

with right_col:
    # ── Sliding Scales Section ──
    st.markdown('<p class="section-title">Thresholds</p>', unsafe_allow_html=True)
    
    # Define scale names in order
    scale_names = [
        "Math",
        "Code Operations", 
        "Reasoning",
        "Agentic Tool Use",
        "Long Context",
        "General QA"
    ]
    
    # Create two columns for the scales
    scale_col1, scale_col2 = st.columns(2)
    
    # Left column: First 3 scales
    with scale_col1:
        for scale_name in scale_names[:3]:
            st.markdown(f"**{scale_name}**")
            
            # Single slider for each scale
            threshold = st.slider(
                f"{scale_name} Threshold",
                min_value=0.0,
                max_value=1.0,
                value=st.session_state.sliders[scale_name],
                step=0.05,
                key=f"{scale_name}_threshold",
                label_visibility="collapsed"
            )
            
            # Update session state
            st.session_state.sliders[scale_name] = threshold
            
            # Visual indicator showing the threshold position
            st.markdown(f"""
                <div style="background: linear-gradient(90deg, 
                    rgba(239,68,68,0.2) 0%, 
                    rgba(239,68,68,0.2) {threshold*100}%, 
                    rgba(34,197,94,0.3) {threshold*100}%, 
                    rgba(34,197,94,0.3) 100%);
                    height: 8px; border-radius: 4px; margin-bottom: 1rem;">
                </div>
            """, unsafe_allow_html=True)
    
    # Right column: Last 3 scales
    with scale_col2:
        for scale_name in scale_names[3:]:
            st.markdown(f"**{scale_name}**")
            
            # Single slider for each scale
            threshold = st.slider(
                f"{scale_name} Threshold",
                min_value=0.0,
                max_value=1.0,
                value=st.session_state.sliders[scale_name],
                step=0.05,
                key=f"{scale_name}_threshold",
                label_visibility="collapsed"
            )
            
            # Update session state
            st.session_state.sliders[scale_name] = threshold
            
            # Visual indicator showing the threshold position
            st.markdown(f"""
                <div style="background: linear-gradient(90deg, 
                    rgba(239,68,68,0.2) 0%, 
                    rgba(239,68,68,0.2) {threshold*100}%, 
                    rgba(34,197,94,0.3) {threshold*100}%, 
                    rgba(34,197,94,0.3) 100%);
                    height: 8px; border-radius: 4px; margin-bottom: 1rem;">
                </div>
            """, unsafe_allow_html=True)

# ── Results Section (below input) ──
if st.session_state.last_result:
    result = st.session_state.last_result

    # Create columns for results display
    results_col1, results_col2 = st.columns([7, 3], gap="medium")
    
    with results_col1:
        # ── Response Display ──
        st.markdown('<p class="section-title">Response</p>', unsafe_allow_html=True)
        st.text_area(
            "Response",
            value=result.response,
            height=200,
            disabled=True,
            label_visibility="collapsed"
        )
        
        # ── Subtasks ──
        if result.classification and result.classification.subtasks:
            st.markdown('<p class="section-title">Subtasks</p>', unsafe_allow_html=True)
            for i, task in enumerate(result.classification.subtasks, 1):
                st.markdown(f"{i}. {task}")
    
    with results_col2:
        # ── Routing Decision ──
        st.markdown('<p class="section-title">Routing Decision</p>', unsafe_allow_html=True)

        tier = "small" if result.model_used == "small" else "large"
        st.markdown(
            f"""<div class="routing-card {tier}">
                <span class="label">Model:</span> {model_badge(result.model_used, result.model_id)}<br>
                <span class="label">Category:</span> {result.classification.dominant_category if result.classification else "—"}<br>
                <span class="label">Reason:</span> {result.routing_reason}
            </div>""",
            unsafe_allow_html=True,
        )

        if result.classification:
            st.progress(result.classification.difficulty, text=f"Difficulty  {result.classification.difficulty:.2f}")

        # ── Cost Analysis ──
        st.markdown("---")
        st.markdown('<p class="section-title">Cost Analysis</p>', unsafe_allow_html=True)

        m1, m2 = st.columns(2)
        with m1:
            st.metric("Request cost", f"${result.cost_usd:.6f}")
        with m2:
            if result.model_used == "small":
                large_cost = estimate_large_model_cost(result)
                savings = large_cost - result.cost_usd
                st.metric("If large model", f"${large_cost:.6f}", delta=f"-${savings:.6f}", delta_color="inverse")
            else:
                st.metric("If large model", "same")

        m3, m4, m5 = st.columns(3)
        with m3:
            st.metric("Session total", f"${st.session_state.session_cost:.6f}")
        with m4:
            st.metric("Tokens in", result.input_tokens)
        with m5:
            st.metric("Tokens out", result.output_tokens)

        st.metric("Latency", f"{result.latency_ms:.0f} ms")

# ── History ──
if st.session_state.history:
    st.markdown("---")
    st.markdown('<p class="section-title">History</p>', unsafe_allow_html=True)

    history_display = []
    for h in st.session_state.history:
        history_display.append({
            "Prompt": h["prompt"],
            "Model": model_badge(h["model_used"], h["model"]),
            "Category": h["category"],
            "Cost": h["cost"],
            "Latency": h["latency"],
        })

    st.dataframe(history_display, use_container_width=True, hide_index=True)
