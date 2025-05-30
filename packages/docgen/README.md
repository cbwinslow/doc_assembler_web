# CloudCurio DocGen

A powerful documentation generator with AI capabilities, supporting multiple input formats and producing highly structured, searchable documentation.

## Key Features

- **Multiple Input Formats**: Support for Markdown, HTML, and more
- **Intelligent Processing**: Smart content structure analysis
- **Template System**: Flexible document templating
- **Metadata Handling**: Rich metadata extraction and management
- **PDF Generation**: High-quality PDF output
- **Table of Contents**: Automatic TOC generation
- **Semantic Analysis**: Content relationship mapping
- **Type Safety**: Full type hinting support

## Installation

```bash
# Using poetry (recommended)
poetry add cloudcurio-docgen

# Using pip
pip install cloudcurio-docgen

# From source
git clone https://github.com/cloudcurio/doc_assembler_web.git
cd doc_assembler_web/packages/docgen
poetry install
```

## Quick Start

### Process Markdown

```python
from docgen.core.processor import DocumentProcessor
from docgen.models.document import DocumentType

processor = DocumentProcessor()

# Process a Markdown document
document = processor.process_document(
    content="""# My Document
    
## Introduction
This is a test document.

## Features
- Feature 1
- Feature 2
    """,
    doc_type=DocumentType.MARKDOWN
)

# Access document structure
print(f"Title: {document.metadata.title}")
print(f"Sections: {len(document.sections)}")
```

### Generate PDF

```python
from docgen.core.template import TemplateManager, TemplateConfig

# Initialize template manager
template_manager = TemplateManager(
    TemplateConfig(template_dir="./templates")
)

# Generate PDF
pdf_content = template_manager.render_document(
    document,
    template_name="pdf_template"
)
```

## Document Processing

### Supported Input Formats

- Markdown (`.md`)
- HTML (`.html`)
- Plain Text (`.txt`)
- PDF (coming soon)

### Content Analysis

```python
# Extract document structure
document = processor.process_document(content, DocumentType.MARKDOWN)

# Access sections
for section in document.sections:
    print(f"Section: {section.heading}")
    print(f"Level: {section.level}")
    print(f"Content: {section.content}")
    print(f"Tags: {section.tags}")
```

## Template System

### Directory Structure

```
templates/
├── default/
│   ├── template.json     # Configuration
│   ├── content.html     # Content template
│   └── style.css       # Styling
├── pdf/
│   ├── template.json
│   └── template.html
└── report/
    └── ...
```

### Template Configuration

```json
{
    "name": "technical_doc",
    "description": "Technical documentation template",
    "template_type": "html",
    "required_fields": [
        "title",
        "author",
        "version"
    ],
    "optional_fields": [
        "description",
        "tags"
    ]
}
```

### Template Example

```html
<!DOCTYPE html>
<html>
<head>
    <title>{{ document.metadata.title }}</title>
    <meta name="author" content="{{ document.metadata.author }}">
    <style>
        {% include "style.css" %}
    </style>
</head>
<body>
    <header>
        <h1>{{ document.metadata.title }}</h1>
        <p class="author">{{ document.metadata.author }}</p>
    </header>

    {% if document.table_of_contents %}
    <nav class="toc">
        <h2>Table of Contents</h2>
        {% for entry in document.table_of_contents %}
        <div class="toc-entry level-{{ entry.level.value }}">
            <a href="#{{ entry.anchor }}">{{ entry.title }}</a>
        </div>
        {% endfor %}
    </nav>
    {% endif %}

    <main>
        {% for section in document.sections %}
        <section id="{{ section.anchor }}">
            <h{{ section.level.value }}>{{ section.heading }}</h{{ section.level.value }}>
            {{ section.content | safe }}
        </section>
        {% endfor %}
    </main>
</body>
</html>
```

## Metadata Handling

### Metadata Structure

```python
@dataclass
class Metadata:
    title: str
    description: Optional[str] = None
    author: Optional[str] = None
    created_date: datetime = field(default_factory=datetime.now)
    modified_date: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)
    source_url: Optional[str] = None
    language: str = "en"
    custom_fields: Dict[str, str] = field(default_factory=dict)
```

### Working with Metadata

```python
# Create document with metadata
metadata = Metadata(
    title="API Documentation",
    author="John Doe",
    tags=["api", "reference"],
    custom_fields={"version": "1.0.0"}
)

document = processor.process_document(
    content=content,
    doc_type=DocumentType.MARKDOWN,
    metadata=metadata
)
```

## PDF Generation

### Basic PDF Generation

```python
from docgen.core.pdf import PDFGenerator

generator = PDFGenerator()
pdf_bytes = generator.generate(document)

with open("output.pdf", "wb") as f:
    f.write(pdf_bytes)
```

### Customized PDF Output

```python
pdf_config = PDFConfig(
    page_size="A4",
    margin_top=25.4,
    margin_bottom=25.4,
    margin_left=25.4,
    margin_right=25.4,
    header_template="templates/pdf/header.html",
    footer_template="templates/pdf/footer.html"
)

pdf_bytes = generator.generate(
    document,
    config=pdf_config
)
```

## Development

### Setup Environment

```bash
# Clone repository
git clone https://github.com/cloudcurio/doc_assembler_web.git
cd doc_assembler_web/packages/docgen

# Install dependencies
poetry install

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=docgen

# Run specific tests
poetry run pytest tests/unit/test_processor.py
```

### Code Quality

```bash
# Format code
poetry run black .

# Type checking
poetry run mypy src/docgen

# Linting
poetry run pylint src/docgen
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and quality checks
5. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) for details.

