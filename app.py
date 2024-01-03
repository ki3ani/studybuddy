from flask import Flask, render_template, request, send_file
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
import replicate
import os
from dotenv import load_dotenv
from flask_weasyprint import HTML, render_pdf
from flask import render_template_string

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
        self.papers = []

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

# ...

@app.route('/write-paper', methods=['GET', 'POST'])
@login_required
def write_paper():
    if request.method == 'POST':
        content = request.form.get('content')
        save_option = request.form.get('save_option')

        if not content:
            return "Invalid input. Content is required."

        # Process user commands
        user_commands = content.lower().split('#')
        user_commands = [cmd.strip() for cmd in user_commands if cmd.strip()]

        # Define Replicate API input prompt
        input_prompt = content

        # Process user commands and modify input prompt accordingly
        for cmd in user_commands:
            input_prompt += f" #{cmd}"

        # Use Replicate API for content generation
        response = replicate.stream(
            "meta/llama-2-70b-chat",
            input={"prompt": input_prompt}
        )

        generated_content = ''.join([str(event) for event in response])

        # Save the generated content to the user's paper
        current_user.papers.append(generated_content)

        # Save the paper based on user's preference (Markdown or PDF)
        if save_option == 'markdown':
            save_path = f"user_{current_user.id}_paper_{len(current_user.papers)}.md"
            with open(save_path, 'w') as file:
                file.write(generated_content)
        elif save_option == 'pdf':
            html = render_template_string('<div>{{ content }}</div>', content=generated_content)
            save_path = f"user_{current_user.id}_paper_{len(current_user.papers)}.pdf"
            HTML(string=html).write_pdf(save_path)

        # Display preview to the user
        return render_template('preview.html', content=generated_content, save_option=save_option)

    return render_template('write_paper.html')

# Add a new route to handle saving and continuing
@app.route('/save-and-continue', methods=['POST'])
@login_required
def save_and_continue():
    # Save the generated content to the user's paper
    content = request.form.get('content')
    current_user.papers.append(content)

    # Clear the input area for the user to continue writing
    return render_template('write_paper.html')
if __name__ == '__main__':
    app.run(debug=False)
