import markdown
import bleach
from markupsafe import Markup

# Custom Jinja2 filter for markdown rendering
def markdown_filter(text):
    if not text:
        return ""
    
    # Configure markdown extensions for better formatting
    md = markdown.Markdown(extensions=[
        'markdown.extensions.extra',      # Tables, fenced code blocks, etc.
        'markdown.extensions.nl2br',      # Convert newlines to <br>
        'markdown.extensions.sane_lists'  # Better list handling
    ])
    
    # Convert markdown to HTML
    html = md.convert(text)
    
    # Sanitize HTML to prevent XSS attacks
    allowed_tags = [
        'p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'ul', 'ol', 'li', 'blockquote', 'code', 'pre', 'a', 'table', 'thead',
        'tbody', 'tr', 'th', 'td', 'hr'
    ]
    allowed_attributes = {
        'a': ['href', 'title', 'rel'],
        'table': ['class'],
        'th': ['align'],
        'td': ['align']
    }
    
    clean_html = bleach.clean(
        html,
        tags=allowed_tags,
        attributes=allowed_attributes,
        protocols=['http', 'https', 'mailto'],
        strip=True
    )
    clean_html = clean_html.replace('<a ', '<a rel="nofollow noopener noreferrer" ')
    return Markup(clean_html)
