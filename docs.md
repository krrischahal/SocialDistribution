# Project Documentation

## Introduction
This project is a social networking platform that allows users to create, share, and manage posts. The platform supports user authentication and follows best practices for web development.

## Getting Started

### Requirements
asgiref==3.8.1
certifi==2024.8.30
charset-normalizer==3.4.0
coverage==7.6.3
Django==4.2.16
djangorestframework==3.15.2
drf-yasg==1.21.8
factory_boy==3.3.1
Faker==30.6.0
idna==3.10
inflection==0.5.1
packaging==24.1
pillow==11.0.0
python-dateutil==2.9.0.post0
pytz==2024.2
PyYAML==6.0.2
requests==2.32.3
six==1.16.0
sqlparse==0.5.1
typing_extensions==4.12.2
tzdata==2024.2
uritemplate==4.1.1
urllib3==2.2.3

### Installation 
1. Clone the repository:
   ```bash
   git clone https://github.com/uofa-cmput404/f24-project-royalblue.git
2. Create a virtual environment
3. Install the required packages
4. Make migrations
5. Start the server

### API Documentation
The project uses Swagger for API documentation. The API endpoints are documented automatically based on the docstrings provided in the views. To access the Swagger UI:

Start the development server (if not already running).
Navigate to http://127.0.0.1:8000/swagger/ in your browser.

### Tests
```bash
python3.11 manage.py test socialnetwork.tests
