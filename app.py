import streamlit as st
import time
import random
from models import CompletionResult, Classification

# Try to import real implementations, fall back to stubs
try:
    from router import route
    from demo_prompts import DEMO_PROMPTS
    USE_STUB = False
except ImportError:
    USE_STUB = True

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


def handle_submit(prompt: str, force_escalate: bool):
    """Process a routing request and update session state."""
    if not prompt.strip():
        st.error("Please enter a prompt")
        return
    
    with st.spinner("Routing..." if not force_escalate else "Sending to large model..."):
        if USE_STUB:
            result = stub_route(prompt, force_escalate)
        else:
            result = route(prompt, force_escalate)
    
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


# Page config
st.set_page_config(page_title="Hybrid LLM Router", layout="wide")

# Run startup checks
import startup
startup.run()

# Agent 5: Prompt Helper import
from prompt_helper import suggest_prompt_rewrite

# Session state
if "history" not in st.session_state:
    st.session_state.history = []
if "session_cost" not in st.session_state:
    st.session_state.session_cost = 0.0
if "last_result" not in st.session_state:
    st.session_state.last_result = None
if "sidebar_copied_prompt" not in st.session_state:
    st.session_state.sidebar_copied_prompt = ""

# Header
st.title("🔀 Hybrid LLM Router")

# Layout
left_col, right_col = st.columns([6, 4])

with left_col:
    st.subheader("Input")
    
    # Prompt selection
    selected = st.selectbox(
        "Choose a demo prompt or write your own:",
        options=range(len(DEMO_PROMPTS)),
        format_func=lambda i: DEMO_PROMPTS[i]["label"]
    )
    
    # Text input
    is_custom = DEMO_PROMPTS[selected]["label"] == "Custom..."
    prompt_value = st.session_state.get("sidebar_copied_prompt") or ("" if is_custom else DEMO_PROMPTS[selected]["prompt"])
    
    prompt = st.text_area(
        "Prompt:",
        value=prompt_value,
        height=100,
        placeholder="Enter your prompt here..." if is_custom else None
    )
    
    # Buttons
    col1, col2 = st.columns([1, 1])
    with col1:
        submit = st.button("Submit", type="primary", use_container_width=True)
    with col2:
        escalate = st.button("⬆ Force Escalate", use_container_width=True)
    
    # Handle submissions
    if submit:
        handle_submit(prompt, force_escalate=False)
    if escalate:
        handle_submit(prompt, force_escalate=True)
    
    # Response display
    if st.session_state.last_result:
        st.markdown("---")
        st.subheader("Response")
        st.text_area(
            "Response:",
            value=st.session_state.last_result.response,
            height=200,
            disabled=True,
            label_visibility="collapsed"
        )

with right_col:
    # ── Agent 5: Prompt Helper Agent ──────────────────────────────────────
    # Initialize helper session state
    if "helper_suggestion" not in st.session_state:
        st.session_state.helper_suggestion = None
    if "last_analyzed_prompt" not in st.session_state:
        st.session_state.last_analyzed_prompt = ""
    if "show_helper" not in st.session_state:
        st.session_state.show_helper = True
    
    # Auto-analyze the current prompt
    current_prompt = prompt.strip() if 'prompt' in locals() else ""
    
    if current_prompt and current_prompt != st.session_state.last_analyzed_prompt:
        try:
            suggestion = suggest_prompt_rewrite(current_prompt)
        except Exception:
            suggestion = None
        
        if suggestion is None:
            from prompt_helper import stub_suggest
            suggestion = stub_suggest(current_prompt)
        
        st.session_state.helper_suggestion = suggestion
        st.session_state.last_analyzed_prompt = current_prompt
    
    # Show compact agent popup if there's a suggestion
    if st.session_state.helper_suggestion and current_prompt and st.session_state.show_helper:
        s = st.session_state.helper_suggestion
        
        # Determine if optimization is valuable
        has_optimization = s.get("rewrite") and s.get("rewrite") != current_prompt
        will_save = s.get("will_save_cost", False)
        
        if has_optimization and will_save:
            # Show optimization popup
            with st.container():
                st.markdown(
                    """
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                border-radius: 10px; padding: 15px; margin-bottom: 20px;
                                box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                        <div style="display: flex; align-items: center; justify-content: space-between;">
                            <div style="color: white;">
                                <div style="font-size: 18px; font-weight: bold; margin-bottom: 5px;">
                                    🤖 Agent Suggestion
                                </div>
                                <div style="font-size: 12px; opacity: 0.9;">
                                    I can optimize this for the small model
                                </div>
                            </div>
                            <div style="background: rgba(255,255,255,0.2); border-radius: 20px; 
                                        padding: 5px 12px; color: white; font-size: 12px; font-weight: bold;">
                                💰 Save cost
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
                # Compact info
                col1, col2 = st.columns(2)
                with col1:
                    route_emoji = "🟢" if s.get("predicted_route") == "small" else "🔴"
                    st.caption(f"{route_emoji} {s.get('predicted_route', '—').title()} model")
                with col2:
                    st.caption(f"Difficulty: {s.get('predicted_difficulty', 0):.1f}")
                
                # Show optimized prompt in expander
                with st.expander("📝 See optimized prompt", expanded=False):
                    st.info(s.get("rewrite", ""))
                    st.caption(f"💡 {s.get('explanation', '')}")
                
                # Action buttons
                col1, col2 = st.columns([2, 1])
                with col1:
                    if st.button("✨ Use this", use_container_width=True, type="primary", key="use_optimized"):
                        st.session_state["sidebar_copied_prompt"] = s.get("rewrite", "")
                        st.session_state.last_analyzed_prompt = ""
                        st.rerun()
                with col2:
                    if st.button("✕", use_container_width=True, key="dismiss_helper"):
                        st.session_state.show_helper = False
                        st.rerun()
                
                st.markdown("---")
    
    if st.session_state.last_result:
        result = st.session_state.last_result
        
        # Routing Decision
        st.subheader("Routing Decision")
        
        # Color-coded container
        border_color = "#28a745" if result.model_used == "small" else "#fd7e14"
        st.markdown(
            f"""
            <div style="border: 2px solid {border_color}; border-radius: 5px; padding: 15px; margin-bottom: 20px;">
                <p style="margin: 5px 0;"><strong>Model:</strong> {model_badge(result.model_used, result.model_id)}</p>
                <p style="margin: 5px 0;"><strong>Category:</strong> {result.classification.dominant_category if result.classification else "—"}</p>
                <p style="margin: 5px 0;"><strong>Difficulty:</strong> {result.classification.difficulty if result.classification else "—"}</p>
                <p style="margin: 5px 0;"><strong>Reason:</strong> {result.routing_reason}</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Difficulty progress bar
        if result.classification:
            st.progress(result.classification.difficulty, text=f"Difficulty: {result.classification.difficulty:.2f}")
        
        # Cost breakdown
        st.markdown("---")
        st.subheader("Cost")
        
        st.metric("This request", f"${result.cost_usd:.6f}")
        
        if result.model_used == "small":
            large_cost = estimate_large_model_cost(result)
            savings = large_cost - result.cost_usd
            st.metric(
                "Large model would cost",
                f"${large_cost:.6f}",
                delta=f"-${savings:.6f}",
                delta_color="inverse"
            )
        else:
            st.metric("Large model would cost", "—")
        
        st.metric("Session total", f"${st.session_state.session_cost:.6f}")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Tokens in", result.input_tokens)
        with col2:
            st.metric("Tokens out", result.output_tokens)
        
        st.metric("Latency", f"{result.latency_ms:.0f}ms")
        
        # Subtasks
        if result.classification and result.classification.subtasks:
            st.markdown("---")
            st.subheader("Subtasks")
            for i, task in enumerate(result.classification.subtasks, 1):
                st.markdown(f"{i}. {task}")
    
    # History
    if st.session_state.history:
        st.markdown("---")
        st.subheader("History")
        
        # Format history for display
        history_display = []
        for h in st.session_state.history:
            history_display.append({
                "Prompt": h["prompt"],
                "Model": model_badge(h["model_used"], h["model"]),
                "Category": h["category"],
                "Cost": h["cost"],
                "Latency": h["latency"],
            })
        
        st.dataframe(
            history_display,
            use_container_width=True,
            hide_index=True
        )
        
        # Re-enable helper button if dismissed
        if not st.session_state.show_helper:
            if st.button("🤖 Show agent suggestions", use_container_width=True):
                st.session_state.show_helper = True
                st.rerun()
