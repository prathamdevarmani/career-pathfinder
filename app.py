from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import json
from datetime import datetime
from resume_processor import ResumeProcessor  # Import the ResumeProcessor class
from hiring_companies_analyzer import HiringCompaniesAnalyzer  # Import the HiringCompaniesAnalyzer class

# Configure upload folder and allowed extensions
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'docx'}

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Optional imports - will work without them for demo
try:
    import mysql.connector
    from mysql.connector import Error
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False
    print("MySQL not available - using in-memory storage for demo")
# Force-disable MySQL via environment variable for free hosting
if os.environ.get('DISABLE_MYSQL') == '1':
    MYSQL_AVAILABLE = False
    print("MySQL disabled via DISABLE_MYSQL=1 - using in-memory storage")
try:
    import spacy
    nlp = spacy.load("en_core_web_sm")
    NLP_AVAILABLE = True
except (ImportError, OSError):
    NLP_AVAILABLE = False
    nlp = None
    print("spaCy not available - some features may be limited")

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("Scikit-learn not available - using basic matching")

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', os.environ.get('FLASK_SECRET', 'dev-secret-change-me'))  # Change this to a secure secret key in production
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# In-memory storage for demo (replace with database in production)
users_db = {}
user_skills_db = {}
user_counter = 1

# Initialize ResumeProcessor
resume_processor = ResumeProcessor()

# Initialize HiringCompaniesAnalyzer
hiring_companies_analyzer = HiringCompaniesAnalyzer()

# Database configuration (for when MySQL is available)
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',  # Change this to your MySQL password
    'database': 'career_pathfinder'
}

def get_db_connection():
    """Get database connection"""
    if MYSQL_AVAILABLE:
        try:
            connection = mysql.connector.connect(**DB_CONFIG)
            return connection
        except Error as e:
            print(f"Error connecting to MySQL: {e}")
            return None
    return None

def init_database():
    """Initialize database and create tables"""
    if MYSQL_AVAILABLE:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            
            # Create database if not exists
            cursor.execute("CREATE DATABASE IF NOT EXISTS career_pathfinder")
            cursor.execute("USE career_pathfinder")
            
            # Create users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create user_skills table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_skills (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT,
                    skill_name VARCHAR(100) NOT NULL,
                    skill_type ENUM('IT', 'Non-IT') NOT NULL,
                    proficiency_level ENUM('Beginner', 'Intermediate', 'Advanced') DEFAULT 'Beginner',
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
            connection.commit()
            cursor.close()
            connection.close()
            print("Database initialized successfully!")
    else:
        print("Using in-memory storage for demo")

# Sample skills data with categories
IT_SKILLS = {
    "Programming Languages": [
        'Python', 'JavaScript', 'Java', 'C++', 'C#', 'TypeScript',
        'PHP', 'Ruby', 'Go', 'Swift', 'Kotlin', 'Rust', 'Dart', 'R'
    ],
    "Web Development": [
        'HTML5', 'CSS3', 'React', 'Angular', 'Vue.js', 'Node.js',
        'Django', 'Flask', 'Spring Boot', 'Express', 'Laravel', 'ASP.NET',
        'Spring Framework', 'Hibernate', 'GraphQL', 'Webpack', 'SASS'
    ],
    "Databases": [
        'MySQL', 'PostgreSQL', 'MongoDB', 'SQLite', 'Oracle', 'SQL Server',
        'Redis', 'Firebase', 'DynamoDB', 'Elasticsearch', 'SQL'
    ],
    "Cloud & DevOps": [
        'AWS', 'Azure', 'Google Cloud', 'Docker', 'Kubernetes',
        'Terraform', 'Jenkins', 'GitHub Actions', 'CI/CD', 'Ansible'
    ],
    "AI/ML & Data Science": [
        'Machine Learning', 'Deep Learning', 'Neural Networks', 'Computer Vision',
        'NLP', 'TensorFlow', 'PyTorch', 'Pandas', 'NumPy', 'Data Analysis',
        'Data Science', 'MLOps', 'Reinforcement Learning'
    ],
    "Testing & Quality": [
        'Testing', 'Automation Testing', 'Selenium', 'JUnit', 'API Testing',
        'Performance Testing', 'Bug Tracking'
    ],
    "Mobile Development": [
        'Mobile Development', 'Android SDK', 'iOS', 'Android', 'React Native',
        'Flutter', 'Jetpack Compose', 'Room Database', 'MVVM'
    ],
    "Security & Compliance": [
        'Cybersecurity', 'Network Security', 'Penetration Testing', 'SIEM',
        'Compliance', 'Forensics', 'Security'
    ],
    "Enterprise & Architecture": [
        'Enterprise Applications', 'System Design', 'Design Patterns',
        'Architecture', 'Cloud Architecture', 'Scalability', 'Performance',
        'Microservices'
    ],
    "Specialized Technologies": [
        'Unity', 'Unreal Engine', '3D Graphics', 'Animation', 'Physics',
        'Blockchain', 'Solidity', 'Smart Contracts', 'Ethereum', 'Web3',
        'DeFi', 'NFT', 'Cryptocurrency'
    ],
    "Monitoring & Operations": [
        'Monitoring', 'Prometheus', 'Grafana', 'Incident Management',
        'Scripting', 'Automation', 'Cloud Platforms'
    ],
    "Java Ecosystem": [
        'Maven', 'Spring Security', 'Apache Kafka', 'JPA'
    ],
    "Other Technologies": [
        'Git', 'Linux', 'REST API', 'GraphQL', 'IoT', 'Embedded Systems',
        'Mathematics', 'Research', 'Publications'
    ]
}

NON_IT_SKILLS = {
    "Business & Management": [
        'Project Management', 'Product Management', 'Agile', 'Scrum',
        'Business Analysis', 'Strategic Planning', 'Risk Management'
    ],
    "Communication": [
        'Public Speaking', 'Technical Writing', 'Documentation',
        'Presentation Skills', 'Negotiation', 'Team Leadership'
    ],
    "Design & Creativity": [
        'UI/UX Design', 'Graphic Design', 'Figma', 'Adobe XD',
        'Adobe Photoshop', 'User Research', 'Prototyping'
    ],
    "Marketing & Sales": [
        'Digital Marketing', 'Content Marketing', 'SEO', 'Social Media',
        'Email Marketing', 'Copywriting', 'Sales Strategy'
    ],
    "Professional Skills": [
        'Problem Solving', 'Critical Thinking', 'Time Management',
        'Teamwork', 'Adaptability', 'Leadership', 'Mentoring'
    ]
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            flash('Please enter both username and password', 'danger')
            return redirect(url_for('login'))
            
        if MYSQL_AVAILABLE:
            connection = get_db_connection()
            if connection:
                cursor = connection.cursor(dictionary=True)
                cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
                user = cursor.fetchone()
                connection.close()
                
                if user and check_password_hash(user['password_hash'], password):
                    session['user_id'] = user['id']
                    session['username'] = user['username']
                    flash('Login successful!', 'success')
                    return redirect(url_for('home'))
        else:
            # In-memory lookup keyed by username
            user = users_db.get(username)
            if user and check_password_hash(user['password_hash'], password):
                session['user_id'] = user['id']
                session['username'] = username
                flash('Login successful!', 'success')
                return redirect(url_for('home'))
                
        flash('Invalid username or password', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    global user_counter
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if password != confirm_password:
            flash('Passwords do not match!', 'error')
            return render_template('register.html')
        
        password_hash = generate_password_hash(password)
        
        if MYSQL_AVAILABLE:
            connection = get_db_connection()
            if connection:
                cursor = connection.cursor()
                try:
                    cursor.execute(
                        "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
                        (username, email, password_hash)
                    )
                    connection.commit()
                    flash('Registration successful! Please login.', 'success')
                    return redirect(url_for('login'))
                except mysql.connector.IntegrityError:
                    flash('Username or email already exists!', 'error')
                finally:
                    cursor.close()
                    connection.close()
        else:
            # In-memory storage for demo
            if username in users_db:
                flash('Username already exists!', 'error')
            else:
                users_db[username] = {
                    'id': user_counter,
                    'username': username,
                    'email': email,
                    'password_hash': password_hash
                }
                user_counter += 1
                flash('Registration successful! Please login.', 'success')
                return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/home')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('home.html', username=session['username'])

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/features')
def features():
    return render_template('features.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        # Handle contact form submission
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        
        # Here you would typically save this to a database or send an email
        flash('Thank you for your message! We will get back to you soon.', 'success')
        return redirect(url_for('contact'))
        
    return render_template('contact.html')

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    if request.method == 'POST':
        if MYSQL_AVAILABLE:
            # Clear existing skills
            connection = get_db_connection()
            if connection:
                cursor = connection.cursor()
                cursor.execute("DELETE FROM user_skills WHERE user_id = %s", (user_id,))
                
                # Add new skills
                it_skills = request.form.getlist('it_skills')
                non_it_skills = request.form.getlist('non_it_skills')
                
                for skill in it_skills:
                    proficiency = request.form.get(f'proficiency_{skill}', 'Beginner')
                    cursor.execute(
                        "INSERT INTO user_skills (user_id, skill_name, skill_type, proficiency_level) VALUES (%s, %s, %s, %s)",
                        (user_id, skill, 'IT', proficiency)
                    )
                
                for skill in non_it_skills:
                    proficiency = request.form.get(f'proficiency_{skill}', 'Beginner')
                    cursor.execute(
                        "INSERT INTO user_skills (user_id, skill_name, skill_type, proficiency_level) VALUES (%s, %s, %s, %s)",
                        (user_id, skill, 'Non-IT', proficiency)
                    )
                
                connection.commit()
                cursor.close()
                connection.close()
                flash('Profile updated successfully!', 'success')
                return redirect(url_for('profile'))
        else:
            # In-memory storage for demo
            user_skills_db[user_id] = []
            
            # Add new skills
            it_skills = request.form.getlist('it_skills')
            non_it_skills = request.form.getlist('non_it_skills')
            
            for skill in it_skills:
                proficiency = request.form.get(f'proficiency_{skill}', 'Beginner')
                user_skills_db[user_id].append((skill, 'IT', proficiency))
            
            for skill in non_it_skills:
                proficiency = request.form.get(f'proficiency_{skill}', 'Beginner')
                user_skills_db[user_id].append((skill, 'Non-IT', proficiency))
            
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('profile'))
    
    # Get current user skills
    user_skills = []
    if MYSQL_AVAILABLE:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            cursor.execute("SELECT skill_name, skill_type, proficiency_level FROM user_skills WHERE user_id = %s", (user_id,))
            user_skills = cursor.fetchall()
            cursor.close()
            connection.close()
    else:
        # In-memory storage for demo
        user_skills = user_skills_db.get(user_id, [])
    
    return render_template('profile.html', 
                         it_skills=IT_SKILLS, 
                         non_it_skills=NON_IT_SKILLS, 
                         user_skills=user_skills)

@app.route('/job_recommendations')
def job_recommendations():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    # Get user skills
    user_skills = []
    if MYSQL_AVAILABLE:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            cursor.execute("SELECT skill_name FROM user_skills WHERE user_id = %s", (user_id,))
            user_skills = [skill[0] for skill in cursor.fetchall()]
            cursor.close()
            connection.close()
    else:
        # In-memory storage for demo
        user_skill_data = user_skills_db.get(user_id, [])
        user_skills = [skill[0] for skill in user_skill_data]
    
    # Generate job recommendations based on skills
    recommendations = generate_job_recommendations(user_skills)
    
    return render_template('job_recommendations.html', 
                         recommendations=recommendations, 
                         user_skills=user_skills)

@app.route('/skill_gap_analysis')
def skill_gap_analysis():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    # Get user skills
    user_skills = []
    if MYSQL_AVAILABLE:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            cursor.execute("SELECT skill_name, proficiency_level FROM user_skills WHERE user_id = %s", (user_id,))
            user_skills = {skill[0]: skill[1] for skill in cursor.fetchall()}
            cursor.close()
            connection.close()
    else:
        # In-memory storage for demo
        user_skill_data = user_skills_db.get(user_id, [])
        user_skills = {skill[0]: skill[2] for skill in user_skill_data}
    
    # Get target job for analysis (default to first job if none selected)
    target_job = request.args.get('job', 'Python Developer')
    
    # Generate skill gap analysis
    gap_analysis = generate_skill_gap_analysis(user_skills, target_job)
    
    return render_template('skill_gap_analysis.html', 
                         gap_analysis=gap_analysis,
                         target_job=target_job,
                         available_jobs=get_available_job_titles())

def generate_skill_gap_analysis(user_skills, target_job):
    """Generate comprehensive skill gap analysis"""
    # Job requirements database (in real app, this would come from APIs)
    job_requirements = {
        'Python Developer': {
            'required_skills': ['Python', 'Django', 'MySQL', 'Git', 'REST API'],
            'preferred_skills': ['Docker', 'AWS', 'Redis', 'JavaScript'],
            'experience_level': 'Mid-level'
        },
        'Full Stack Developer': {
            'required_skills': ['JavaScript', 'React', 'Node.js', 'MongoDB', 'HTML5', 'CSS3'],
            'preferred_skills': ['TypeScript', 'GraphQL', 'Docker', 'AWS'],
            'experience_level': 'Mid-level'
        },
        'Data Scientist': {
            'required_skills': ['Python', 'Machine Learning', 'Data Analysis', 'Pandas', 'NumPy'],
            'preferred_skills': ['TensorFlow', 'Deep Learning', 'SQL', 'R'],
            'experience_level': 'Senior'
        },
        'DevOps Engineer': {
            'required_skills': ['AWS', 'Docker', 'Kubernetes', 'Linux', 'CI/CD'],
            'preferred_skills': ['Terraform', 'Ansible', 'Jenkins', 'Python'],
            'experience_level': 'Mid-level'
        },
        'Frontend Developer': {
            'required_skills': ['JavaScript', 'React', 'HTML5', 'CSS3'],
            'preferred_skills': ['Vue.js', 'TypeScript', 'Webpack', 'SASS'],
            'experience_level': 'Entry-level'
        },
        'Backend Developer': {
            'required_skills': ['Python', 'Node.js', 'MySQL', 'REST API', 'Git'],
            'preferred_skills': ['Redis', 'MongoDB', 'Docker', 'Microservices'],
            'experience_level': 'Mid-level'
        },
        'Mobile App Developer': {
            'required_skills': ['Swift', 'Kotlin', 'React Native', 'Mobile Development'],
            'preferred_skills': ['Flutter', 'Firebase', 'iOS', 'Android'],
            'experience_level': 'Mid-level'
        },
        'Machine Learning Engineer': {
            'required_skills': ['Python', 'Machine Learning', 'TensorFlow', 'Data Science', 'Deep Learning'],
            'preferred_skills': ['PyTorch', 'MLOps', 'Kubernetes', 'AWS'],
            'experience_level': 'Senior'
        },
        'Cloud Architect': {
            'required_skills': ['AWS', 'Azure', 'Cloud Architecture', 'Kubernetes', 'Terraform'],
            'preferred_skills': ['Google Cloud', 'Microservices', 'Security', 'DevOps'],
            'experience_level': 'Senior'
        },
        'Cybersecurity Analyst': {
            'required_skills': ['Cybersecurity', 'Network Security', 'Risk Assessment', 'Incident Response'],
            'preferred_skills': ['Penetration Testing', 'SIEM', 'Compliance', 'Forensics'],
            'experience_level': 'Mid-level'
        },
        'UI/UX Designer': {
            'required_skills': ['UI/UX Design', 'Figma', 'User Research', 'Prototyping'],
            'preferred_skills': ['Adobe XD', 'Sketch', 'User Testing', 'Design Systems'],
            'experience_level': 'Mid-level'
        },
        'Product Manager': {
            'required_skills': ['Product Management', 'Agile', 'User Research', 'Strategic Planning'],
            'preferred_skills': ['Data Analysis', 'A/B Testing', 'Roadmapping', 'Stakeholder Management'],
            'experience_level': 'Senior'
        },
        'QA Engineer': {
            'required_skills': ['Testing', 'Automation Testing', 'Selenium', 'Bug Tracking'],
            'preferred_skills': ['API Testing', 'Performance Testing', 'CI/CD', 'Python'],
            'experience_level': 'Mid-level'
        },
        'Database Administrator': {
            'required_skills': ['MySQL', 'PostgreSQL', 'Database Design', 'SQL', 'Backup & Recovery'],
            'preferred_skills': ['MongoDB', 'Oracle', 'Performance Tuning', 'Cloud Databases'],
            'experience_level': 'Mid-level'
        },
        'Software Architect': {
            'required_skills': ['System Design', 'Microservices', 'Design Patterns', 'Architecture'],
            'preferred_skills': ['Cloud Architecture', 'Scalability', 'Security', 'Performance'],
            'experience_level': 'Senior'
        },
        'Game Developer': {
            'required_skills': ['Unity', 'C#', 'Game Development', '3D Graphics'],
            'preferred_skills': ['Unreal Engine', 'C++', 'Animation', 'Physics'],
            'experience_level': 'Mid-level'
        },
        'Blockchain Developer': {
            'required_skills': ['Blockchain', 'Solidity', 'Smart Contracts', 'Ethereum'],
            'preferred_skills': ['Web3', 'DeFi', 'NFT', 'Cryptocurrency'],
            'experience_level': 'Senior'
        },
        'AI Research Scientist': {
            'required_skills': ['Deep Learning', 'Neural Networks', 'Research', 'Python', 'Mathematics'],
            'preferred_skills': ['Computer Vision', 'NLP', 'Reinforcement Learning', 'Publications'],
            'experience_level': 'Senior'
        },
        'Site Reliability Engineer': {
            'required_skills': ['Linux', 'Monitoring', 'Automation', 'Incident Management', 'Scripting'],
            'preferred_skills': ['Kubernetes', 'Prometheus', 'Grafana', 'Cloud Platforms'],
            'experience_level': 'Senior'
        },
        'Business Analyst': {
            'required_skills': ['Business Analysis', 'Requirements Gathering', 'Process Improvement', 'Documentation'],
            'preferred_skills': ['SQL', 'Data Visualization', 'Project Management', 'Stakeholder Management'],
            'experience_level': 'Mid-level'
        },
        'Java Developer': {
            'required_skills': ['Java', 'Spring Boot', 'MySQL', 'Maven', 'Git'],
            'preferred_skills': ['Spring Framework', 'Hibernate', 'REST API', 'JUnit'],
            'experience_level': 'Mid-level'
        },
        'Java Full Stack Developer': {
            'required_skills': ['Java', 'Spring Boot', 'JavaScript', 'React', 'MySQL'],
            'preferred_skills': ['Angular', 'Microservices', 'Docker', 'AWS'],
            'experience_level': 'Mid-level'
        },
        'Enterprise Java Developer': {
            'required_skills': ['Java', 'Spring Framework', 'JPA', 'Enterprise Applications', 'Design Patterns'],
            'preferred_skills': ['Spring Security', 'Apache Kafka', 'Redis', 'Microservices'],
            'experience_level': 'Senior'
        },
        'Android Developer': {
            'required_skills': ['Java', 'Kotlin', 'Android SDK', 'Mobile Development'],
            'preferred_skills': ['Jetpack Compose', 'Firebase', 'Room Database', 'MVVM'],
            'experience_level': 'Mid-level'
        }
    }
    
    job_req = job_requirements.get(target_job, job_requirements['Python Developer'])
    
    # Calculate skill gaps
    required_skills = job_req['required_skills']
    preferred_skills = job_req['preferred_skills']
    
    skill_analysis = {
        'target_job': target_job,
        'required_skills_analysis': [],
        'preferred_skills_analysis': [],
        'overall_readiness': 0,
        'missing_skills': [],
        'improvement_areas': []
    }
    
    # Analyze required skills
    required_score = 0
    for skill in required_skills:
        proficiency = user_skills.get(skill, None)
        if proficiency:
            score = get_proficiency_score(proficiency)
            required_score += score
            status = 'have' if score > 0 else 'missing'
        else:
            score = 0
            status = 'missing'
            skill_analysis['missing_skills'].append(skill)
        
        skill_analysis['required_skills_analysis'].append({
            'skill': skill,
            'user_proficiency': proficiency,
            'score': score,
            'status': status,
            'progress_percentage': min(score * 33, 100)  # Convert to percentage
        })
    
    # Analyze preferred skills
    preferred_score = 0
    for skill in preferred_skills:
        proficiency = user_skills.get(skill, None)
        if proficiency:
            score = get_proficiency_score(proficiency)
            preferred_score += score
            status = 'have' if score > 0 else 'missing'
        else:
            score = 0
            status = 'missing'
        
        skill_analysis['preferred_skills_analysis'].append({
            'skill': skill,
            'user_proficiency': proficiency,
            'score': score,
            'status': status,
            'progress_percentage': min(score * 33, 100)
        })
    
    # Calculate overall readiness
    total_required = len(required_skills) * 3  # Max score per skill is 3
    total_preferred = len(preferred_skills) * 3
    
    required_percentage = (required_score / total_required) * 100 if total_required > 0 else 0
    preferred_percentage = (preferred_score / total_preferred) * 100 if total_preferred > 0 else 0
    
    # Overall readiness weighted 70% required, 30% preferred
    skill_analysis['overall_readiness'] = round((required_percentage * 0.7) + (preferred_percentage * 0.3), 1)
    skill_analysis['required_percentage'] = round(required_percentage, 1)
    skill_analysis['preferred_percentage'] = round(preferred_percentage, 1)
    
    # Generate improvement suggestions
    if skill_analysis['overall_readiness'] < 70:
        skill_analysis['improvement_areas'] = generate_improvement_suggestions(skill_analysis['missing_skills'])
    
    return skill_analysis

def get_proficiency_score(proficiency):
    """Convert proficiency level to numeric score"""
    proficiency_scores = {
        'Beginner': 1,
        'Intermediate': 2,
        'Advanced': 3
    }
    return proficiency_scores.get(proficiency, 0)

def get_available_job_titles():
    """Get list of available job titles for analysis"""
    return ['Python Developer', 'Full Stack Developer', 'Data Scientist', 'DevOps Engineer', 'Frontend Developer', 'Backend Developer', 'Mobile App Developer', 'Machine Learning Engineer', 'Cloud Architect', 'Cybersecurity Analyst', 'UI/UX Designer', 'Product Manager', 'QA Engineer', 'Database Administrator', 'Software Architect', 'Game Developer', 'Blockchain Developer', 'AI Research Scientist', 'Site Reliability Engineer', 'Business Analyst', 'Java Developer', 'Java Full Stack Developer', 'Enterprise Java Developer', 'Android Developer']

def generate_improvement_suggestions(missing_skills):
    """Generate learning suggestions for missing skills"""
    suggestions = []
    for skill in missing_skills[:5]:  # Limit to top 5 suggestions
        suggestions.append({
            'skill': skill,
            'course': f"Complete {skill} Course",
            'provider': 'Coursera',
            'duration': '4-6 weeks',
            'level': 'Beginner to Intermediate',
            'priority': 'High' if skill in ['Python', 'JavaScript', 'React', 'AWS'] else 'Medium'
        })
    return suggestions

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/analyze_resume')
def analyze_resume():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('analyze_resume.html')

@app.route('/api/save-skills', methods=['POST'])
def save_skills():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not logged in'}), 401
    
    data = request.get_json()
    if not data or 'skills' not in data:
        return jsonify({'status': 'error', 'message': 'No skills provided'}), 400
    
    user_id = session['user_id']
    skills = data['skills']
    
    if MYSQL_AVAILABLE:
        try:
            connection = get_db_connection()
            if connection:
                cursor = connection.cursor()
                # Clear existing skills
                cursor.execute("DELETE FROM user_skills WHERE user_id = %s", (user_id,))
                
                # Add new skills
                for skill in skills:
                    cursor.execute(
                        """
                        INSERT INTO user_skills (user_id, skill_name, skill_type, proficiency_level)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (user_id, skill, 'IT', 'Intermediate')  # Default to IT type and Intermediate proficiency
                    )
                
                connection.commit()
                cursor.close()
                connection.close()
                return jsonify({'status': 'success', 'message': 'Skills saved successfully'})
                
        except Exception as e:
            print(f"Error saving skills: {e}")
            return jsonify({'status': 'error', 'message': 'Database error'}), 500
    else:
        # In-memory storage for demo
        user_skills_db[user_id] = [(skill, 'IT', 'Intermediate') for skill in skills]
        return jsonify({'status': 'success', 'message': 'Skills saved successfully'})

def generate_job_recommendations(user_skills):
    """Generate job recommendations based on user skills"""
    # Sample job data (in real implementation, this would come from APIs)
    job_database = [
        {
            'title': 'Python Developer',
            'company': 'Tech Corp',
            'location': 'Remote',
            'skills': ['Python', 'Django', 'MySQL', 'Git'],
            'experience': 'Mid-level',
            'salary': '$70,000 - $90,000'
        },
        {
            'title': 'Full Stack Developer',
            'company': 'StartupXYZ',
            'location': 'New York',
            'skills': ['JavaScript', 'React', 'Node.js', 'MongoDB'],
            'experience': 'Mid-level',
            'salary': '$80,000 - $100,000'
        },
        {
            'title': 'Data Scientist',
            'company': 'Data Analytics Inc',
            'location': 'San Francisco',
            'skills': ['Python', 'Machine Learning', 'Data Science'],
            'experience': 'Senior',
            'salary': '$100,000 - $130,000'
        },
        {
            'title': 'DevOps Engineer',
            'company': 'Cloud Solutions',
            'location': 'Remote',
            'skills': ['AWS', 'Docker', 'Kubernetes', 'Linux'],
            'experience': 'Mid-level',
            'salary': '$85,000 - $110,000'
        },
        {
            'title': 'Frontend Developer',
            'company': 'Design Studio',
            'location': 'Los Angeles',
            'skills': ['JavaScript', 'React', 'HTML5', 'CSS3'],
            'experience': 'Entry-level',
            'salary': '$60,000 - $80,000'
        },
        {
            'title': 'Java Developer',
            'company': 'Tech Corp',
            'location': 'Remote',
            'skills': ['Java', 'Spring Boot', 'MySQL', 'Maven', 'Git'],
            'experience': 'Mid-level',
            'salary': '$70,000 - $90,000'
        },
        {
            'title': 'Java Full Stack Developer',
            'company': 'StartupXYZ',
            'location': 'New York',
            'skills': ['Java', 'Spring Boot', 'JavaScript', 'React', 'MySQL'],
            'experience': 'Mid-level',
            'salary': '$80,000 - $100,000'
        },
        {
            'title': 'Enterprise Java Developer',
            'company': 'Data Analytics Inc',
            'location': 'San Francisco',
            'skills': ['Java', 'Spring Framework', 'JPA', 'Enterprise Applications', 'Design Patterns'],
            'experience': 'Senior',
            'salary': '$100,000 - $130,000'
        },
        {
            'title': 'Android Developer',
            'company': 'Cloud Solutions',
            'location': 'Remote',
            'skills': ['Java', 'Kotlin', 'Android SDK', 'Mobile Development'],
            'experience': 'Mid-level',
            'salary': '$85,000 - $110,000'
        }
    ]
    
    # Calculate similarity scores
    recommendations = []
    for job in job_database:
        skill_match = len(set(user_skills) & set(job['skills']))
        if skill_match > 0:
            similarity_score = skill_match / len(job['skills'])
            job['match_score'] = round(similarity_score * 100, 1)
            job['matching_skills'] = list(set(user_skills) & set(job['skills']))
            recommendations.append(job)
    
    # Sort by match score
    recommendations.sort(key=lambda x: x['match_score'], reverse=True)
    
    return recommendations

def get_upskill_suggestions(missing_skills):
    """Get upskilling course suggestions"""
    course_suggestions = []
    for skill in missing_skills:
        course_suggestions.append({
            'skill': skill,
            'course': f"Complete {skill} Course",
            'provider': 'Coursera',
            'duration': '4-6 weeks',
            'level': 'Beginner to Intermediate'
        })
    
    return course_suggestions

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/upload-resume', methods=['POST'])
def upload_resume():
    if 'file' not in request.files:
        return jsonify({
            'status': 'error',
            'message': 'No file part'
        }), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({
            'status': 'error',
            'message': 'No selected file'
        }), 400
    
    if file and allowed_file(file.filename):
        try:
            # Secure the filename and save to upload folder
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Process the resume
            result = resume_processor.process_resume(filepath)
            
            # Clean up the saved file after processing
            try:
                os.remove(filepath)
            except Exception as e:
                print(f"Warning: Could not delete temporary file {filepath}: {e}")
            
            return jsonify(result)
            
        except Exception as e:
            print(f"Error processing resume: {e}")
            return jsonify({
                'status': 'error',
                'message': f'Error processing file: {str(e)}'
            }), 500
    
    return jsonify({
        'status': 'error',
        'message': 'File type not allowed. Please upload a PDF or DOCX file.'
    }), 400

@app.route('/hiring_companies')
def hiring_companies():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('hiring_companies.html')

@app.route('/api/analyze_hiring_companies', methods=['POST'])
def api_analyze_hiring_companies():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        keywords = data.get('keywords', 'developer OR engineer OR analyst OR manager OR designer OR consultant OR specialist')
        location = data.get('location', 'India')
        
        analyzer = hiring_companies_analyzer
        results = analyzer.analyze_hiring_companies(keywords, location)
        
        return jsonify({
            'success': True,
            'data': results
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def format_date(date_str):
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        return None

if __name__ == '__main__':
    init_database()
    app.run(debug=True)
