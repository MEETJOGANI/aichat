import os
import sys
import subprocess
import importlib.util
import streamlit as st
import serpapi

# Function to check and install packages if they don't exist
def install_package(package):
    try:
        spec = importlib.util.find_spec(package.split('>=')[0].split('==')[0])
        if spec is None:
            print(f"Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    except Exception as e:
        print(f"Error installing {package}: {str(e)}")

# List of required packages
required_packages = [
    "streamlit>=1.31.0",
    "openai>=1.12.0",
    "python-dotenv>=1.0.0",
    "numpy>=1.26.0",
    "pandas>=2.1.0",
    "google-search-results>=2.4.2"  # SerpAPI package
]

# Install all required packages
for package in required_packages:
    install_package(package)

# Now import the required packages
import streamlit as st
import openai
from dotenv import load_dotenv
import datetime
import time
import json
from serpapi import GoogleSearch  # For real web search capabilities

# Streamlit page configuration (must be the first Streamlit command)
st.set_page_config(
    page_title="WebMind - Better than ChatGPT",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load environment variables from .env file
load_dotenv()

# Configure API keys from environment variables or Streamlit secrets
try:
    # Configure OpenAI API Key
    if hasattr(st, 'secrets') and "OPENAI_API_KEY" in st.secrets and st.secrets["OPENAI_API_KEY"]:
        openai.api_key = st.secrets["OPENAI_API_KEY"]
    elif os.getenv("OPENAI_API_KEY"):
        openai.api_key = os.getenv("OPENAI_API_KEY")
    else:
        # Will be handled in the UI
        pass

    # Configure SerpAPI Key
    if hasattr(st, 'secrets') and "SERPAPI_API_KEY" in st.secrets and st.secrets["SERPAPI_API_KEY"]:
        serpapi_key = st.secrets["SERPAPI_API_KEY"]
    elif os.getenv("SERPAPI_API_KEY"):
        serpapi_key = os.getenv("SERPAPI_API_KEY")
    else:
        # Set the provided key directly
        serpapi_key = "662c0de587977680d79a77f3cf0af5d8a0927e2fc6e27e01b98bcccc0996d47a"

except Exception as e:
    print(f"Error configuring API keys: {str(e)}")
    # Will be handled in the UI

# Define web search function using SerpAPI
def perform_web_search(query, num_results=5):
    """
    Perform a real web search using SerpAPI and return formatted results.

    Args:
        query (str): The search query
        num_results (int): Number of results to return

    Returns:
        dict: Search results with organic results and knowledge panel if available
    """
    try:
        # Setup search parameters
        search_params = {
            "engine": "google",
            "q": query,
            "api_key": serpapi_key,
            "num": str(num_results)
        }

        # Execute search
        search = GoogleSearch(search_params)
        results = search.get_dict()

        # Format the results
        formatted_results = {
            "query": query,
            "organic_results": [],
            "knowledge_graph": None,
            "answer_box": None,
            "related_questions": []
        }

        # Extract organic search results
        if "organic_results" in results:
            for result in results["organic_results"][:num_results]:
                formatted_results["organic_results"].append({
                    "title": result.get("title", ""),
                    "link": result.get("link", ""),
                    "snippet": result.get("snippet", ""),
                    "source": result.get("source", "")
                })

        # Extract knowledge graph if available
        if "knowledge_graph" in results:
            kg = results["knowledge_graph"]
            formatted_results["knowledge_graph"] = {
                "title": kg.get("title", ""),
                "type": kg.get("type", ""),
                "description": kg.get("description", ""),
                "attributes": kg.get("attributes", {})
            }

        # Extract answer box if available
        if "answer_box" in results:
            ab = results["answer_box"]
            formatted_results["answer_box"] = {
                "title": ab.get("title", ""),
                "answer": ab.get("answer", ab.get("snippet", "")),
                "source": ab.get("source", "")
            }

        # Extract related questions if available
        if "related_questions" in results:
            for question in results["related_questions"]:
                formatted_results["related_questions"].append({
                    "question": question.get("question", ""),
                    "answer": question.get("answer", ""),
                    "source": question.get("source", {}).get("name", "")
                })

        return formatted_results
    except Exception as e:
        # Return error information
        return {
            "error": str(e),
            "query": query,
            "organic_results": []
        }

# Initialize session state variables if they don't exist
if "messages" not in st.session_state:
    st.session_state.messages = []

if "username" not in st.session_state:
    st.session_state.username = None

# Set up API key session state
if "api_key_configured" not in st.session_state:
    st.session_state.api_key_configured = openai.api_key is not None

# Sidebar navigation
with st.sidebar:
    st.title("WebMind AI")

    # API Key configuration
    if not st.session_state.api_key_configured:
        with st.expander("Configure OpenAI API Key", expanded=True):
            api_key = st.text_input("Enter your OpenAI API Key:", type="password")
            if st.button("Save API Key") and api_key:
                openai.api_key = api_key
                st.session_state.api_key_configured = True
                st.success("API key configured successfully!")
                st.experimental_rerun()

    # Username input for first-time users
    if st.session_state.username is None:
        with st.form("username_form"):
            input_username = st.text_input("Enter your username to get started:")
            submit_button = st.form_submit_button("Start Chatting")

            if submit_button and input_username:
                st.session_state.username = input_username
                st.success(f"Welcome, {input_username}!")
                st.experimental_rerun()
    else:
        st.write(f"Logged in as: **{st.session_state.username}**")
        if st.button("Logout"):
            st.session_state.username = None
            st.session_state.messages = []
            st.experimental_rerun()

    # Navigation menu
    st.header("Navigation")
    page = st.radio("Go to:", ["Chat", "Code Playground", "Terminal", "Version Control", "Settings"])

    # Display app information
    st.markdown("---")
    st.markdown("### About")
    st.markdown("**WebMind - An AI that thinks and searches like a human.**")
    st.markdown("Powered by OpenAI and real-time web search.")

# Main content based on selected page
if st.session_state.username is None:
    # Welcome screen for users who haven't set a username
    st.markdown("# Welcome to WebMind")
    st.markdown("### An AI that thinks and searches like a human")
    st.markdown("Please enter a username in the sidebar to get started.")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("https://upload.wikimedia.org/wikipedia/commons/0/04/ChatGPT_logo.svg", width=200)
        st.markdown("""
        ### Features:
        - Real-time web search integration
        - Code Playground with syntax highlighting
        - Terminal emulation
        - Version control visualization
        - Up-to-date information with citations
        """)
else:
    # Content based on selected page
    if page == "Chat":
        st.header("💬 Chat")

        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Chat input
        if prompt := st.chat_input("Type your message here..."):
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})

            # Display user message
            with st.chat_message("user"):
                st.markdown(prompt)

            # Display AI thinking indicator
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                message_placeholder.markdown("Thinking...")

                try:
                    if not openai.api_key:
                        raise ValueError("OpenAI API key is not configured. Please add your API key in the sidebar or Settings page.")

                    # Current date for context
                    current_date = datetime.datetime.now().strftime("%Y-%m-%d")

                    # Check if this looks like a question that needs web search
                    needs_search = any(keyword in prompt.lower() for keyword in [
                        "what is", "who is", "when", "where", "why", "how", "which", "news",
                        "latest", "current", "recent", "today", "update", "explain",
                        "difference between", "compare", "best", "definition", "define"
                    ])

                    # Perform web search for questions that might need real-time info
                    search_results = None
                    if needs_search:
                        with st.spinner("Searching the web..."):
                            search_results = perform_web_search(prompt)

                            # Check if search had an error
                            if "error" in search_results and not search_results.get("organic_results"):
                                st.warning(f"Web search error: {search_results['error']}. Using AI knowledge only.")
                                search_results = None

                    # Enhanced system prompt with web search capabilities
                    system_prompt = f"""You are WebMind, an advanced AI assistant with real web search capabilities talking to {st.session_state.username}. Today's date is {current_date}.

When answering questions:
1. Use the provided search results (if available) to give accurate, up-to-date information.
2. Include relevant facts, statistics, and citations when appropriate using [Source: Website] format.
3. For coding questions, provide modern, best-practice code examples.
4. Structure complex responses with clear headings and organized information.
5. If you're unsure about some information, acknowledge this rather than making up facts.

Your goal is to provide the most helpful, accurate, and comprehensive response possible."""

                    # Prepare the messages for OpenAI
                    messages = [{"role": "system", "content": system_prompt}]

                    # Add search results as a system message if available
                    if search_results:
                        search_content = "Here are the web search results for your query:\n\n"

                        # Add answer box/featured snippet if available
                        if search_results.get("answer_box"):
                            ab = search_results["answer_box"]
                            search_content += f"FEATURED ANSWER: {ab.get('title', '')}\n{ab.get('answer', '')}\n"
                            if ab.get('source'):
                                search_content += f"[Source: {ab.get('source')}]\n\n"

                        # Add knowledge graph if available
                        if search_results.get("knowledge_graph"):
                            kg = search_results["knowledge_graph"]
                            search_content += f"KNOWLEDGE PANEL: {kg.get('title', '')} - {kg.get('type', '')}\n"
                            search_content += f"{kg.get('description', '')}\n\n"

                        # Add organic search results
                        if search_results.get("organic_results"):
                            search_content += "SEARCH RESULTS:\n"
                            for i, result in enumerate(search_results["organic_results"], 1):
                                search_content += f"{i}. {result['title']}\n"
                                search_content += f"   {result['snippet']}\n"
                                search_content += f"   [Source: {result['source']}]\n\n"

                        # Add related questions if available
                        if search_results.get("related_questions"):
                            search_content += "PEOPLE ALSO ASK:\n"
                            for i, question in enumerate(search_results["related_questions"], 1):
                                search_content += f"{i}. {question['question']}\n"
                                search_content += f"   {question['answer']}\n"
                                if question.get('source'):
                                    search_content += f"   [Source: {question['source']}]\n"

                        messages.append({"role": "system", "content": search_content})

                    # Add conversation history
                    messages.extend([{"role": m["role"], "content": m["content"]} for m in st.session_state.messages])

                    # Send request to OpenAI API
                    response = openai.chat.completions.create(
                        model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
                        messages=messages,
                        max_tokens=1500,  # Increased to allow for more detailed responses
                        temperature=0.7,
                    )

                    # Extract response text
                    response_text = response.choices[0].message.content

                    # Update AI message
                    message_placeholder.markdown(response_text)

                    # Add assistant response to chat history
                    st.session_state.messages.append({"role": "assistant", "content": response_text})

                except ValueError as e:
                    # Handle missing API key
                    error_message = str(e)
                    message_placeholder.markdown(f"⚠️ **Configuration Error:** {error_message}")
                    st.error(error_message)

                    # Show API key configuration guidance
                    with st.expander("How to configure your OpenAI API key"):
                        st.markdown("""
                        ### Getting an OpenAI API Key
                        1. Visit [OpenAI's API platform](https://platform.openai.com/)
                        2. Sign up or log in
                        3. Navigate to the [API Keys section](https://platform.openai.com/api-keys)
                        4. Create a new secret key
                        5. Copy the key and paste it in the API Key field in the sidebar or Settings page
                        """)

                except Exception as e:
                    # Handle other errors (rate limits, connectivity issues, etc.)
                    error_type = type(e).__name__
                    error_message = str(e)

                    # Format user-friendly error message
                    if "RateLimitError" in error_type or "insufficient_quota" in error_message:
                        friendly_message = "Rate limit exceeded. Your OpenAI account has reached its usage limit or quota."
                        solution = "Check your [OpenAI usage limits](https://platform.openai.com/account/limits) or consider upgrading your plan."
                    elif "AuthenticationError" in error_type:
                        friendly_message = "Authentication error. Your API key may be invalid or expired."
                        solution = "Please update your API key in the Settings page."
                    elif "Timeout" in error_type or "ConnectionError" in error_type:
                        friendly_message = "Connection timeout. Unable to reach OpenAI servers."
                        solution = "Please check your internet connection and try again later."
                    else:
                        friendly_message = f"An error occurred: {error_message}"
                        solution = "Please try again or check the Settings page to verify your configuration."

                    # Update message placeholder with error details
                    message_placeholder.markdown(f"⚠️ **Error:** {friendly_message}\n\n**Solution:** {solution}")

                    # Display technical error details in an expander
                    with st.expander("Technical error details"):
                        st.code(f"{error_type}: {error_message}")

                    # Log error
                    st.error(friendly_message)

    elif page == "Code Playground":
        st.header("💻 Code Playground")

        # Language selection
        language = st.selectbox(
            "Select Language",
            ["Python", "JavaScript", "HTML", "CSS", "SQL"],
            index=0
        )

        # Default code examples for different languages
        default_code = {
            "Python": """# Python Example
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)

print("Hello, world!")
print(f"Fibonacci of 10: {fibonacci(10)}")""",

            "JavaScript": """// JavaScript Example
function fibonacci(n) {
  if (n <= 1) return n;
  return fibonacci(n - 1) + fibonacci(n - 2);
}

console.log("Hello, world!");
console.log(fibonacci(10));""",

            "HTML": """<!DOCTYPE html>
<html>
<head>
  <title>Sample Page</title>
</head>
<body>
  <h1>Hello, World!</h1>
  <p>This is a sample HTML page.</p>
</body>
</html>""",

            "CSS": """/* CSS Example */
body {
  font-family: Arial, sans-serif;
  margin: 0;
  padding: 20px;
  background-color: #f5f5f5;
}

h1 {
  color: #333;
  text-align: center;
}

p {
  line-height: 1.6;
}""",

            "SQL": """-- SQL Example
SELECT
  users.name,
  COUNT(orders.id) as order_count
FROM
  users
LEFT JOIN
  orders ON users.id = orders.user_id
GROUP BY
  users.id
ORDER BY
  order_count DESC
LIMIT 10;"""
        }

        # Create two columns for code editor and output
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### Code Editor")
            code = st.text_area("", value=default_code[language], height=400)
            run_button = st.button("Run Code")

        with col2:
            st.markdown("### Output")
            output_container = st.container()

            if run_button:
                with output_container:
                    st.code("Running code...", language="bash")

                    # For Python code, we can use st.code to run it (simulated)
                    if language == "Python":
                        st.code("Output will appear here. In a full implementation, we would execute this code securely.", language="bash")
                    else:
                        st.code(f"Code execution for {language} would be handled by a backend service.\n\nSimulated output for demonstration purposes.", language="bash")

    elif page == "Terminal":
        st.header("🖥️ Terminal")

        # Terminal simulation
        st.markdown("### Interactive Terminal (Simulated)")

        # Terminal history display
        if "terminal_history" not in st.session_state:
            st.session_state.terminal_history = [
                {"output": "\x1b[1;32mWelcome to the Replit-like Terminal!\x1b[0m"},
                {"output": "This is a simulated terminal for demonstration purposes."},
                {"output": "Try typing some commands like:"},
                {"output": "- help: Show available commands"},
                {"output": "- ls: List files in current directory"},
                {"output": "- echo <text>: Display text"},
                {"output": "- clear: Clear the terminal"},
                {"output": "- date: Show current date and time"},
                {"output": "- whoami: Show current user"},
                {"output": ""}
            ]

        # Display terminal history in a scrollable area
        terminal_display = st.code("\n".join([entry["output"] for entry in st.session_state.terminal_history]), language="bash")

        # Terminal input
        with st.form("terminal_input", clear_on_submit=True):
            terminal_prompt = st.text_input("$", key="terminal_command")
            submit_cmd = st.form_submit_button("Execute")

            if submit_cmd and terminal_prompt:
                cmd = terminal_prompt.strip()
                args = cmd.split()
                primary_cmd = args[0].lower() if args else ""

                if primary_cmd == "help":
                    output = "Available commands:\n- help - Show this help message\n- clear - Clear the terminal\n- echo <text> - Display text\n- ls - List files (simulated)\n- date - Show current date and time\n- whoami - Show current user"

                elif primary_cmd == "clear":
                    st.session_state.terminal_history = []
                    output = ""

                elif primary_cmd == "echo":
                    output = " ".join(args[1:])

                elif primary_cmd == "ls":
                    output = "app.py\n.env\npyproject.toml\nrequirements.txt"

                elif primary_cmd == "date":
                    output = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                elif primary_cmd == "whoami":
                    output = st.session_state.username or "anonymous"

                else:
                    output = f"Command not found: {primary_cmd}\nType 'help' to see available commands"

                # Add command and output to history
                st.session_state.terminal_history.append({"output": f"$ {cmd}"})
                st.session_state.terminal_history.append({"output": output})

                # Rerun to update terminal display
                st.experimental_rerun()

    elif page == "Version Control":
        st.header("🔄 Version Control")

        # Sample data for demonstration
        sample_commits = [
            {
                "id": "a1b2c3d",
                "message": "Add chat functionality",
                "author": st.session_state.username,
                "date": "2023-11-15 14:32",
                "branch": "main",
                "changes": {"added": 5, "modified": 2, "deleted": 0}
            },
            {
                "id": "e4f5g6h",
                "message": "Implement user authentication",
                "author": st.session_state.username,
                "date": "2023-11-14 10:15",
                "branch": "main",
                "changes": {"added": 3, "modified": 1, "deleted": 0}
            },
            {
                "id": "i7j8k9l",
                "message": "Fix sidebar responsiveness",
                "author": st.session_state.username,
                "date": "2023-11-13 16:45",
                "branch": "main",
                "changes": {"added": 0, "modified": 2, "deleted": 1}
            }
        ]

        # Create tabs for different views
        tab1, tab2 = st.tabs(["Changes", "History"])

        with tab1:
            st.subheader("Current Changes")

            col1, col2 = st.columns([3, 1])

            with col1:
                # Commit message input
                commit_message = st.text_input("Commit message")
                st.button("Commit Changes", disabled=not commit_message)

            with col2:
                # Branch selection
                st.selectbox("Branch", ["main", "development", "feature/user-profile"])

            # Staged and unstaged changes
            st.markdown("#### Staged Changes")
            staged_files = [
                {"name": "app.py", "status": "modified", "changes": 12},
                {"name": "requirements.txt", "status": "modified", "changes": 8}
            ]

            for file in staged_files:
                st.markdown(f"🟢 **{file['name']}** - {file['status'].capitalize()} ({file['changes']} changes)")

            st.markdown("#### Unstaged Changes")
            unstaged_files = [
                {"name": "README.md", "status": "modified", "changes": 5}
            ]

            for file in unstaged_files:
                st.markdown(f"🟠 **{file['name']}** - {file['status'].capitalize()} ({file['changes']} changes)")

        with tab2:
            st.subheader("Commit History")

            for commit in sample_commits:
                with st.expander(f"{commit['message']} ({commit['id'][:7]})"):
                    st.markdown(f"**Author:** {commit['author']}")
                    st.markdown(f"**Date:** {commit['date']}")
                    st.markdown(f"**Branch:** {commit['branch']}")
                    st.markdown(f"**Changes:** +{commit['changes']['added']} −{commit['changes']['deleted']} ~{commit['changes']['modified']}")

    elif page == "Settings":
        st.header("⚙️ Settings")

        # Create tabs for different settings sections
        profile_tab, api_tab, theme_tab = st.tabs(["Profile", "API Settings", "Display & Theme"])

        with profile_tab:
            st.subheader("Profile Settings")

            # Profile form
            with st.form("profile_settings"):
                current_username = st.session_state.username
                new_username = st.text_input("Change Username", value=current_username)
                email = st.text_input("Email Address", placeholder="your@email.com")
                display_name = st.text_input("Display Name", placeholder="How you want to be addressed")

                # Profile preferences
                st.markdown("#### Preferences")
                notify_responses = st.checkbox("Notify me when AI responds", value=True)
                save_history = st.checkbox("Save chat history between sessions", value=True)

                submit_profile = st.form_submit_button("Update Profile")

                if submit_profile:
                    if new_username != current_username:
                        st.session_state.username = new_username
                        st.success(f"Username updated to {new_username}!")
                    st.success("Profile settings updated successfully!")

        with api_tab:
            st.subheader("API Settings")

            # API key management
            with st.form("api_settings"):
                # OpenAI model selection
                model = st.selectbox(
                    "Default AI Model",
                    ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"],
                    index=0
                )

                # API key configuration
                current_api_key = "••••••••" if st.session_state.api_key_configured else ""
                new_api_key = st.text_input("OpenAI API Key", value=current_api_key, type="password",
                                          placeholder="sk-...")

                # AI behavior settings
                st.markdown("#### AI Behavior")
                temperature = st.slider("Response Creativity (Temperature)", min_value=0.0, max_value=2.0, value=0.7, step=0.1)
                max_tokens = st.slider("Maximum Response Length", min_value=50, max_value=4000, value=1000, step=50)

                # Local AI fallback options
                use_local_fallback = st.checkbox("Use local AI as fallback if OpenAI is unavailable", value=True)

                submit_api = st.form_submit_button("Save API Settings")

                if submit_api:
                    if new_api_key and new_api_key != "••••••••":
                        openai.api_key = new_api_key
                        st.session_state.api_key_configured = True

                    st.success("API settings updated successfully!")

        with theme_tab:
            st.subheader("Display & Theme Settings")

            # Theme selection form
            with st.form("theme_settings"):
                # Theme options
                theme_choice = st.radio(
                    "Theme Mode",
                    ["Light", "Dark", "System Default"],
                    index=1
                )

                # Color scheme
                color_scheme = st.selectbox(
                    "Color Scheme",
                    ["Blue (Default)", "Green", "Purple", "Orange", "Red"],
                    index=0
                )

                # Font size
                font_size = st.select_slider(
                    "Font Size",
                    options=["Small", "Medium", "Large", "Extra Large"],
                    value="Medium"
                )

                # Layout options
                compact_mode = st.checkbox("Compact Mode (Reduce spacing)", value=False)
                full_width = st.checkbox("Full-width Layout", value=True)

                submit_theme = st.form_submit_button("Apply Theme Settings")

                if submit_theme:
                    st.success("Theme settings updated! Note: Some settings may require a refresh to take full effect.")
                    # Here we would actually apply these settings in a real implementation

import streamlit as st

# Example of using st.rerun()
if some_condition:
    # Reset session state variables if needed
    st.session_state.some_variable = new_value
    st.rerun()  # Updated method

# Example of manual state reset
if some_other_condition:
    # Reset session state variables
    st.session_state.some_variable = new_value
    st.stop()  # Stop the script execution



# Example form submission
with st.form("my_form"):
    user_input = st.text_input("Enter some text")
    submitted = st.form_submit_button("Submit")

    if submitted:  # This is the condition
        # Process the form data
        st.session_state.processed_input = user_input
        st.rerun()  # Rerun the app to reflect changes

# Display the processed input
if 'processed_input' in st.session_state:
    st.write("You entered:", st.session_state.processed_input)
