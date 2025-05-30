# Documentation Assembly System

A comprehensive system for crawling web content and generating structured documentation with AI capabilities.

## Project Overview

This project consists of three main components:

1. **Web Crawler** (`packages/webcrawler`):
   - Intelligent web crawling with domain/subdomain support
   - Respects robots.txt and implements rate limiting
   - Concurrent crawling with proper session management
   - Content extraction and relationship mapping

2. **Documentation Generator** (`packages/docgen`):
   - Markdown and HTML processing
   - Table of contents generation
   - PDF output support
   - Template-based document generation
   - Metadata handling

3. **Web Interface** (`services/web`):
   - React/Vite-based web application
   - Real-time processing feedback
   - Document preview and editing
   - Configuration management

## Getting Started

### Prerequisites

- Python 3.12+
- Node.js 20+
- Docker (optional)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/cloudcurio/doc_assembler_web.git
   cd doc_assembler_web
   ```

2. **Set up Python packages:**
   ```bash
   # Install Poetry
   curl -sSL https://install.python-poetry.org | python3 -

   # Install webcrawler package
   cd packages/webcrawler
   poetry install

   # Install docgen package
   cd ../docgen
   poetry install
   ```

3. **Set up web interface:**
   ```bash
   cd ../../services/web
   npm install
   ```

### Development Setup

1. **Install pre-commit hooks:**
   ```bash
   pip install pre-commit
   pre-commit install
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

### Running Tests

```bash
# Run webcrawler tests
cd packages/webcrawler
poetry run pytest

# Run docgen tests
cd ../docgen
poetry run pytest

# Run web interface tests
cd ../../services/web
npm test
```

## Usage

### Web Crawler

```python
from webcrawler.core.config import CrawlerConfig
from webcrawler.core.crawler import Crawler

config = CrawlerConfig(
    start_url="https://example.com",
    max_depth=3,
    max_pages=100
)

async with Crawler(config) as crawler:
    async for url, content, links in crawler.crawl():
        print(f"Crawled: {url}")
```

### Document Generator

```python
from docgen.core.processor import DocumentProcessor
from docgen.models.document import DocumentType

processor = DocumentProcessor()
document = processor.process_document(
    content="# My Document\n\nContent here...",
    doc_type=DocumentType.MARKDOWN
)
```

## Docker Support

Build and run using Docker:

```bash
# Build images
docker compose build

# Run services
docker compose up -d
```

## Configuration

### Web Crawler

- `max_depth`: Maximum crawl depth (default: 3)
- `max_pages`: Maximum pages to crawl (default: 1000)
- `requests_per_second`: Rate limit (default: 2.0)
- `respect_robots_txt`: Follow robots.txt rules (default: True)

### Document Generator

- Template customization in `templates/`
- Output format configuration
- Metadata schema definitions

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

- Website: [cloudcurio.cc](https://cloudcurio.cc)
- Email: dev@cloudcurio.cc

# React + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Babel](https://babeljs.io/) for Fast Refresh
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/) for Fast Refresh

## Expanding the ESLint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and [`typescript-eslint`](https://typescript-eslint.io) in your project.
