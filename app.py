import streamlit as st
import os
import json
import tempfile
import logging
from pathlib import Path

from dotenv import load_dotenv
import google.generativeai as genai

from gemini_utils import call_gemini
from parser import extract_text

# ─── Logging ────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ─── Environment ────────────────────────────────────────────────────────────
load_dotenv()

_api_key = os.getenv("GOOGLE_API_KEY")
if not _api_key:
    raise EnvironmentError(
        "GOOGLE_API_KEY is not set. "
        "Add it to your .env file or environment variables."
    )
genai.configure(api_key=_api_key)

# ─── Constants ───────────────────────────────────────────────────────────────
SUPPORTED_TYPES = ["pdf", "docx", "pptx", "txt", "py", "java", "cpp", "js"]
PREVIEW_CHAR_LIMIT = 5000

EXPLANATION_PROMPTS = [
    ("📘 Detailed Explanation", "Explain the following content in full detail, covering key concepts, context, and examples:"),
    ("📗 Simplified Explanation", "Explain this content in simple terms as if teaching a complete beginner. Use analogies and avoid jargon:"),
]

QUIZ_PROMPT_TEMPLATE = """
Generate a quiz based on the content below. Return ONLY valid JSON — no markdown, no backticks, no explanation.

Required structure:
{{
  "multiple_choice": [
    {{"question": "...", "options": ["A", "B", "C", "D"], "answer": "A"}}
  ],
  "true_false": [
    {{"question": "...", "options": ["True", "False"], "answer": "True"}}
  ]
}}

Generate at least 3 multiple choice and 2 true/false questions.

Content:
{content}
"""


# ─── Session State Init ──────────────────────────────────────────────────────
def init_session_state() -> None:
    defaults = {
        "temp_dir": tempfile.mkdtemp(),
        "explanations": {},   # file_name -> {title: text}
        "quizzes": {},        # file_name -> quiz data
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


# ─── File Processing ─────────────────────────────────────────────────────────
def extract_file_content(file) -> str | None:
    """Save uploaded file to temp dir, extract text, clean up."""
    temp_path = Path(st.session_state["temp_dir"]) / file.name
    try:
        temp_path.write_bytes(file.getvalue())
        content = extract_text(str(temp_path))
        if not content or not content.strip():
            st.warning(f"⚠️ Could not extract text from **{file.name}**. The file may be empty or unsupported.")
            logger.warning("Empty content extracted from %s", file.name)
            return None
        return content
    except Exception as e:
        st.error(f"❌ Failed to read **{file.name}**: {e}")
        logger.exception("Error extracting text from %s", file.name)
        return None
    finally:
        if temp_path.exists():
            temp_path.unlink()


# ─── Explanations ────────────────────────────────────────────────────────────
def get_explanations(file_name: str, preview: str) -> dict:
    """
    Returns cached explanations or generates + caches them.
    Avoids re-calling the API on every Streamlit rerun.
    """
    cache = st.session_state["explanations"]
    if file_name in cache:
        return cache[file_name]

    results = {}
    for title, prompt_prefix in EXPLANATION_PROMPTS:
        with st.spinner(f"Generating {title}..."):
            try:
                response = call_gemini(f"{prompt_prefix}\n\n{preview}")
                results[title] = response
            except Exception as e:
                results[title] = f"⚠️ Could not generate explanation: {e}"
                logger.exception("Explanation error for %s | %s", file_name, title)

    cache[file_name] = results
    return results


def show_explanations(file_name: str, preview: str) -> None:
    explanations = get_explanations(file_name, preview)
    for title, content in explanations.items():
        st.markdown(f"### {title}")
        st.write(content)
        st.markdown("")


# ─── Quiz ────────────────────────────────────────────────────────────────────
def fetch_quiz(preview: str) -> dict | None:
    """Call Gemini to generate a quiz; returns parsed dict or None on failure."""
    prompt = QUIZ_PROMPT_TEMPLATE.format(content=preview)
    with st.spinner("Creating interactive quiz..."):
        try:
            raw = call_gemini(prompt)
        except Exception as e:
            logger.exception("Quiz generation error: %s", e)
            return None

    # Strip accidental markdown fences
    txt = raw.strip()
    if "```" in txt:
        start = txt.find("{")
        end = txt.rfind("}") + 1
        if start == -1 or end == 0:
            logger.error("No JSON object found in quiz response.")
            return None
        txt = txt[start:end]

    try:
        data = json.loads(txt)
    except json.JSONDecodeError as e:
        logger.error("JSON decode error in quiz response: %s\nRaw: %s", e, txt[:500])
        return None

    has_mcq = bool(data.get("multiple_choice"))
    has_tf = bool(data.get("true_false"))
    if not has_mcq and not has_tf:
        logger.warning("Quiz data parsed but contained no questions.")
        return None

    return data


def render_quiz(data: dict, quiz_key: str) -> None:
    st.markdown("### 🧪 Interactive Quiz")

    mcqs: list = data.get("multiple_choice", [])
    tfqs: list = data.get("true_false", [])
    total = len(mcqs) + len(tfqs)

    if total == 0:
        st.warning("No quiz questions were generated.")
        return

    PLACEHOLDER_MC = "Select an option..."
    PLACEHOLDER_TF = "Select True / False..."

    with st.form(key=f"quiz_form_{quiz_key}"):
        answers: dict[str, dict] = {}
        qcount = 1

        if mcqs:
            st.markdown("#### 📝 Multiple Choice")
            for idx, q in enumerate(mcqs):
                options = [PLACEHOLDER_MC] + q.get("options", [])
                selected = st.selectbox(
                    f"Q{qcount}: {q['question']}",
                    options,
                    key=f"mc_{quiz_key}_{idx}",
                )
                answers[f"mc_{idx}"] = {
                    "user": selected,
                    "correct": str(q["answer"]),
                    "question": q["question"],
                }
                qcount += 1

        if tfqs:
            st.markdown("#### ✅ True / False")
            for idx, q in enumerate(tfqs):
                options = [PLACEHOLDER_TF, "True", "False"]
                selected = st.selectbox(
                    f"Q{qcount}: {q['question']}",
                    options,
                    key=f"tf_{quiz_key}_{idx}",
                )
                answers[f"tf_{idx}"] = {
                    "user": selected,
                    "correct": str(q["answer"]).capitalize(),
                    "question": q["question"],
                }
                qcount += 1

        submitted = st.form_submit_button("✅ Submit Quiz")

    if not submitted:
        return

    placeholders = {PLACEHOLDER_MC, PLACEHOLDER_TF}
    unanswered = [k for k, v in answers.items() if v["user"] in placeholders]
    if unanswered:
        st.warning(f"Please answer all {len(unanswered)} remaining question(s) before submitting.")
        return

    score = sum(1 for v in answers.values() if v["user"] == v["correct"])
    pct = score / total * 100

    col1, col2 = st.columns([1, 2])
    col1.metric("Score", f"{score}/{total}", f"{pct:.1f}%")

    if pct >= 80:
        col2.success("🎉 Excellent! You nailed it.")
    elif pct >= 60:
        col2.info("👍 Good job! A bit more revision and you'll ace it.")
    else:
        col2.warning("📚 Keep practicing! Review the material and try again.")

    st.markdown("---")
    st.markdown("### 📋 Answer Review")
    for v in answers.values():
        is_correct = v["user"] == v["correct"]
        icon = "✅" if is_correct else "❌"
        st.markdown(
            f"{icon} **{v['question']}**  \n"
            f"Your answer: `{v['user']}` | Correct: `{v['correct']}`"
        )

    if st.button("🔄 Reset Quiz", key=f"reset_{quiz_key}"):
        # Clear only this quiz's state
        keys_to_clear = [k for k in st.session_state if quiz_key in k]
        for k in keys_to_clear:
            del st.session_state[k]
        st.rerun()


# ─── Per-File UI ─────────────────────────────────────────────────────────────
def process_file(file) -> None:
    content = extract_file_content(file)
    if not content:
        return

    preview = content[:PREVIEW_CHAR_LIMIT]
    quiz_state_key = f"quiz__{file.name}"

    st.markdown(f"## 📄 {file.name}")
    st.caption(f"{len(content):,} characters extracted")
    st.markdown("---")

    with st.expander("📖 Explanations", expanded=True):
        show_explanations(file.name, preview)

    st.markdown("---")

    col1, col2 = st.columns([1, 5])
    with col1:
        generate = st.button("🎲 Generate Quiz", key=f"gen_quiz__{file.name}")
    with col2:
        if quiz_state_key in st.session_state:
            if st.button("🗑️ Clear Quiz", key=f"clear_quiz__{file.name}"):
                del st.session_state[quiz_state_key]
                st.rerun()

    if generate:
        quiz_data = fetch_quiz(preview)
        if quiz_data:
            st.session_state[quiz_state_key] = quiz_data
        else:
            st.error("⚠️ Quiz generation failed. The model response was invalid. Try again.")

    if quiz_state_key in st.session_state and st.session_state[quiz_state_key]:
        render_quiz(st.session_state[quiz_state_key], quiz_state_key)


# ─── App Entry Point ─────────────────────────────────────────────────────────
def main() -> None:
    st.set_page_config(
        page_title="🧠 AI StudyMate",
        page_icon="🧠",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    init_session_state()

    st.title("🧠 AI StudyMate")
    st.caption("Upload your study material and get instant explanations + quizzes powered by Gemini.")

    uploaded_files = st.file_uploader(
        "Upload study material",
        type=SUPPORTED_TYPES,
        accept_multiple_files=True,
        help=f"Supported: {', '.join(f'.{t}' for t in SUPPORTED_TYPES)}",
    )

    if not uploaded_files:
        st.info("👆 Upload one or more files above to get started.")
        return

    for file in uploaded_files:
        with st.container():
            process_file(file)
            st.markdown("<br>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
