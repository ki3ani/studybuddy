from flask import Flask, render_template, request, send_file
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
import replicate
import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# Set up Replicate API client
replicate.api_key = os.environ.get("REPLICATE_API_TOKEN")

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Your User class and login manager setup
class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

# Login route
@app.route('/login')
def login():
    user = User(1)  # For simplicity, assume a single user
    login_user(user)
    return "Logged in successfully."

# Logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return "Logged out successfully."

# Main route to select a topic
@app.route('/')
@login_required
def select_topic():
    return render_template('select_topic.html')

# Route to write a paper
@app.route('/write-paper', methods=['POST'])
@login_required
def write_paper():
    topic = request.form.get('topic')
    return render_template('write_paper.html', topic=topic)

# Route to generate content using Replicate API
@app.route('/generate-content', methods=['POST'])
@login_required
def generate_content():
    topic = request.form.get('topic')
    content = request.form.get('content')
    commands = request.form.get('commands')
    styling = request.form.get('styling')

    if not topic or not content:
        return "Invalid input. Topic and content are required."

    # Process user commands
    user_commands = commands.lower().split('#')
    user_commands = [cmd.strip() for cmd in user_commands if cmd.strip()]

    # Define Replicate API input prompt
    input_prompt = f"Write an essay on the topic: {topic}. {content}"

    # Process user commands and modify input prompt accordingly
    for cmd in user_commands:
        if cmd.startswith('explain'):
            input_prompt += " #explain"
        elif cmd.startswith('title'):
            input_prompt += " #title"
        elif cmd.startswith('summary'):
            input_prompt += " #summary"
        elif cmd.startswith('quote'):
            input_prompt += " #quote"
        elif cmd.startswith('questions'):
            input_prompt += " #questions"
        elif cmd.startswith('examples'):
            input_prompt += " #examples"
        elif cmd.startswith('compare'):
            input_prompt += " #compare"
        elif cmd.startswith('visualize'):
            input_prompt += " #visualize"
        elif cmd.startswith('related-topics'):
            input_prompt += " #related-topics"
        elif cmd.startswith('sources'):
            input_prompt += " #sources"

    # Use Replicate API for content generation
    response = replicate.stream(
        "meta/llama-2-70b-chat",
        input={"prompt": input_prompt}
    )

    generated_content = ''.join([str(event) for event in response])

    return render_template('write_paper.html', topic=topic, generated_content=generated_content)

# Route to export content to Markdown
@app.route('/export-to-markdown', methods=['POST'])
@login_required
def export_to_markdown():
    content = request.form.get('content')
    with open('exported_content.md', 'w') as file:
        file.write(content)
    return send_file('exported_content.md', as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
