# 📘 Study Assistant

**Study Assistant** is an AI-powered tool designed to help students and professionals study smarter by extracting key information from PDFs, enabling interactive Q&A, and generating concise summaries.

---

## 🚀 Features

- 📂 **PDF Parsing** – Extracts clean text and structure from PDF documents.  
- ❓ **Interactive Q&A** – Ask questions about the PDF and get precise AI-powered answers.  
- 📝 **Summarization** – Generate concise summaries to speed up your revision.  
- ⚡ **Lightweight & Modular** – Easy to run and extend with minimal setup.  

---

## 📑 Table of Contents

1. [Features](#-features)  
2. [Installation](#-installation)  
3. [Usage](#-usage)  
   - [Run via `app.py`](#run-via-apppy)  
   - [Use `parser.py`](#use-parserpy)  
4. [Configuration](#-configuration)  
5. [Requirements](#-requirements)  
6. [Project Structure](#-project-structure)  
7. [Contributing](#-contributing)  
8. [License](#-license)  
9. [Author](#-author)

---

## ⚙️ Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Qamber02/Study_Assistant.git
   cd Study_Assistant
   ```

2. **Create a virtual environment (recommended)**
   ```bash
   python -m venv venv
   source venv/bin/activate   # On Linux/Mac
   venv\Scripts\activate      # On Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

---

## ▶️ Usage

### Run via `app.py`
```bash
python app.py --pdf path/to/your/document.pdf
```

👉 Once loaded, you can:  
- Ask questions about the document  
- Generate summaries of the content  

---

### Use `parser.py`
```bash
python parser.py --input path/to/document.pdf --summary --qa
```

Options:  
- `--summary` → Output a concise summary of the document  
- `--qa` → Start an interactive Q&A session  

---

## 🔧 Configuration

Set up environment variables (if required):

- `OPENAI_API_KEY` → Your OpenAI or Gemini API key for AI integration  
- `PDF_PARSER_MODE` → Choose parsing mode: `"fast"` or `"accurate"`  

---

## 📋 Requirements

- **Python 3.7+**  
- Dependencies listed in `requirements.txt`  

Install all dependencies with:
```bash
pip install -r requirements.txt
```

---

## 📂 Project Structure

```
Study_Assistant/
├── app.py             # Main interactive entry point
├── parser.py          # PDF parsing and Q&A logic
├── gemini_utils.py    # Utility functions for AI integrations
├── requirements.txt   # Project dependencies
├── .gitignore         # Ignored files for Git
└── README.md          # Project documentation
```

---

## 🤝 Contributing

Contributions are always welcome!  

1. Fork the repository  
2. Create a feature branch  
   ```bash
   git checkout -b feature/YourFeature
   ```
3. Commit your changes and push the branch  
4. Open a Pull Request  

---

## 📜 License

This project is licensed under the **MIT License**.  
See the [LICENSE](LICENSE) file for details.  

---

## 👨‍💻 Author

**Qamber**  
- GitHub: [Qamber02](https://github.com/Qamber02)    

---
