from typing import List
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from app.adapters.ai.llm.prompts import (
    REPORT_SUMMARIZATION_PROMPT,
    REPORT_CATEGORIZATION_PROMPT,
    PREDICTIVE_VALIDATION_PROMPT,
)
from app.domain.schema.categorize import CategoryNode

DEFAULT_MODEL = "llama2-uncensored"


# Structured output schemas for LLM responses
class CategoryResponse(BaseModel):
    """Structured response for report categorization."""
    category_ids: List[int] = Field(description="List of category IDs that match the report")


class ValidationResponse(BaseModel):
    """Structured response for report validation."""
    summary: str = Field(description="Comprehensive assessment explaining why the report is true or false")
    requires_human_review: bool = Field(description="Whether this report needs human review")
    confidence_score: float = Field(ge=0, le=100, description="AI confidence in the validity assessment (0-100)")
    final_validity_status: str = Field(description="AI's determination: valid, suspicious, invalid, or requires_review")
    reasons: List[str] = Field(description="List of reasons explaining why the report is valid or invalid")
    supporting_inferences: List[str] = Field(default_factory=list, description="Inferences that support the validity decision")


class OllamaLLMEngine:
    def __init__(self, model: str = DEFAULT_MODEL):
        self.model_name = model
        self.model = ChatOllama(model=self.model_name)
        self.prompt_template = ChatPromptTemplate.from_template(REPORT_SUMMARIZATION_PROMPT)

    async def generate_report_summary(self, content: str) -> str:
        """
        Generate a structured title and description for the given report content.

        Args:
            content (str): The unstructured report content from the user.

        Returns:
            str: Output as plain text, including "Title:" and "Description:" fields.
        """
        prompt = self.prompt_template.format(content=content)
        response = await self.model.ainvoke(prompt)
        return response.content.strip()

    async def categorize_report(self, title: str, description: str, categories: List[CategoryNode]) -> List[int]:
        """
        Categorize a report based on its title and description.

        Args:
            title (str): The report title
            description (str): The report description
            categories (List[CategoryNode]): List of available category nodes

        Returns:
            List[int]: List of category IDs that match the report
        """
        categories_text = self._format_categories_for_prompt(categories)

        prompt_template = ChatPromptTemplate.from_template(REPORT_CATEGORIZATION_PROMPT)
        prompt = prompt_template.format(
            title=title,
            description=description,
            categories=categories_text
        )

        # Use structured output for categorization
        structured_model = self.model.with_structured_output(CategoryResponse)
        response = await structured_model.ainvoke(prompt)

        return response.category_ids

    async def validate_report(
        self,
        title: str,
        summary: str,
        categories: List[str],
        deterministic_data: dict,
    ) -> ValidationResponse:
        """
        Perform predictive validation on a report using AI.

        Args:
            title (str): Report title
            summary (str): Report summary
            categories (List[str]): List of category slugs
            deterministic_data (dict): Deterministic validation data

        Returns:
            ValidationResponse: Structured validation result
        """
        # Format issues and inferences for prompt
        issues_text = self._format_validation_items(
            deterministic_data.get("issues", []), "issue"
        )
        inferences_text = self._format_validation_items(
            deterministic_data.get("inferences", []), "inference"
        )

        metadata = deterministic_data.get("metadata", {})
        categories_str = ", ".join(categories) if categories else "None"

        # Calculate rejection rate
        reporter_history_count = metadata.get("reporter_history_count", 0)
        rejected_reports_count = metadata.get("rejected_reports_count", 0)
        rejection_rate = (
            round((rejected_reports_count / reporter_history_count) * 100, 2)
            if reporter_history_count > 0
            else 0.0
        )

        prompt_template = ChatPromptTemplate.from_template(PREDICTIVE_VALIDATION_PROMPT)
        prompt = prompt_template.format(
            title=title,
            summary=summary,
            categories=categories_str,
            trust_score=deterministic_data.get("trust_score", 0),
            issues_count=deterministic_data.get("issues_count", 0),
            inferences_count=deterministic_data.get("inferences_count", 0),
            reporter_history_count=reporter_history_count,
            rejected_reports_count=rejected_reports_count,
            rejection_rate=rejection_rate,
            device_fingerprint_match=metadata.get("device_fingerprint_match", False),
            average_evidence_distance=metadata.get("average_evidence_distance", 0.0),
            report_frequency_score=metadata.get("report_frequency_score", 0),
            reporter_join_date=metadata.get("reporter_join_date", "Unknown"),
            issues=issues_text,
            inferences=inferences_text,
        )

        # Use structured output for validation
        structured_model = self.model.with_structured_output(ValidationResponse)
        response = await structured_model.ainvoke(prompt)

        return response

    ###### HELPERS ########

    def _format_categories_for_prompt(self, categories: List[CategoryNode], level: int = 0) -> str:
        """
        Format category nodes into a readable string for the prompt.

        Args:
            categories (List[CategoryNode]): List of category nodes
            level (int): Current nesting level for indentation

        Returns:
            str: Formatted categories string
        """
        lines = []
        indent = "  " * level

        for category in categories:
            lines.append(f"{indent}ID: {category.id}")
            lines.append(f"{indent}Name: {category.name}")
            lines.append(f"{indent}Slug: {category.slug}")
            lines.append(f"{indent}Description: {category.description}")
            lines.append("")

        return "\n".join(lines)

    def parse_ollama_response(self, response: str) -> tuple[str, str]:
        """
        Parse Ollama's response in the format:
        Title: <title>
        Description: <description>
        """
        title = "Untitled Report"
        description = "No description available"

        lines = response.split("\n")
        for i, line in enumerate(lines):
            line = line.strip()
            if line.lower().startswith("title:"):
                title = line[6:].strip()
            elif line.lower().startswith("description:"):
                description = line[12:].strip()
                if i + 1 < len(lines):
                    remaining = "\n".join(lines[i + 1:]).strip()
                    if remaining:
                        description = (
                            description + "\n" + remaining if description else remaining
                        )
                break

        return title, description

    def _format_validation_items(self, items: List[dict], item_type: str) -> str:
        """
        Format validation issues or inferences for the prompt.

        Args:
            items (List[dict]): List of issue or inference dictionaries
            item_type (str): "issue" or "inference"

        Returns:
            str: Formatted string representation
        """
        if not items:
            return f"No {item_type}s found."

        critical_issue_fields = {
            "location",
            "app_version",
            "device_information",
            "incident_datetime",
            "data_completeness",
            "report_frequency",
            "evidence_count",
        }

        high_suspicion_inferences = {
            "anonymous_report",
            "reporter_history",
            "device_fingerprint",
            "duplicate_report",
            "timestamp_anomaly",
        }

        lines = []
        for i, item in enumerate(items, 1):
            if item_type == "issue":
                field = item.get("field", "Unknown")
                message = item.get("message", "")
                level = item.get("level", "info")

                is_critical = field in critical_issue_fields or level == "error"
                marker = "⚠️ CRITICAL " if is_critical else ""

                lines.append(f"{i}. {marker}[{level.upper()}] {field}: {message}")
            elif item_type == "inference":
                category = item.get("category", "Unknown")
                observation = item.get("observation", "")
                level = item.get("level", "info")

                is_suspicious = category in high_suspicion_inferences
                marker = "🔴 HIGH SUSPICION " if is_suspicious else ""

                lines.append(f"{i}. {marker}[{level.upper()}] {category}: {observation}")

        return "\n".join(lines)
