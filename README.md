# 🤖 TalentScout AI Hiring Assistant

**An intelligent, conversational AI agent for conducting initial candidate screenings, powered by Large Language Models and a robust state machine architecture.**

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35-red?style=for-the-badge&logo=streamlit)
![Groq](https://img.shields.io/badge/Groq-Llama_3.1-orange?style=for-the-badge)

---

## 📍 Project Overview

[INSERT_A_GIF_OF_YOUR_APP_IN_ACTION_HERE]

*A GIF is highly recommended. Use a tool like Giphy Capture or ScreenToGif to record a short (10-15 second) walkthrough of your app.*

[cite_start]TalentScout AI is a sophisticated chatbot designed to automate the initial screening phase of the recruitment process. [cite: 5] Built for a fictional tech recruitment agency, this tool demonstrates a practical application of Large Language Models in a real-world business scenario. [cite_start]The assistant engages candidates in a natural, multi-stage conversation to gather essential information and conduct a tailored technical assessment based on their specific skills. [cite: 5]

### ✨ Key Features

* [cite_start]**🗣️ Multi-Stage Conversational Flow:** Guides the candidate through a logical sequence of steps, from personal details to a technical deep-dive. [cite: 11, 34]
* **🎙️ Voice & Text Input:** Offers a flexible user experience, allowing candidates to respond via typing or microphone for more natural interaction.
* [cite_start]**🧠 Dynamic Technical Assessment:** Generates relevant technical questions based on the candidate's declared role, experience level, and tech stack, ensuring a personalized screening. [cite: 10, 31]
* **🤖 Intelligent Response Handling:** The AI is engineered to handle various conversational scenarios, including vague answers, requests for clarification, and topic skips, making the interaction feel more human.
* **📝 Automated Interview Summary:** Upon completion, the AI synthesizes the entire conversation into a structured summary report, evaluating the candidate's strengths and weaknesses for the hiring manager.
* [cite_start]**✨ Polished & Professional UI:** A custom-styled, dark-themed interface built with Streamlit provides a clean, intuitive, and impressive user experience. [cite: 15, 90]

---

## 🚀 Technical Architecture & Details

This project is built on a modular and scalable architecture that separates concerns for maintainability and clarity.

* **State Machine Core:** The entire application is orchestrated by a robust state machine managed within Streamlit's `session_state`. [cite_start]This ensures the conversation follows a logical path and maintains context across user interactions. [cite: 34]
* **Modular Structure:**
    * `app.py`: The main application entry point, handling UI rendering and state management.
    * `prompts.py`: A dedicated module that contains all LLM prompts. This separation allows for easy tuning and refinement of the AI's persona and logic.
    * `utils.py`: A utility module for deterministic, rule-based validation (e.g., email, phone number), making the app more efficient.
* **Key Technologies:**
    * [cite_start]**Frontend:** Streamlit [cite: 43]
    * [cite_start]**LLM:** Groq API with the `llama-3.3-70b-versatile` model [cite: 44]
    * **Voice Processing:** `streamlit-mic-recorder` for audio capture, `pydub` for format conversion, and `SpeechRecognition` for speech-to-text.
    * [cite_start]**Performance:** The application uses the `AsyncGroq` client and `asyncio` to handle API calls without blocking Streamlit's main event loop, ensuring a smooth and responsive UI. [cite: 92]

---

## 💡 Prompt Design: The Core Intelligence

The effectiveness of this assistant is rooted in sophisticated prompt engineering. Instead of relying on simple text responses, the application uses a structured and rule-based approach.

* [cite_start]**Structured JSON Outputs:** Every prompt instructs the LLM to return a JSON object. [cite: 50, 51] This transforms the LLM from an unpredictable text generator into a reliable API, allowing the Python backend to make deterministic decisions based on the AI's output.
* [cite_start]**Context-Aware Generation:** Prompts are dynamically formatted with the candidate's profile (experience, role, tech stack) and the conversation history to generate highly relevant and personalized questions. [cite: 10]
* **Advanced Conversational Logic:** The main assessment prompt includes a complex rule set that enables the AI to:
    * **Challenge Vague Answers:** Asks for elaboration on non-answers like "yes" or "sure."
    * **Handle Clarification Requests:** Rephrases its own question if the candidate is confused.
    * **Ask Varied Questions:** Is instructed to ask new, distinct questions to broaden the assessment rather than getting stuck on a single topic.

---

## 🛠️ Installation & Usage

### Prerequisites

* Python 3.10+
* FFmpeg (for voice processing). Can be installed with Chocolatey on Windows (`choco install ffmpeg`) or Homebrew on macOS (`brew install ffmpeg`).

### Setup

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url.git>
    cd <your-repo-name>
    ```

2.  **Create and configure the environment file:**
    * Rename the example environment file:
        ```bash
        mv .env.example .env
        ```
    * Open the `.env` file and add your Groq API key:
        ```
        GROQ_API_KEY="your_actual_key_here"
        ```

3.  **Set up the Python virtual environment:**
    ```bash
    # Create the virtual environment
    python -m venv venv

    # Activate it
    # On Windows:
    venv\Scripts\activate
    # On macOS/Linux:
    source venv/bin/activate
    ```

4.  **Install the dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

### Running the Application

Once the setup is complete, run the Streamlit app from your terminal:
```bash
streamlit run app.py