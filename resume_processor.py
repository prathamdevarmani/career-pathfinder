import os
import re
import PyPDF2
from docx import Document
from typing import List, Dict, Union, Optional

class ResumeProcessor:
    def __init__(self):
        # Comprehensive technical skills database
        self.technical_skills = {
            'languages': [
                'python', 'javascript', 'java', 'c++', 'c#', 'c', 'php', 'ruby', 'go', 'swift', 
                'kotlin', 'typescript', 'r', 'scala', 'rust', 'dart', 'perl', 'haskell', 'lua', 'matlab'
            ],
            'web_frontend': [
                'html', 'html5', 'css', 'css3', 'sass', 'less', 'bootstrap', 'tailwind', 'material ui',
                'react', 'angular', 'vue', 'vue.js', 'vuejs', 'svelte', 'next.js', 'nuxt.js', 'gatsby',
                'redux', 'mobx', 'graphql', 'apollo', 'webpack', 'babel', 'npm', 'yarn', 'vite', 'parcel'
            ],
            'web_backend': [
                'node', 'node.js', 'express', 'nest.js', 'django', 'flask', 'fastapi', 'spring', 'spring boot',
                'ruby on rails', 'laravel', 'asp.net', 'asp.net core', '.net core', 'play framework',
                'phoenix', 'gin', 'echo', 'koa', 'hapi', 'sails.js', 'loopback', 'adonis.js', 'slim',
                'fastify', 'hono', 'deno', 'bun'
            ],
            'mobile': [
                'react native', 'flutter', 'ios', 'android', 'swift', 'kotlin', 'objective-c', 'xamarin',
                'ionic', 'phonegap', 'cordova', 'capacitor', 'kmm', 'kmm', 'kmm', 'kmm', 'kmm'
            ],
            'databases': [
                'mysql', 'postgresql', 'mongodb', 'redis', 'oracle', 'sql server', 'sqlite', 'mariadb',
                'cassandra', 'couchbase', 'dynamodb', 'firebase', 'firestore', 'realm', 'neo4j', 'arangodb',
                'couchdb', 'rethinkdb', 'influxdb', 'timescaledb', 'cockroachdb', 'scylladb', 'cosmosdb'
            ],
            'devops': [
                'docker', 'kubernetes', 'helm', 'terraform', 'ansible', 'puppet', 'chef', 'jenkins',
                'github actions', 'gitlab ci', 'circleci', 'travis ci', 'argo cd', 'flux', 'crossplane',
                'spinnaker', 'tekton', 'pulumi', 'serverless', 'aws cdk', 'sst', 'sst', 'sst', 'sst'
            ],
            'cloud': [
                'aws', 'amazon web services', 'azure', 'google cloud', 'gcp', 'digitalocean', 'heroku',
                'vercel', 'netlify', 'cloudflare', 'cloudflare workers', 'cloudflare pages', 'cloud run',
                'cloud functions', 'lambda', 'ec2', 's3', 'rds', 'dynamodb', 'aurora', 'sns', 'sqs', 'ses',
                'ecs', 'eks', 'fargate', 'cloudfront', 'route 53', 'vpc', 'iam', 'cognito', 'app sync',
                'app runner', 'lightsail', 'elastic beanstalk', 'elasticache', 'opensearch', 'kinesis',
                'msk', 'msk', 'msk', 'msk'
            ],
            'data_science': [
                'pandas', 'numpy', 'scipy', 'scikit-learn', 'tensorflow', 'pytorch', 'keras', 'opencv',
                'nltk', 'spacy', 'huggingface', 'transformers', 'datasets', 'tokenizers', 'ray', 'dask',
                'pyspark', 'apache spark', 'hadoop', 'hive', 'hbase', 'kafka', 'flink', 'beam', 'airflow',
                'prefect', 'dagster', 'mlflow', 'kubeflow', 'sagemaker', 'vertex ai', 'h2o', 'rapids',
                'rapids', 'rapids', 'rapids'
            ],
            'testing': [
                'jest', 'mocha', 'jasmine', 'karma', 'cypress', 'playwright', 'puppeteer', 'selenium',
                'testcafe', 'testing library', 'react testing library', 'enzyme', 'vitest', 'junit',
                'testng', 'pytest', 'unittest', 'rspec', 'cucumber', 'jbehave', 'serenity bdd', 'mabl',
                'appium', 'detox', 'espresso', 'xcuitest', 'xctest', 'junit', 'testng', 'testng', 'testng'
            ],
            'security': [
                'owasp', 'jwt', 'oauth', 'openid connect', 'saml', 'ldap', 'rbac', 'abac', 'pam', 'tls',
                'ssl', 'waf', 'siem', 'soc', 'vpn', 'vpc', 'sg', 'nacl', 'iam', 'pim', 'pam', 'pdp', 'pep',
                'pip', 'pip', 'pip', 'pip', 'pip'
            ]
        }
        
        # Normalization mapping for common variations
        self.skill_normalization = {
            'js': 'javascript',
            'reactjs': 'react',
            'vuejs': 'vue',
            'vue.js': 'vue',
            'nextjs': 'next.js',
            'nodejs': 'node.js',
            'nestjs': 'nest.js',
            'aws': 'amazon web services',
            'gcp': 'google cloud',
            'postgres': 'postgresql',
            'mongo': 'mongodb',
            'ms sql': 'sql server',
            'ms sql server': 'sql server',
            'azure functions': 'azure functions',
            'azure functions': 'azure functions',
            'azure functions': 'azure functions',
        }
        
        # Compile regex patterns for better performance
        self.email_pattern = re.compile(r'[\w\.-]+@[\w\.-]+\.\w+')
        self.url_pattern = re.compile(r'https?://\S+|www\.\S+')
        self.phone_pattern = re.compile(r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b')
        self.skill_pattern = self._build_skill_pattern()
    
    def _build_skill_pattern(self):
        """Build a regex pattern to match all skills"""
        all_skills = []
        for category in self.technical_skills.values():
            all_skills.extend(category)
        
        # Sort by length in descending order to match longer phrases first
        all_skills = sorted(list(set(all_skills)), key=len, reverse=True)
        
        # Escape special regex characters and create pattern
        escaped_skills = [re.escape(skill) for skill in all_skills]
        pattern = r'\b(' + '|'.join(escaped_skills) + r')\b'
        
        return re.compile(pattern, re.IGNORECASE)
    
    def _normalize_skill(self, skill: str) -> str:
        """Normalize skill name to a standard format"""
        # Convert to lowercase and strip whitespace
        skill = skill.lower().strip()
        
        # Apply normalization mappings
        skill = self.skill_normalization.get(skill, skill)
        
        # Handle special cases
        if skill == 'js':
            return 'javascript'
        elif skill == 'c#':
            return 'c#'
        elif skill == 'c++':
            return 'c++'
        elif skill == '.net':
            return '.net'
        elif skill == 'asp.net':
            return 'asp.net'
        
        # Capitalize first letter of each word, handle special cases
        parts = skill.split()
        normalized_parts = []
        
        for part in parts:
            if part in ['js', 'css', 'html', 'api', 'rest', 'grpc', 'graphql', 'aws', 'gcp', 'azure']:
                normalized_parts.append(part.upper())
            elif part in ['ios', 'iot', 'ai', 'ml', 'nlp', 'cv', 'ci', 'cd', 'devops', 'api']:
                normalized_parts.append(part.upper())
            elif part in ['javascript', 'typescript']:
                normalized_parts.append(part[0].upper() + part[1:])
            elif '-' in part:
                # Handle kebab-case
                normalized_parts.append('-'.join([p.capitalize() for p in part.split('-')]))
            else:
                normalized_parts.append(part.capitalize())
        
        return ' '.join(normalized_parts)

    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file."""
        try:
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ''
                for page in reader.pages:
                    text += page.extract_text() + '\n'
                # Basic cleaning
                text = self._clean_text(text)
                return text
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
            return ""

    def extract_text_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX file."""
        try:
            doc = Document(file_path)
            return '\n'.join([paragraph.text for paragraph in doc.paragraphs])
        except Exception as e:
            print(f"Error extracting text from DOCX: {e}")
            return ""

    def _clean_text(self, text: str) -> str:
        """Clean and normalize extracted text."""
        # Remove email addresses
        text = self.email_pattern.sub('', text)
        # Remove URLs
        text = self.url_pattern.sub('', text)
        # Remove phone numbers
        text = self.phone_pattern.sub('', text)
        # Remove multiple spaces and newlines
        text = ' '.join(text.split())
        return text.strip()

    def extract_skills(self, text: str) -> List[str]:
        """Extract and normalize skills from text."""
        if not text:
            return []
            
        # Find all skill matches
        matches = set()
        text_lower = text.lower()
        
        # Find all matches using the pre-built pattern
        for match in self.skill_pattern.finditer(text_lower):
            skill = match.group(0).lower()
            normalized_skill = self._normalize_skill(skill)
            matches.add(normalized_skill)
        
        return sorted(list(matches))

    def process_resume(self, file_path: str) -> Dict[str, Union[str, List[str]]]:
        """
        Process a resume file and extract skills.
        
        Args:
            file_path: Path to the resume file (PDF or DOCX)
            
        Returns:
            Dictionary with status, cleaned text, and extracted skills
        """
        if not os.path.exists(file_path):
            return {
                "status": "error",
                "message": "File not found"
            }
            
        # Determine file type and extract text
        file_ext = os.path.splitext(file_path)[1].lower()
        text = ""
        
        if file_ext == '.pdf':
            text = self.extract_text_from_pdf(file_path)
        elif file_ext == '.docx':
            text = self.extract_text_from_docx(file_path)
        else:
            return {
                "status": "error",
                "message": "Unsupported file format. Please upload a PDF or DOCX file."
            }
        
        if not text.strip():
            return {
                "status": "error",
                "message": "Unable to extract text from the file. The file might be empty or corrupted."
            }
        
        # Extract and normalize skills
        skills = self.extract_skills(text)
        
        return {
            "status": "success",
            "resume_text": text,
            "skills": skills
        }
