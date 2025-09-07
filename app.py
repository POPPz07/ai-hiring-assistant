import streamlit as st
import os
import json
import random
import re
import io
import asyncio
from groq import AsyncGroq
from dotenv import load_dotenv
import speech_recognition as sr
from streamlit_mic_recorder import mic_recorder
from pydub import AudioSegment

# Load environment variables at the very top
load_dotenv()

# --- IMPORTS ---
from prompts import (
    get_name_gathering_prompt, get_email_gathering_prompt, get_phone_gathering_prompt,
    get_experience_gathering_prompt, get_position_gathering_prompt,
    get_location_gathering_prompt, get_tech_stack_gathering_prompt,
    get_assessment_response_prompt, get_coding_question_prompt, get_conclusion_prompt
)
from utils import is_valid_email, is_valid_phone, is_valid_experience

# --- UI & STYLING CONFIGURATION ---
st.set_page_config(page_title="TalentScout AI Assistant", page_icon="🤖", layout="centered")

st.markdown("""
<style>
    /* General body styling */
    body { background-color: #1a1a1a; color: #f0f2f6; }
    .stApp { background-color: #1a1a1a; }
    /* Main chat container */
    [data-testid="stChatMessages"] { background-color: #262730; border-radius: 10px; padding: 1rem; min-height: 500px; }
    /* Chat message styling */
    [data-testid="stChatMessage"] { background-color: transparent; border-radius: 10px; padding: 0.75rem; margin-bottom: 0.5rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    /* Assistant chat bubble */
    [data-testid="stChatMessage"]:has([data-testid="stAvatarIcon-assistant"]) { background-color: #333344; }
    /* User chat bubble */
    [data-testid="stChatMessage"]:has([data-testid="stAvatarIcon-user"]) { background-color: #004d40; text-align: right; color: white; }
    /* Make user messages align to the right */
    [data-testid="stChatMessage"]:has([data-testid="stAvatarIcon-user"]) > div > div { display: flex; flex-direction: row-reverse; text-align: right; }
    /* Input bar stuck to the bottom */
    [data-testid="stChatInput"] { background-color: #1a1a1a; border-top: 1px solid #444; padding-top: 1rem; }
    /* Title and Header styling */
    h1 { color: #00aaff; text-align: center; }
    .intro-card { background-color: #262730; border-radius: 10px; padding: 1.5rem; margin-bottom: 1.5rem; border: 1px solid #444; }
    /* Reset button styling */
    .stButton>button { background-color: #ff4b4b; color: white; border-radius: 5px; border: none; padding: 0.5rem 1rem; float: right; }
</style>
""", unsafe_allow_html=True)


# --- STATE MANAGEMENT ---
def reset_conversation():
    groq_client = st.session_state.groq_client if "groq_client" in st.session_state else None
    st.session_state.clear()
    
    st.session_state.messages = []
    st.session_state.conversation_stage = "greeting"
    st.session_state.candidate_info = { "full_name": None, "email": None, "phone_number": None, "experience_years": None, "desired_position": None, "current_location": None, "tech_stack": None }
    st.session_state.awaiting_position_choice = False
    st.session_state.question_plan = []
    st.session_state.current_topic_index = 0
    st.session_state.questions_asked_on_topic = 0
    st.session_state.coding_questions_asked = 0
    st.session_state.last_question_asked = ""
    st.session_state.question_history = []
    st.session_state.recorder_count = 0
    
    if groq_client:
        st.session_state.groq_client = groq_client

if "messages" not in st.session_state:
    reset_conversation()

if "groq_client" not in st.session_state:
    try:
        st.session_state.groq_client = AsyncGroq(api_key=os.environ.get("GROQ_API_KEY"))
    except Exception as e:
        st.error("Failed to initialize Groq client. Please check your API key.", icon="🚨")
        st.stop()


async def get_llm_response(prompt):
    try:
        chat_completion = await st.session_state.groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}], model="llama-3.3-70b-versatile",
            temperature=0.8, max_tokens=500, response_format={"type": "json_object"},
            timeout=20.0
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        st.error(f"Sorry, I'm having trouble connecting right now. Please try again. (Error: {e})", icon="🔥")
        return None

# --- UI RENDERING & LOGIC ---
col1, col2 = st.columns([3, 1])
with col1:
    st.title("🤖 TalentScout AI Assistant")
with col2:
    if st.button("Restart Interview 🔄"):
        reset_conversation()
        st.rerun()

# Show the intro card and first message ONLY on the very first run.
if st.session_state.conversation_stage == "greeting":
    with st.container(border=False):
        st.markdown("""
        <div class="intro-card">
        Welcome to your initial screening with <b>TalentScout</b>! I'm your AI assistant, designed to make this first step as smooth as possible. Here's how our session will work:
        <ul>
            <li><span style="font-size: 1.2em;">👤</span> <b>Information Gathering:</b> I'll start by collecting some essential details to build your candidate profile.</li>
            <li><span style="font-size: 1.2em;">🧠</span> <b>Technical Assessment:</b> I'll then ask a few technical questions tailored to your skills and the role you're interested in.</li>
            <li><span style="font-size: 1.2em;">💬</span> <b>Conversational Flow:</b> Please feel free to answer naturally. You can use the microphone for voice input or type your responses.</li>
        </ul>
        This process helps us get a great initial understanding of your expertise. Let's begin!
        </div>
        """, unsafe_allow_html=True)
    
    if not st.session_state.messages:
        initial_greeting = "Hello! I'm the AI Hiring Assistant from TalentScout. To start, could you please tell me your full name?"
        st.session_state.messages.append({"role": "assistant", "content": initial_greeting})

# Display all chat messages from history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- USER INPUT HANDLING ---
recognizer = sr.Recognizer()
audio_bytes = None
input_col, mic_col = st.columns([10, 1])
with input_col:
    user_input_text = st.chat_input("Your response...")
with mic_col:
    st.markdown(" ")
    audio_info = mic_recorder(start_prompt="🎤", stop_prompt="⏹️", key=f'recorder_{st.session_state.recorder_count}')

if audio_info:
    audio_bytes = audio_info['bytes']

user_input = None
if user_input_text:
    user_input = user_input_text
elif audio_bytes:
    try:
        audio_segment = AudioSegment.from_file(io.BytesIO(audio_bytes))
        wav_buffer = io.BytesIO()
        audio_segment.export(wav_buffer, format="wav")
        wav_buffer.seek(0)
        with sr.AudioFile(wav_buffer) as source:
            audio_data = recognizer.record(source)
        user_input = recognizer.recognize_google(audio_data)
    except Exception:
        st.warning("I couldn't understand the audio. Please try again or type your response.", icon="🤔")

if user_input:
    # First user interaction moves the stage from 'greeting' to 'gathering'
    if st.session_state.conversation_stage == "greeting":
        st.session_state.conversation_stage = "gathering_name"
        
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.spinner("Assistant is thinking..."):
        current_stage = st.session_state.conversation_stage
        
        # --- THE REST OF THE CHATBOT LOGIC ---
        if current_stage.startswith("gathering_"):
            if current_stage == "gathering_name":
                prompt = get_name_gathering_prompt(user_input, st.session_state.messages)
                llm_json_response_str = asyncio.run(get_llm_response(prompt))
                if llm_json_response_str:
                    try:
                        data = json.loads(llm_json_response_str)
                        response_text, is_valid = data.get("response"), data.get("is_valid", False)
                        st.session_state.messages.append({"role": "assistant", "content": response_text})
                        if is_valid:
                            st.session_state.candidate_info["full_name"] = user_input
                            st.session_state.conversation_stage = "gathering_email"
                    except json.JSONDecodeError:
                        st.session_state.messages.append({"role": "assistant", "content": "I had a little hiccup. Could you please repeat your name?"})
            elif current_stage == "gathering_email":
                if not is_valid_email(user_input):
                    prompt = get_email_gathering_prompt(user_input, st.session_state.messages)
                    llm_json_response_str = asyncio.run(get_llm_response(prompt))
                    if llm_json_response_str:
                        try:
                            data = json.loads(llm_json_response_str)
                            st.session_state.messages.append({"role": "assistant", "content": data.get("response")})
                        except json.JSONDecodeError:
                            st.session_state.messages.append({"role": "assistant", "content": "I had a little hiccup. Could you provide your email again?"})
                else:
                    st.session_state.candidate_info["email"] = user_input
                    st.session_state.messages.append({"role": "assistant", "content": "Thank you. Your email is recorded. Now, could you please provide your 10-digit phone number?"})
                    st.session_state.conversation_stage = "gathering_phone"
            elif current_stage == "gathering_phone":
                if not is_valid_phone(user_input):
                    prompt = get_phone_gathering_prompt(user_input, st.session_state.messages)
                    llm_json_response_str = asyncio.run(get_llm_response(prompt))
                    if llm_json_response_str:
                        try:
                            data = json.loads(llm_json_response_str)
                            st.session_state.messages.append({"role": "assistant", "content": data.get("response")})
                        except json.JSONDecodeError:
                            st.session_state.messages.append({"role": "assistant", "content": "I had a little hiccup. Could you provide your phone number again?"})
                else:
                    st.session_state.candidate_info["phone_number"] = user_input
                    st.session_state.messages.append({"role": "assistant", "content": "Thanks. How many years of professional experience do you have?"})
                    st.session_state.conversation_stage = "gathering_experience"
            elif current_stage == "gathering_experience":
                if not is_valid_experience(user_input):
                    prompt = get_experience_gathering_prompt(user_input, st.session_state.messages)
                    llm_json_response_str = asyncio.run(get_llm_response(prompt))
                    if llm_json_response_str:
                        try:
                            data = json.loads(llm_json_response_str)
                            st.session_state.messages.append({"role": "assistant", "content": data.get("response")})
                        except json.JSONDecodeError:
                            st.session_state.messages.append({"role": "assistant", "content": "I had a little hiccup. Could you provide your experience again?"})
                else:
                    st.session_state.candidate_info["experience_years"] = user_input
                    st.session_state.messages.append({"role": "assistant", "content": f"Great, {user_input} years. Which position(s) are you interested in?"})
                    st.session_state.conversation_stage = "gathering_position"
            elif current_stage == "gathering_position":
                prompt = get_position_gathering_prompt(user_input, st.session_state.messages, st.session_state.awaiting_position_choice)
                llm_json_response_str = asyncio.run(get_llm_response(prompt))
                if llm_json_response_str:
                    try:
                        data = json.loads(llm_json_response_str)
                        st.session_state.messages.append({"role": "assistant", "content": data.get("response")})
                        if st.session_state.awaiting_position_choice:
                            st.session_state.candidate_info["desired_position"] = data.get("role_chosen")
                            st.session_state.awaiting_position_choice = False
                            st.session_state.conversation_stage = "gathering_location"
                        else:
                            if data.get("role_count", 0) > 1:
                                st.session_state.awaiting_position_choice = True
                            elif data.get("role_count", 0) == 1:
                                st.session_state.candidate_info["desired_position"] = data.get("roles", [user_input])[0]
                                st.session_state.conversation_stage = "gathering_location"
                    except json.JSONDecodeError:
                         st.session_state.messages.append({"role": "assistant", "content": "I had a little hiccup. Could you clarify your desired position?"})
            elif current_stage == "gathering_location":
                prompt = get_location_gathering_prompt(user_input, st.session_state.messages)
                llm_json_response_str = asyncio.run(get_llm_response(prompt))
                if llm_json_response_str:
                    try:
                        data = json.loads(llm_json_response_str)
                        st.session_state.candidate_info["current_location"] = user_input
                        st.session_state.messages.append({"role": "assistant", "content": data.get("response")})
                        st.session_state.conversation_stage = "gathering_tech_stack"
                    except json.JSONDecodeError:
                         st.session_state.messages.append({"role": "assistant", "content": "I had a little hiccup. Could you repeat your location?"})
            elif current_stage == "gathering_tech_stack":
                prompt = get_tech_stack_gathering_prompt(user_input, st.session_state.messages)
                llm_json_response_str = asyncio.run(get_llm_response(prompt))
                if llm_json_response_str:
                    try:
                        data = json.loads(llm_json_response_str)
                        st.session_state.candidate_info["tech_stack"] = user_input
                        st.session_state.messages.append({"role": "assistant", "content": data.get("response")})
                        st.session_state.conversation_stage = "assessment_start"
                    except json.JSONDecodeError:
                        st.session_state.messages.append({"role": "assistant", "content": "I had a little hiccup. Could you list your tech stack again?"})

        elif current_stage == "assessment_start":
            tech_stack_input = st.session_state.candidate_info["tech_stack"]
            tech_stack = [tech for tech in re.split(r'[, ]+', tech_stack_input) if tech]
            random.shuffle(tech_stack)
            st.session_state.question_plan = tech_stack
            st.session_state.current_topic_index = 0
            st.session_state.questions_asked_on_topic = 0
            
            first_topic = st.session_state.question_plan[0]
            first_question_prompt = f"""
You are an expert technical interviewer. Your task is to ask the very first technical question of the interview.
The topic is: **{first_topic}**. The candidate has {st.session_state.candidate_info.get('experience_years', 'N/A')} years of experience and is applying for the **{st.session_state.candidate_info.get('desired_position', 'N/A')}** role.
Formulate an appropriate question.
Your response MUST be a JSON object with one key: "question". The value for "question" MUST be a single string.
**JSON Response:**
"""
            llm_json_response_str = asyncio.run(get_llm_response(first_question_prompt))
            if llm_json_response_str:
                try:
                    data = json.loads(llm_json_response_str)
                    question = data.get("question")
                    
                    if isinstance(question, dict):
                        question = question.get('description', next(iter(question.values()), str(question)))
                    
                    question_str = str(question)
                    
                    st.session_state.last_question_asked = question_str
                    st.session_state.question_history.append(question_str)
                    st.session_state.messages.append({"role": "assistant", "content": question_str})
                    st.session_state.conversation_stage = "in_assessment"
                except json.JSONDecodeError:
                    st.session_state.messages.append({"role": "assistant", "content": "I'm having a moment of writer's block. Let's try that again. Are you ready?"})

        elif current_stage == "in_assessment":
            current_topic = st.session_state.question_plan[st.session_state.current_topic_index]
            prompt = get_assessment_response_prompt(
                candidate_info=st.session_state.candidate_info, 
                topic=current_topic,
                questions_asked_on_this_topic=st.session_state.questions_asked_on_topic,
                last_question=st.session_state.last_question_asked, 
                user_answer=user_input,
                question_history=st.session_state.question_history
            )
            llm_json_response_str = asyncio.run(get_llm_response(prompt))
            
            if llm_json_response_str:
                try:
                    data = json.loads(llm_json_response_str)
                    action = data.get("action_needed")
                    full_response = data.get("full_response")
                    new_question = data.get("new_question_asked")

                    st.session_state.messages.append({"role": "assistant", "content": full_response})
                    st.session_state.last_question_asked = new_question
                    
                    if action == "move_on":
                        st.session_state.question_history.append(new_question)
                        st.session_state.questions_asked_on_topic += 1
                        if st.session_state.questions_asked_on_topic >= 2:
                            st.session_state.current_topic_index += 1
                            st.session_state.questions_asked_on_topic = 0
                    
                    if st.session_state.current_topic_index >= len(st.session_state.question_plan):
                        st.session_state.conversation_stage = "coding_challenge"
                        coding_prompt = get_coding_question_prompt(st.session_state.candidate_info, st.session_state.coding_questions_asked)
                        coding_response_str = asyncio.run(get_llm_response(coding_prompt))
                        if coding_response_str:
                            coding_data = json.loads(coding_response_str)
                            coding_question = coding_data.get("question")
                            st.session_state.messages.append({"role": "assistant", "content": "Great, thank you. To wrap up, I have a couple of brief logic questions for you."})
                            st.session_state.messages.append({"role": "assistant", "content": coding_question})
                            st.session_state.last_question_asked = coding_question
                
                except json.JSONDecodeError:
                    st.session_state.messages.append({"role": "assistant", "content": "My apologies, I lost my train of thought. Let's move on."})
                    st.session_state.current_topic_index += 1

        elif current_stage == "coding_challenge":
            st.session_state.messages.append({"role": "assistant", "content": "Okay, thank you for that."})
            st.session_state.coding_questions_asked += 1

            if st.session_state.coding_questions_asked >= 2:
                st.session_state.conversation_stage = "conclusion"
            else:
                prompt = get_coding_question_prompt(st.session_state.candidate_info, st.session_state.coding_questions_asked)
                llm_json_response_str = asyncio.run(get_llm_response(prompt))
                if llm_json_response_str:
                    try:
                        data = json.loads(llm_json_response_str)
                        question = data.get("question")
                        st.session_state.messages.append({"role": "assistant", "content": f"For the final question: {question}"})
                        st.session_state.last_question_asked = question
                    except json.JSONDecodeError:
                        st.session_state.conversation_stage = "conclusion"

        if st.session_state.conversation_stage == "conclusion":
            prompt = get_conclusion_prompt(st.session_state.candidate_info)
            llm_json_response_str = asyncio.run(get_llm_response(prompt))
            if llm_json_response_str:
                try:
                    data = json.loads(llm_json_response_str)
                    st.session_state.messages.append({"role": "assistant", "content": data.get("response")})
                    st.session_state.conversation_stage = "finished"
                except json.JSONDecodeError:
                     st.session_state.messages.append({"role": "assistant", "content": "Thank you for your time. The recruiting team will be in touch."})
        
        st.session_state.recorder_count += 1
        st.rerun()