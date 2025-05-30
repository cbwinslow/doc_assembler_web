"""Unit tests for research templates functionality."""
import pytest
from datetime import date, datetime
from typing import Dict, Any
from pydantic import ValidationError

from airesearch.interfaces.document_interface import DocumentFormat
from airesearch.interfaces.templates import (
    BaseTemplate,
    BaseTemplateMetadata,
    TemplateSection
)
from airesearch.interfaces.research_templates import (
    ResearchReportTemplate,
    ResearchReportMetadata,
    ResearchMethodology,
    DataSource,
    ExecutiveSummaryTemplate,
    ExecutiveSummaryMetadata,
    SummaryLevel,
    TargetAudience,
    BusinessImpact,
    PriorityLevel,
    TechnicalAnalysisTemplate,
    TechnicalAnalysisMetadata,
    TechnicalComplexity,
    DevelopmentStatus,
    SystemRequirementLevel,
    PerformanceMetricType,
    DataVisualizationTemplate,
    DataVisualizationMetadata,
    VisualizationType,
    DataFormat,
    ChartType,
    ColorScheme,
    UpdateFrequency,
    DatasetMetrics,
    VisualizationConfig
)

# Base Template Tests
class TestTemplateImpl(BaseTemplate):
    """Test implementation of BaseTemplate."""
    
    def _initialize_sections(self) -> None:
        """Initialize test sections."""
        self.add_section(TemplateSection(
            name="test_section",
            required=True,
            order=0,
            content_type="text"
        ))
        self.add_section(TemplateSection(
            name="optional_section",
            required=False,
            order=1,
            content_type="text"
        ))

    async def format_content(self, content: Dict[str, Any]) -> str:
        """Format test content."""
        return "Test formatted content"

@pytest.fixture
def base_metadata():
    """Create base template metadata."""
    return BaseTemplateMetadata(
        title="Test Template",
        author="Test Author",
        keywords=["test", "template"],
        classification="test"
    )

@pytest.fixture
def base_template(base_metadata):
    """Create base template instance."""
    return TestTemplateImpl(
        name="test_template",
        format=DocumentFormat.PDF,
        metadata=base_metadata
    )

def test_base_template_initialization(base_template, base_metadata):
    """Test base template initialization."""
    assert base_template.name == "test_template"
    assert base_template.format == DocumentFormat.PDF
    assert base_template.metadata == base_metadata

def test_base_section_management(base_template):
    """Test section management functionality."""
    # Test initial sections
    sections = base_template.get_ordered_sections()
    assert len(sections) == 2
    assert sections[0].name == "test_section"
    assert sections[1].name == "optional_section"
    
    # Test adding new section
    new_section = TemplateSection(
        name="new_section",
        required=True,
        order=2,
        content_type="text"
    )
    base_template.add_section(new_section)
    assert len(base_template.get_ordered_sections()) == 3
    
    # Test removing section
    base_template.remove_section("new_section")
    assert len(base_template.get_ordered_sections()) == 2

def test_base_template_validation(base_template):
    """Test template validation."""
    assert base_template.validate_sections()
    
    # Remove required section
    base_template.remove_section("test_section")
    assert not base_template.validate_sections()

@pytest.mark.asyncio
async def test_base_format_content(base_template):
    """Test content formatting."""
    content = {"test": "content"}
    formatted = await base_template.format_content(content)
    assert formatted == "Test formatted content"

# Research Report Template Tests
@pytest.fixture
def research_metadata():
    """Create research report metadata."""
    return ResearchReportMetadata(
        title="Test Research Report",
        author="Test Researcher",
        research_period_start=date(2024, 1, 1),
        research_period_end=date(2024, 12, 31),
        methodology=ResearchMethodology.MIXED_METHODS,
        confidence_level=0.95,
        data_sources=[
            DataSource(
                name="Test Source",
                type="database",
                url="https://example.com",
                access_date=date(2024, 6, 1),
                reliability_score=0.9
            )
        ]
    )

@pytest.fixture
def research_template(research_metadata):
    """Create research report template."""
    return ResearchReportTemplate(
        name="test_research_report",
        format=DocumentFormat.PDF,
        metadata=research_metadata
    )

def test_research_template_initialization(research_template, research_metadata):
    """Test research template initialization."""
    assert research_template.name == "test_research_report"
    assert research_template.format == DocumentFormat.PDF
    assert research_template.metadata == research_metadata

def test_research_metadata_validation():
    """Test research metadata validation."""
    # Test invalid date range
    with pytest.raises(ValidationError):
        ResearchReportMetadata(
            title="Test",
            author="Test",
            research_period_start=date(2024, 12, 31),
            research_period_end=date(2024, 1, 1),
            methodology=ResearchMethodology.MIXED_METHODS,
            confidence_level=0.95
        )

    # Test invalid confidence level
    with pytest.raises(ValidationError):
        ResearchReportMetadata(
            title="Test",
            author="Test",
            research_period_start=date(2024, 1, 1),
            research_period_end=date(2024, 12, 31),
            methodology=ResearchMethodology.MIXED_METHODS,
            confidence_level=1.5
        )

# Executive Summary Template Tests
@pytest.fixture
def executive_metadata():
    """Create executive summary metadata."""
    return ExecutiveSummaryMetadata(
        title="Test Executive Summary",
        author="Test Executive",
        summary_level=SummaryLevel.BUSINESS,
        target_audience=[TargetAudience.EXECUTIVE],
        business_impact=BusinessImpact.HIGH,
        priority_level=PriorityLevel.HIGH,
        presentation_time=15,
        keywords=["executive", "summary"]
    )

@pytest.fixture
def executive_template(executive_metadata):
    """Create executive summary template."""
    return ExecutiveSummaryTemplate(
        name="test_executive_summary",
        format=DocumentFormat.PDF,
        metadata=executive_metadata
    )

def test_executive_template_initialization(executive_template, executive_metadata):
    """Test executive summary template initialization."""
    assert executive_template.name == "test_executive_summary"
    assert executive_template.format == DocumentFormat.PDF
    assert executive_template.metadata == executive_metadata

def test_executive_metadata_validation():
    """Test executive summary metadata validation."""
    # Test invalid presentation time
    with pytest.raises(ValidationError):
        ExecutiveSummaryMetadata(
            title="Test",
            author="Test",
            summary_level=SummaryLevel.BUSINESS,
            target_audience=[TargetAudience.EXECUTIVE],
            business_impact=BusinessImpact.HIGH,
            priority_level=PriorityLevel.HIGH,
            presentation_time=-1
        )

    # Test duplicate target audience
    metadata = ExecutiveSummaryMetadata(
        title="Test",
        author="Test",
        summary_level=SummaryLevel.BUSINESS,
        target_audience=[TargetAudience.EXECUTIVE, TargetAudience.EXECUTIVE],
        business_impact=BusinessImpact.HIGH,
        priority_level=PriorityLevel.HIGH
    )
    assert len(metadata.target_audience) == 1

@pytest.mark.asyncio
async def test_format_conversions():
    """Test format conversion across templates."""
    templates = [
        (TestTemplateImpl, BaseTemplateMetadata),
        (ResearchReportTemplate, ResearchReportMetadata),
        (ExecutiveSummaryTemplate, ExecutiveSummaryMetadata)
    ]
    
    for template_cls, metadata_cls in templates:
        # Create basic metadata
        metadata = metadata_cls(title="Test", author="Test")
        if isinstance(metadata, ResearchReportMetadata):
            metadata.research_period_start = date(2024, 1, 1)
            metadata.research_period_end = date(2024, 12, 31)
            metadata.methodology = ResearchMethodology.MIXED_METHODS
            metadata.confidence_level = 0.95
        elif isinstance(metadata, ExecutiveSummaryMetadata):
            metadata.summary_level = SummaryLevel.BUSINESS
            metadata.target_audience = [TargetAudience.EXECUTIVE]
            metadata.business_impact = BusinessImpact.HIGH
            metadata.priority_level = PriorityLevel.HIGH
        
        # Test each format
        for format in DocumentFormat:
            template = template_cls(
                name=f"test_{format.value}",
                format=format,
                metadata=metadata
            )
            assert template.format == format
            
            # Convert to DocumentTemplate
            doc_template = template.to_document_template()
            assert doc_template.format == format
            assert doc_template.name == template.name

# Technical Analysis Template Tests
@pytest.fixture
def technical_metadata():
    """Create technical analysis metadata."""
    return TechnicalAnalysisMetadata(
        title="Test Technical Analysis",
        author="Test Engineer",
        technology_stack=["Python 3.8", "PostgreSQL 13"],
        system_requirements={
            "cpu": SystemRequirementLevel.MEDIUM,
            "memory": SystemRequirementLevel.HIGH,
            "storage": SystemRequirementLevel.LOW
        },
        version_compatibility=">=1.0.0,<2.0.0",
        technical_complexity=TechnicalComplexity.HIGH,
        development_status=DevelopmentStatus.BETA,
        repository_links=[
            "https://github.com/org/repo",
            "https://github.com/org/docs"
        ],
        performance_benchmarks={
            "response_time_ms": 100.0,
            "throughput_rps": 1000.0,
            "memory_usage_mb": 512.0
        }
    )

@pytest.fixture
def technical_template(technical_metadata):
    """Create technical analysis template."""
    return TechnicalAnalysisTemplate(
        name="test_technical_analysis",
        format=DocumentFormat.PDF,
        metadata=technical_metadata
    )

def test_technical_template_initialization(technical_template, technical_metadata):
    """Test technical analysis template initialization."""
    assert technical_template.name == "test_technical_analysis"
    assert technical_template.format == DocumentFormat.PDF
    assert technical_template.metadata == technical_metadata

def test_technical_sections(technical_template):
    """Test technical analysis sections."""
    sections = technical_template.get_ordered_sections()
    required_sections = {
        "system_architecture",
        "technical_specifications",
        "implementation_details",
        "performance_metrics",
        "dependencies",
        "api_documentation",
        "deployment_guide"
    }
    
    section_names = {section.name for section in sections}
    assert required_sections.issubset(section_names)
    assert all(section.required for section in sections if section.name in required_sections)

def test_technical_metadata_validation():
    """Test technical metadata validation."""
    # Test invalid version compatibility
    with pytest.raises(ValidationError):
        TechnicalAnalysisMetadata(
            title="Test",
            author="Test",
            technology_stack=["Python"],
            system_requirements={"cpu": SystemRequirementLevel.LOW},
            version_compatibility="invalid",  # Invalid semver format
            technical_complexity=TechnicalComplexity.LOW,
            development_status=DevelopmentStatus.ALPHA
        )
    
    # Test invalid repository link
    with pytest.raises(ValidationError):
        TechnicalAnalysisMetadata(
            title="Test",
            author="Test",
            technology_stack=["Python"],
            system_requirements={"cpu": SystemRequirementLevel.LOW},
            version_compatibility="1.0.0",
            technical_complexity=TechnicalComplexity.LOW,
            development_status=DevelopmentStatus.ALPHA,
            repository_links=["not-a-url"]  # Invalid URL format
        )

def test_performance_metrics_validation(technical_template):
    """Test performance metrics validation."""
    valid_metrics = {
        "response_time_ms": 100.0,
        "throughput_rps": 1000.0,
        "memory_usage_mb": 512.0,
        "cpu_usage_percent": 75.0
    }
    assert technical_template.validate_performance_metrics(valid_metrics)
    
    invalid_metrics = {
        "response_time_ms": -100.0  # Invalid negative value
    }
    assert not technical_template.validate_performance_metrics(invalid_metrics)

def test_system_requirements_validation(technical_template):
    """Test system requirements validation."""
    valid_requirements = {
        "cpu": SystemRequirementLevel.HIGH,
        "memory": SystemRequirementLevel.MEDIUM,
        "storage": SystemRequirementLevel.LOW
    }
    assert technical_template.validate_system_requirements(valid_requirements)
    
    invalid_requirements = {
        "unknown": SystemRequirementLevel.LOW  # Unknown requirement type
    }
    assert not technical_template.validate_system_requirements(invalid_requirements)

@pytest.mark.asyncio
async def test_technical_markdown_formatting(technical_template):
    """Test technical analysis Markdown format output."""
    technical_template.format = DocumentFormat.MARKDOWN
    content = {
        "system_architecture": "# System Architecture\n\n```mermaid\ngraph TD;\\nA-->B;\\n```",
        "technical_specifications": "## Specifications\n\n* Spec 1\n* Spec 2",
        "implementation_details": "## Implementation\n\n```python\ndef main():\n    pass\n```",
        "performance_metrics": {
            "response_time_ms": 100.0,
            "throughput_rps": 1000.0
        },
        "dependencies": "## Dependencies\n\n* Dep 1\n* Dep 2",
        "api_documentation": "## API\n\n### Endpoints\n\n* GET /api/v1/test",
        "deployment_guide": "## Deployment\n\n1. Step 1\n2. Step 2"
    }
    
    formatted = await technical_template.format_content(content)
    assert "# Test Technical Analysis" in formatted
    assert "## System Architecture" in formatted
    assert "```mermaid" in formatted
    assert "```python" in formatted
    assert "## Performance Metrics" in formatted
    assert "| Metric | Value | Unit |" in formatted

@pytest.mark.asyncio
async def test_technical_html_formatting(technical_template):
    """Test technical analysis HTML format output."""
    technical_template.format = DocumentFormat.HTML
    content = {
        "system_architecture": "<div class='mermaid'>graph TD;A-->B;</div>",
        "technical_specifications": "<ul><li>Spec 1</li><li>Spec 2</li></ul>",
        "implementation_details": "<pre><code>def main():\n    pass</code></pre>",
        "performance_metrics": {
            "response_time_ms": 100.0,
            "throughput_rps": 1000.0
        },
        "dependencies": "<ul><li>Dep 1</li><li>Dep 2</li></ul>",
        "api_documentation": "<h3>API Endpoints</h3><ul><li>GET /api/v1/test</li></ul>",
        "deployment_guide": "<ol><li>Step 1</li><li>Step 2</li></ol>"
    }
    
    formatted = await technical_template.format_content(content)
    assert "<!DOCTYPE html>" in formatted
    assert "<title>Test Technical Analysis</title>" in formatted
    assert "<div class='mermaid'>" in formatted
    assert "<pre><code>" in formatted
    assert "<table class='metrics-table'>" in formatted

@pytest.mark.asyncio
async def test_technical_pdf_formatting(technical_template):
    """Test technical analysis PDF (LaTeX) format output."""
    content = {
        "system_architecture": "\\begin{figure}\n\\includegraphics{architecture.pdf}\n\\end{figure}",
        "technical_specifications": "\\begin{itemize}\n\\item Spec 1\n\\item Spec 2\n\\end{itemize}",
        "implementation_details": "\\begin{lstlisting}\ndef main():\n    pass\n\\end{lstlisting}",
        "performance_metrics": {
            "response_time_ms": 100.0,
            "throughput_rps": 1000.0
        },
        "dependencies": "\\begin{itemize}\n\\item Dep 1\n\\item Dep 2\n\\end{itemize}",
        "api_documentation": "\\section{API}\n\\subsection{Endpoints}\n\\begin{itemize}\n\\item GET /api/v1/test\n\\end{itemize}",
        "deployment_guide": "\\begin{enumerate}\n\\item Step 1\n\\item Step 2\n\\end{enumerate}"
    }
    
    formatted = await technical_template.format_content(content)
    assert "\\documentclass" in formatted
    assert "\\usepackage{listings}" in formatted
    assert "\\begin{figure}" in formatted
    assert "\\begin{lstlisting}" in formatted
    assert "\\begin{tabular}" in formatted

# Data Visualization Template Tests
@pytest.fixture
def visualization_metadata():
    """Create data visualization metadata."""
    return DataVisualizationMetadata(
        title="Test Data Visualization",
        author="Test Analyst",
        data_sources=[
            DataSource(
                name="Test Dataset",
                type="database",
                url="https://example.com/data",
                access_date=date(2024, 6, 1),
                reliability_score=0.95
            )
        ],
        visualizations=[
            VisualizationConfig(
                type=VisualizationType.CHART,
                chart_type=ChartType.BAR,
                color_scheme=ColorScheme.SEQUENTIAL,
                interactive=True,
                data_format=DataFormat.JSON,
                accessibility_features=[
                    "alt_text",
                    "aria_labels",
                    "color_contrast_ratio",
                    "keyboard_navigation"
                ]
            ),
            VisualizationConfig(
                type=VisualizationType.MAP,
                color_scheme=ColorScheme.DIVERGING,
                interactive=True,
                data_format=DataFormat.GEOJSON,
                accessibility_features=[
                    "alt_text",
                    "aria_labels",
                    "color_contrast_ratio",
                    "keyboard_navigation"
                ]
            )
        ],
        dataset_metrics=DatasetMetrics(
            rows=10000,
            columns=15,
            size_bytes=1024000,
            last_updated=datetime.now(),
            update_frequency=UpdateFrequency.DAILY,
            completeness_score=0.98
        )
    )

@pytest.fixture
def visualization_template(visualization_metadata):
    """Create data visualization template."""
    return DataVisualizationTemplate(
        name="test_data_visualization",
        format=DocumentFormat.PDF,
        metadata=visualization_metadata
    )

def test_visualization_template_initialization(visualization_template, visualization_metadata):
    """Test data visualization template initialization."""
    assert visualization_template.name == "test_data_visualization"
    assert visualization_template.format == DocumentFormat.PDF
    assert visualization_template.metadata == visualization_metadata

def test_visualization_sections(visualization_template):
    """Test data visualization sections."""
    sections = visualization_template.get_ordered_sections()
    required_sections = {
        "data_overview",
        "charts_and_graphs",
        "statistical_analysis",
        "interpretation_guide",
        "accessibility_notes"
    }
    
    section_names = {section.name for section in sections}
    assert required_sections.issubset(section_names)
    assert all(section.required for section in sections if section.name in required_sections)

def test_visualization_config_validation():
    """Test visualization configuration validation."""
    # Test missing chart type for chart visualization
    with pytest.raises(ValidationError):
        VisualizationConfig(
            type=VisualizationType.CHART,
            color_scheme=ColorScheme.SEQUENTIAL,
            interactive=True,
            data_format=DataFormat.JSON
        )
    
    # Test valid map configuration without chart type
    config = VisualizationConfig(
        type=VisualizationType.MAP,
        color_scheme=ColorScheme.DIVERGING,
        interactive=True,
        data_format=DataFormat.JSON
    )
    assert config.chart_type is None

def test_visualization_validation(visualization_template):
    """Test visualization content validation."""
    valid_viz = {
        "data": [1, 2, 3],
        "type": "bar",
        "title": "Test Chart",
        "description": "Test description",
        "alt_text": "Alternative text"
    }
    assert visualization_template.validate_visualization(
        visualization_template.metadata.visualizations[0],
        valid_viz
    )
    
    invalid_viz = {
        "data": [1, 2, 3]  # Missing required fields
    }
    assert not visualization_template.validate_visualization(
        visualization_template.metadata.visualizations[0],
        invalid_viz
    )

def test_accessibility_validation(visualization_template):
    """Test accessibility validation."""
    valid_content = {
        "accessibility_features": [
            "alt_text",
            "aria_labels",
            "color_contrast_ratio",
            "keyboard_navigation"
        ]
    }
    assert visualization_template.validate_accessibility(valid_content)
    
    invalid_content = {
        "accessibility_features": [
            "alt_text"  # Missing required features
        ]
    }
    assert not visualization_template.validate_accessibility(invalid_content)

@pytest.mark.asyncio
async def test_visualization_markdown_formatting(visualization_template):
    """Test data visualization Markdown format output."""
    visualization_template.format = DocumentFormat.MARKDOWN
    """Test content validation during formatting."""
    invalid_content = {
        "performance_metrics": {
            "response_time_ms": -100.0  # Invalid negative value
        }
    }
    
    with pytest.raises(ValueError):
        await technical_template.format_content(invalid_content)

def test_template_integration():
    """Test template integration with DocumentInterface protocol."""
    from airesearch.interfaces.document_interface import DocumentInterface
    
    class TestInterface(DocumentInterface):
        async def format_research_results(
            self,
            results: Dict[str, Any],
            template: Any
        ) -> str:
            return "Formatted results"
        
        async def generate_document(
            self,
            content: str,
            template: Any
        ) -> bytes:
            return b"Generated document"
        
        async def validate_template(self, template: Any) -> bool:
            return True
    
    interface = TestInterface()
    assert hasattr(interface, 'format_research_results')
    assert hasattr(interface, 'generate_document')
    assert hasattr(interface, 'validate_template')

