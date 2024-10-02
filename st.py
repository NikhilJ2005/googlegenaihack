import os
import google.generativeai as genai
import streamlit as st
from dotenv import load_dotenv
from streamlit_mic_recorder import speech_to_text
import streamlit.components.v1 as components
import pytube as pt
from streamlit_player import st_player as stp
import PIL.Image as pi

load_dotenv()
# Configure the Google Gemini API
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# Set up the model configuration
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

# Create the GenerativeModel with instructions for the Socratic method
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
    system_instruction=(
        "Be a teaching assistant to teach a student using the Socratic teaching method. "
        "The topic is Learning of Data Structures and Algorithms, with a focus on Sorting algorithms. "
        "Ask probing questions and lead the student to answers without revealing them directly. "
        "Stay on Topic, even if the user tries to ask something else."
    ),
)

# Initialize Streamlit app
st.set_page_config(page_title="AI Teaching Assistant", layout="wide")
st.title("AI Teaching Assistant for Data Structures and Algorithms")
state = st.session_state

# Initialize state variables
if 'chat_history' not in state:
    state.chat_history = {}  # Saved chats
if 'current_chat' not in state:
    state.current_chat = []  # Current chat session
if 'current_topic' not in state:
    state.current_topic = None  # Topic of the current chat
if 'chat_session' not in state:
    state.chat_session = None  # Model chat session
if 'page' not in state:
    state.page = 'chat'  # Current page

# Sidebar to manage chat history
with st.sidebar:
    st.header("Chat History")

    # Button to save the current chat
    if state.current_chat and state.current_topic:
        if st.button("Save Chat"):
            state.chat_history[state.current_topic] = state.current_chat.copy()
            st.success(f"Chat '{state.current_topic}' saved.")
    else:
        st.write("Start a chat to enable saving.")

    # Button to delete entire chat history
    if st.button("Delete All Chats"):
        state.chat_history.clear()
        st.success("All chat history deleted.")

    # Display existing chat history
    if state.chat_history:
        st.write("Saved Chats:")
        chat_titles = list(state.chat_history.keys())
        selected_chat = st.selectbox("Select a chat to view", chat_titles)

        if st.button("Load Selected Chat"):
            # Load the selected chat into current chat
            state.current_topic = selected_chat
            state.current_chat = state.chat_history[selected_chat].copy()
            # Reconstruct the chat session with the loaded history
            history = [
                {"role": msg["role"], "parts": [msg["text"]]} for msg in state.current_chat
            ]
            state.chat_session = model.start_chat(history=history)
            st.success(f"Chat '{selected_chat}' loaded.")

        # Button to delete the selected chat
        if st.button("Delete Selected Chat"):
            del state.chat_history[selected_chat]
            st.success(f"Chat '{selected_chat}' deleted.")
    else:
        st.write("No saved chats.")

    # Button to navigate to the visualization page
    if st.button("Go to Learning and Visualization (Non Socratic)"):
        state.page = 'learn'

# Main Chat Interface
if state.page == 'chat':
    if not state.current_chat:
        # Input to start a new chat
        st.subheader("Start a New Chat")
        new_topic = st.text_input("Enter chat topic (e.g., Sorting Algorithms)")
        if st.button("Start Chat"):
            if new_topic:
                state.current_topic = new_topic
                state.current_chat = []
                # Start a new chat session with the assistant's opening message
                opening_message = "Hey! I'm your assistant. What would you like to learn about sorting algorithms today?"
                state.chat_session = model.start_chat(history=[
                    {
                        "role": "model",
                        "parts": [opening_message]
                    }
                ])
                # Display the assistant's opening message using st.chat_message
                with st.chat_message("assistant"):
                    st.markdown(opening_message)
                # Add to current chat
                state.current_chat.append({"role": "model", "text": opening_message})
            else:
                st.warning("Please enter a topic to start a new chat.")
    else:
        st.write(f"**Chat Topic:** {state.current_topic}")
        # Display chat history using st.chat_message
        for message in state.current_chat:
            role = "assistant" if message["role"] == "model" else "user"
            with st.chat_message(role):
                st.markdown(message["text"])

        # Provide options for input method
        input_method = st.radio("Select input method:", ("Type", "Voice"))

        user_input = None  # Initialize user_input

        if input_method == "Type":
            # Chat input using st.chat_input
            user_input = st.chat_input("Your message")
        elif input_method == "Voice":
            # Speech to text input
            text = speech_to_text(
                language='en',
                start_prompt="Start recording",
                stop_prompt="Stop recording",
                just_once=True,
                use_container_width=True,
                callback=None,
                args=(),
                kwargs={},
                key='voice_input'
            )
            if text:
                user_input = text
                # Display the user's message using st.chat_message
                with st.chat_message("user"):
                    st.markdown(user_input)

        if user_input:
            # If input_method is 'Voice' and we have user_input, we need to send it to the model
            if input_method == "Voice":
                # Send user input to the model
                response = state.chat_session.send_message(user_input)
                # Display the assistant's response using st.chat_message
                with st.chat_message("assistant"):
                    st.markdown(response.text)
                # Add messages to current chat
                state.current_chat.append({"role": "user", "text": user_input})
                state.current_chat.append({"role": "model", "text": response.text})
            elif input_method == "Type" and user_input:
                # Send user input to the model
                response = state.chat_session.send_message(user_input)
                # Display the user's message using st.chat_message
                with st.chat_message("user"):
                    st.markdown(user_input)
                # Display the assistant's response using st.chat_message
                with st.chat_message("assistant"):
                    st.markdown(response.text)
                # Add messages to current chat
                state.current_chat.append({"role": "user", "text": user_input})
                state.current_chat.append({"role": "model", "text": response.text})

        # Option to end the current chat
        if st.button("End Chat"):
            state.current_chat = []
            state.current_topic = None
            state.chat_session = None
            st.info("Chat ended. You can start a new chat.")

# Page for Plots and Graphs (Data Structure Visualizations)
elif state.page == 'learn':
    st.header("Learning Resources With Summarization")

    # Dropdown for selecting the data structure to visualize
    data_structure = st.selectbox("Select a topic", ["Bubble Sort", "Merge Sort", "Quick Sort", "Heap Sort"])

    modelvid = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config=generation_config,
        system_instruction="Explain visualization thoroughly",
    )

    # Button to generate the plot
    if st.button(label="Get Video and Explain", key="get_video"):
        with st.spinner("Obtaining..."):
            if data_structure == "Bubble Sort":
                link = "https://www.youtube.com/watch?v=xli_FI7CuzA"
                st.write(f"[Bubble Sort Video]({link})")
                stp(link)
                image = pi.open("bs.jpg")
                st.image(image)
                response = modelvid.generate_content(["Explain bubble sort visualizations with image"])
                st.write(f"**Assistant:** {response.text}")

            elif data_structure == "Merge Sort":
                link = "https://www.youtube.com/watch?v=4VqmGXwpLqc"
                st.write(f"[Merge Sort Video]({link})")
                stp(link)
                image = pi.open("ms.png")
                st.image(image)
                response = modelvid.generate_content(["Explain merge sort visualizations with images"])
                st.write(f"**Assistant:** {response.text}")

            elif data_structure == "Quick Sort":
                link = "https://www.youtube.com/watch?v=Hoixgm4-P4M"
                st.write(f"[Quick Sort Video]({link})")
                stp(link)
                image = pi.open("qs.png")
                st.image(image)
                response = modelvid.generate_content(["Explain quick sort visualizations with images"])
                st.write(f"**Assistant:** {response.text}")

            elif data_structure == "Heap Sort":
                link = "https://www.youtube.com/watch?v=2DmK_H7IdTo"
                st.write(f"[Heap Sort Video]({link})")
                stp(link)
                image = pi.open("hs.png")
                st.image(image)
                response = modelvid.generate_content(["Explain heap sort visualizations with images"])
                st.write(f"**Assistant:** {response.text}")

    # Button to return to chat
    if st.button("Back to Chat"):
        state.page = 'chat'
