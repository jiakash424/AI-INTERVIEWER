import streamlit as st
from streamlit_feedback import streamlit_feedback
import trubrics
from openai import OpenAI

# Sidebar to input OpenAI API key
with st.sidebar:
    openai_api_key = st.text_input("OpenAI API Key", type="password")

st.title("🤖Feedback")

st.write("""
This app generates interview questions based on the role you enter.
You can also leave feedback on the quality of the AI's responses!
""")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hi! Please enter a job role and I'll ask you an interview question."}
    ]
if "response" not in st.session_state:
    st.session_state["response"] = None

messages = st.session_state.messages

# Display previous messages
for msg in messages:
    st.chat_message(msg["role"]).write(msg["content"])

# Input: Role for interview question
if prompt := st.chat_input(placeholder="Enter a job role, e.g., Backend Developer, Data Scientist"):
    messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    if not openai_api_key:
        st.info("Please add your OpenAI API key to continue.")
        st.stop()

    # Instantiate OpenAI client
    client = OpenAI(api_key=openai_api_key)

    # Create dynamic prompt for interviewer
    system_prompt = {
        "role": "system",
        "content": (
            "You are a professional technical interviewer. Based on the job role provided by the user, "
            "generate a challenging, role-specific interview question. Keep the question concise."
        )
    }
    convo = [system_prompt] + messages

    # API call to generate question
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=convo
    )

    # Extract and save AI response
    ai_response = response.choices[0].message.content
    st.session_state["response"] = ai_response

    with st.chat_message("assistant"):
        messages.append({"role": "assistant", "content": ai_response})
        st.write(ai_response)

# Feedback collection
if st.session_state["response"]:
    feedback = streamlit_feedback(
        feedback_type="thumbs",
        optional_text_label="[Optional] Why did you like/dislike this question?",
        key=f"feedback_{len(messages)}",
    )

    if feedback and "TRUBRICS_EMAIL" in st.secrets:
        config = trubrics.init(
            email=st.secrets.TRUBRICS_EMAIL,
            password=st.secrets.TRUBRICS_PASSWORD,
        )
        collection = trubrics.collect(
            component_name="AI Interviewer",
            model="gpt-3.5-turbo",
            response=feedback,
            metadata={"chat": messages},
        )
        trubrics.save(config, collection)
        st.toast("📝 Feedback recorded!")
