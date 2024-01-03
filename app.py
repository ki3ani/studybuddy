from flask import Flask, render_template, request, send_file
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
import replicate
import os
from dotenv import load_dotenv
from flask_weasyprint import HTML, render_pdf

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
            html = render_template('paper_template.html', content=generated_content)
            save_path = f"user_{current_user.id}_paper_{len(current_user.papers)}.pdf"
            HTML(string=html).write_pdf(save_path)

        return send_file(save_path, as_attachment=True)

    return render_template('write_paper.html')

if __name__ == '__main__':
    app.run(debug=True)


    