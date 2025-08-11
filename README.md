# Job Application Manager

A comprehensive Flask web application for managing job applications, generating tailored CVs and cover letters using LaTeX, and tracking application progress.

## Features

- **Job Application Management**: Track job applications with company, title, description, and status
- **Web Scraping**: Automatically extract job details from posting URLs
- **Skills Analysis**: Match your skills against job descriptions with scoring
- **LaTeX Document Generation**: Create professional CVs and cover letters using LaTeX templates
- **PDF Generation**: Compile LaTeX documents to PDF format with section file support
- **Template Management**: Create and manage reusable LaTeX templates (database or file-based)
- **File-based Templates**: Support for complex LaTeX templates with section files (sections/, styles/, etc.)
- **User Profile**: Store personal information and skills for document generation

## Technical Stack

- **Backend**: Python 3, Flask
- **Database**: SQLite3 (using Flask-SQLAlchemy)
- **Frontend**: Bootstrap 5, Font Awesome
- **PDF Generation**: LaTeX compiler (pdflatex)
- **Web Scraping**: BeautifulSoup4, requests

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd JobApp_v2
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Install LaTeX** (required for PDF generation):
   - **Windows**: Install MiKTeX or TeX Live
   - **macOS**: Install MacTeX
   - **Linux**: Install TeX Live (`sudo apt-get install texlive-full`)

5. **Run the application**:
   ```bash
   python app.py
   ```

6. **Access the application**:
   Open your browser and go to `http://localhost:5000`

## Usage

### 1. Set Up Your Profile

1. Navigate to "Profile" in the navigation menu
2. Fill in your personal information (name, email, phone, LinkedIn, GitHub)
3. Add your skills (comma-separated)
4. Save your profile

### 2. Create LaTeX Templates

1. Go to "Templates" in the navigation menu
2. Choose between database or file-based templates:
   - **Database Templates**: Simple templates stored in the database
   - **File-based Templates**: Complex templates with section files (sections/, styles/, etc.)
3. Create templates for your CV and cover letters
4. Use placeholders like `{{NAME}}`, `{{EMAIL}}`, `{{COMPANY}}`, `{{JOB_TITLE}}`
5. For file-based templates, use `\input{sections/filename}` to include section files
6. Save your templates

#### Template Types

**Database Templates**
- Simple LaTeX content stored in the database
- Good for basic CVs and cover letters
- Easy to edit through the web interface

**File-based Templates**
- Complex LaTeX templates with section files
- Support for `\input{sections/...}` commands
- Stored in `documents/templates_latex/` directory
- Recommended structure:
  ```
  documents/templates_latex/
  ├── your_template.tex          # Main template file
  ├── _header.tex               # Header file
  ├── TLCresume.sty             # Style file
  └── sections/                 # Section files
      ├── education.tex
      ├── experience.tex
      ├── skills.tex
      └── projects.tex
  ```

### 3. Add Job Applications

1. Click "New Job" in the navigation menu
2. Optionally paste a job posting URL and click "Scrape" to auto-fill details
3. Fill in company, title, and description
4. Save the application

### 4. Analyze and Generate Documents

1. Click on a job application to view details
2. Review the skills analysis and match score
3. Select a template and document type
4. Generate and download PDF documents

## Project Structure

```
JobApp_v2/
├── app.py                 # Main application instance
├── config.py             # Configuration settings
├── models/              # Database models package
│   └── __init__.py      # Model definitions
├── requirements.txt      # Python dependencies
├── README.md            # This file
├── routes/              # Flask blueprints
│   ├── __init__.py
│   ├── main.py          # Main routes (dashboard, user profile)
│   ├── jobs.py          # Job-specific routes
│   ├── templates.py     # Template management routes
│   └── forms.py         # WTForms definitions
├── templates/           # HTML templates organized by domain
│   ├── base.html        # Base template with theme support
│   ├── dashboard.html   # Main dashboard
│   ├── components/      # Reusable template components
│   │   ├── forms.html   # Form field macros and utilities
│   │   ├── cards.html   # Card component macros
│   │   └── modals.html  # Modal component macros
│   ├── jobs/           # Job-related templates
│   │   ├── new_job.html     # New job application form
│   │   ├── edit_job.html    # Edit job application
│   │   ├── job_detail.html  # Job details with logging
│   │   └── add_log.html     # Add log entry form
│   ├── user/           # User-related templates
│   │   └── user_data.html   # User profile management
│   └── templates_mgmt/ # Template management
│       ├── templates.html        # Template listing
│       ├── template_create.html  # Create template
│       ├── template_view_edit.html # View/edit template
│       └── templates_landing.html  # Template landing page
├── static/              # Static files (CSS, JS, images)
│   ├── css/            # Organized stylesheets
│   │   ├── main.css    # Main styles with theme support
│   │   └── components/ # Component-specific styles
│   │       ├── cards.css    # Card component styles
│   │       └── forms.css    # Form component styles
│   ├── js/             # JavaScript modules
│   │   ├── main.js     # Main application JavaScript
│   │   └── utils/      # JavaScript utility modules
│   │       ├── ajax.js      # AJAX helper functions
│   │       ├── ui.js        # UI utility functions
│   │       └── forms.js     # Form validation utilities
│   └── images/         # Image assets
├── services/            # Business logic service layer
│   ├── __init__.py      # Service exports
│   ├── base_service.py  # Base service with common operations
│   ├── job_service.py   # Job application business logic
│   ├── user_service.py  # User data management
│   ├── log_service.py   # Activity logging operations
│   └── template_service.py # Template management
├── utils/               # Python utility modules
│   ├── __init__.py
│   ├── analysis.py     # Skills matching algorithm
│   ├── latex.py        # LaTeX compilation utilities
│   ├── scraper.py      # Web scraping utilities
│   ├── forms.py        # Form validation utilities
│   └── responses.py    # Response formatting utilities
├── tests/               # Test suite
│   ├── __init__.py
│   ├── conftest.py     # Test configuration
│   ├── test_models.py  # Model tests
│   ├── test_routes.py  # Route tests
│   └── test_utils.py   # Utility tests
└── documents/           # Generated documents and templates
    └── templates_latex/ # LaTeX template files
```

## 🔧 **Code Organization & Architecture**

### **Refactored Structure**
The codebase has been significantly refactored to improve maintainability, reduce duplication, and enhance code organization:

#### **Python Utilities**
- **`utils/database.py`**: Centralized database operations with error handling
- **`utils/responses.py`**: Consistent API response formatting and flash messaging
- **`utils/forms.py`**: Form validation utilities and custom validators
- **`utils/analysis.py`**: Skills matching and job analysis algorithms
- **`utils/latex.py`**: LaTeX compilation and PDF generation
- **`utils/scraper.py`**: Web scraping functionality for job postings

#### **Frontend Components**
- **Template Macros**: Reusable Jinja2 macros for forms, cards, and modals
- **JavaScript Modules**: Organized utility modules for AJAX, UI, and form handling
- **CSS Components**: Component-based styling with theme support
- **Responsive Design**: Mobile-first approach with Bootstrap 5

#### **Key Improvements**
- ✅ **Eliminated Code Duplication**: Extracted common patterns into reusable utilities
- ✅ **Improved Error Handling**: Centralized error handling with consistent user feedback
- ✅ **Enhanced Maintainability**: Clear separation of concerns and modular architecture
- ✅ **Better Testing**: Comprehensive test suite with proper fixtures
- ✅ **Theme Support**: Dark/light theme switching with CSS custom properties
- ✅ **Accessibility**: Improved keyboard navigation and screen reader support

## Database Models

### UserData
- Personal information (name, email, phone, LinkedIn, GitHub)
- Skills (comma-separated string)

### MasterTemplate
- LaTeX template content
- Template name and metadata

### JobApplication
- Job details (company, title, description, URL)
- Application status and timestamps
- **Status Options**:
  - **Collected**: Job information collected but not yet applied
  - **Applied**: Application submitted
  - **Process**: Application is being processed/reviewed
  - **Waiting Decision**: Waiting for hiring decision
  - **Completed**: Application process completed (accepted)
  - **Rejected**: Application rejected

### Document
- Generated PDF files
- Links to job applications

## API Endpoints

### Main Routes
- `GET /` - Dashboard
- `GET/POST /user` - User profile management
- `GET/POST /templates` - Template management
- `GET /templates/<id>` - Get template content

### Job Routes
- `GET/POST /job/new` - Create new job application
- `GET /job/<id>` - Job details
- `POST /job/<id>/scrape` - Scrape job details from URL
- `POST /job/<id>/generate-pdf` - Generate PDF document
- `GET /job/<id>/download/<doc_id>` - Download generated PDF
- `POST /job/<id>/update-status` - Update application status

## Configuration

The application uses the following configuration options (in `config.py`):

- `SECRET_KEY`: Flask secret key for sessions
- `SQLALCHEMY_DATABASE_URI`: Database connection string
- `UPLOAD_FOLDER`: Directory for generated PDFs

## Dependencies

- Flask 2.3.3
- Flask-SQLAlchemy 3.0.5
- BeautifulSoup4 4.12.2
- requests 2.31.0
- lxml 4.9.3

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions, please create an issue in the repository.
