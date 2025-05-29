import streamlit as st
import os
import json
from gemini_utils import call_gemini
from parser import extract_text
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()  # Loads the .env file

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def main():
    st.set_page_config(page_title="🧠 AI StudyMate", layout="wide")
    st.title("🧠 AI StudyMate – Your Smart File-Based Learning Companion")

    uploaded_files = st.file_uploader(
        "Upload your study material (PDF, DOCX, PPTX, TXT, PY, JAVA, CPP, JS)",
        type=['pdf', 'docx', 'pptx', 'txt', 'py', 'java', 'cpp', 'js'],
        accept_multiple_files=True
    )

    if not uploaded_files:
        st.info("Please upload at least one file to get started.")
        return

    for file in uploaded_files:
        process_file(file)


def process_file(file):
    temp_path = os.path.join(st.session_state.get('temp_dir', '.'), file.name)
    with open(temp_path, "wb") as f:
        f.write(file.getvalue())
    content = extract_text(temp_path)
    os.remove(temp_path)

    st.markdown(f"## 📄 {file.name}")
    st.markdown("---")

    preview = content[:5000]
    show_explanations(preview)
    quiz_key = f"quiz_{file.name}"

    if st.button("Generate Quiz", key=f"btn_{file.name}"):
        st.session_state[quiz_key] = fetch_quiz(preview)

    if quiz_key in st.session_state:
        if st.session_state[quiz_key]:
            render_quiz(st.session_state[quiz_key], quiz_key)
        else:
            st.error("⚠️ Failed to generate quiz. Please try again.")


def show_explanations(preview):
    for title, prefix in [
        ("### 📘 Detailed Explanation", "Explain the following in detail:"),
        ("### 📗 Simplified Explanation", "Explain this in simple terms someone new could understand:")
    ]:
        with st.spinner(f"Generating {title.lower()}..."):
            resp = call_gemini(f"{prefix}\n\n{preview}")
        st.markdown(title)
        st.write(resp)


def fetch_quiz(preview):
    with st.spinner("Creating interactive quiz..."):
        prompt = (
            "Generate quiz questions as JSON with keys: multiple_choice, true_false. "
            "Each must include 'question', 'options', and 'answer'. Return only valid JSON."
            f"\n\n{preview}"
        )
        raw = call_gemini(prompt)
    txt = raw.strip()
    if txt.startswith("```json"):
        txt = txt[txt.find('{'):txt.rfind('}')+1]
    try:
        data = json.loads(txt)
        if not any(data.get(k) for k in ["multiple_choice","true_false"]):
            return None
        return data
    except json.JSONDecodeError:
        return None


def render_quiz(data, key):
    st.markdown("### 🧪 Interactive Quiz")
    mcqs = data.get("multiple_choice", [])
    tfqs = data.get("true_false", [])
    total = len(mcqs) + len(tfqs)
    if total == 0:
        st.warning("No quiz questions available.")
        return

    form = st.form(key=f"form_{key}")
    answers = {}
    placeholders = {"mc": "Select an option...", "tf": "Select True/False..."}
    qcount = 1

    form.markdown("#### 📝 Multiple Choice Questions")
    for idx, q in enumerate(mcqs):
        opts = [placeholders['mc']] + q['options']
        ans = form.selectbox(f"Q{qcount}: {q['question']}", opts, key=f"mc_{key}_{idx}")
        answers[f"mc_{idx}"] = {'user': ans, 'correct': q['answer']}
        qcount += 1

    form.markdown("#### ✅ True/False Questions")
    for idx, q in enumerate(tfqs):
        opts = [placeholders['tf'], "True", "False"]
        ans = form.selectbox(f"Q{qcount}: {q['question']}", opts, key=f"tf_{key}_{idx}")
        answers[f"tf_{idx}"] = {'user': ans, 'correct': str(q['answer']).capitalize()}
        qcount += 1

    submit = form.form_submit_button("Submit Quiz")
    if submit:
        unanswered = [k for k,v in answers.items() if v['user'] in placeholders.values()]
        if unanswered:
            st.warning("Please answer all questions before submitting.")
            return
        score = sum(1 for v in answers.values() if v['user']==v['correct'])
        pct = score/total*100
        st.success(f"You scored {score}/{total} ({pct:.1f}%)")
        feedback = ("🎉 Excellent!" if pct>=80 else "👍 Good job!" if pct>=60 else "📚 Keep practicing!")
        st.info(feedback)

        st.markdown("---")
        st.markdown("### 📝 Answers Review")
        for v in answers.values():
            st.write(f"Your: {v['user']} | Correct: {v['correct']}")

        if st.button("Try Again", key=f"retry_{key}"):
            for k in list(st.session_state):
                if k.startswith((f"mc_{key}", f"tf_{key}", key)):
                    del st.session_state[k]
            st.experimental_rerun()

if __name__ == "__main__":
    main()
