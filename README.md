# DocAssembler: AI-Powered Document Research & Assembly System

An intelligent document assembly system that combines targeted web crawling, AI-driven research compilation, and smart template-based document generation. DocAssembler helps users create comprehensive documents by automatically gathering, analyzing, and synthesizing information from various web sources.

## 🎯 Core Features

### 1. Intelligent Web Documentation Crawler
- Crawls entire website directories to gather documentation
- Focuses on process documentation, API specs, software instructions
- Supports various documentation types:
  - Technical documentation
  - API documentation
  - Process instructions
  - Wiki pages
  - Social media profiles
  - Knowledge bases

### 2. AI Research Compilation
- Tag-based research gathering
- Accepts user summaries and topic keywords
- Performs deep web searches on individual tags
- Analyzes tag relationships and domain contexts
- Generates comprehensive research reports in PDF/Markdown
- Similar to OpenAI's DeepResearch functionality

### 3. Smart Template-Based Document Assembly
- Semi-automated document completion
- User provides partial information
- AI completes missing sections
- Supported templates include:
  - Software Requirements Specification (SRS)
  - Executive Summaries
  - CREST Data Problem Reports
  - RFP Proposals
  - Report Abstracts
  - Plot Summaries
  - Research Synopses

## Project Components

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

3. **Web Interface** (`services/web` and `apps/rag-web`):
   - React/Vite application for core features
   - Next.js RAG interface with data browser and report writer
   - Real-time processing feedback
   - Document preview and editing
 - Configuration management

4. **RAG Database** (`apps/backend`):
   - LangChain-based ingestion scripts for vector storage
   - Retrieval-Augmented Generation API endpoints
   - Embedding models configured for similarity search

## Database Recommendation

DocAssembler stores raw text in a traditional relational database and vectors in a vector database. By default we recommend **MySQL** for document metadata and **ChromaDB** for vector search. Example setup scripts are located in `scripts/databases/`.

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

## Usage Examples

### 1. Documentation Crawling
```python
from webcrawler.core.config import CrawlerConfig
from webcrawler.core.crawler import Crawler

# Configure and run documentation crawler
config = CrawlerConfig(
    start_url="https://docs.example.com",
    doc_types=["api", "wiki", "technical"],
    content_filters=["documentation", "guide", "manual"]
)

async with Crawler(config) as crawler:
    docs = await crawler.gather_documentation()
    print(f"Found {len(docs)} documentation pages")
```

### 2. Research Compilation
```python
from airesearch.core.researcher import Researcher
from airesearch.models.topic import ResearchTopic

# Configure research parameters
topic = ResearchTopic(
    tags=["kubernetes", "service mesh", "istio"],
    context="cloud native architecture",
    depth="technical"
)

# Generate research report
researcher = Researcher()
report = await researcher.compile_research(
    topic=topic,
    output_format="pdf",
    include_citations=True
)
```

### 3. Template-Based Document
```python
from docgen.core.assembler import DocumentAssembler
from docgen.models.template import Template

# Create SRS document from template
assembler = DocumentAssembler()
srs_doc = await assembler.create_document(
    template=Template.SRS,
    initial_content={
        "project_name": "MyProject",
        "project_scope": "Cloud-based service...",
    },
    auto_complete=True
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

## Configuration Options

### Documentation Crawler
- `doc_types`: Types of documentation to gather
  - api, wiki, technical, process, social
- `content_filters`: Content type filters
- `depth`: Crawling depth configuration
- `extract_assets`: Include images and diagrams
- `rate_limits`: Domain-specific rate limiting

### AI Research
- `search_depth`: Research depth level
- `tag_relationships`: Tag correlation settings
- `source_quality`: Source validation rules
- `citation_style`: Citation format
- `analysis_level`: Research analysis depth

### Document Templates
- `templates/`: Customizable document templates
  - SRS Template
  - Executive Summary Template
  - RFP Template
  - Research Report Template
- `completion_rules/`: AI completion guidelines
- `style_guides/`: Document styling rules

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
