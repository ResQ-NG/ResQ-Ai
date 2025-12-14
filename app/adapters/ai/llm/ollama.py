from typing import List
import json
from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate


from app.adapters.ai.llm.prompts import REPORT_SUMMARIZATION_PROMPT, REPORT_CATEGORIZATION_PROMPT
from app.domain.schema.categorize import CategoryNode

DEFAULT_MODEL = "llama2-uncensored"



class OllamaLLMEngine:
    def __init__(self, model: str = DEFAULT_MODEL):
        self.model_name = model
        self.model = OllamaLLM(model=self.model_name)
        self.prompt_template = ChatPromptTemplate.from_template(REPORT_SUMMARIZATION_PROMPT)

    async def generate_report_summary(self, content: str) -> str:
        """
        Generate a structured title and description for the given report content.

        Args:
            content (str): The unstructured report content from the user.

        Returns:
            str: Output as plain text, including "Title:" and "Description:" fields, not as JSON.
        """
        prompt = self.prompt_template.format(content=content)
        response = await self.model.ainvoke(prompt)
        return response.strip()

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
        # Format categories for the prompt
        categories_text = self._format_categories_for_prompt(categories)

        # Create prompt template and format it
        prompt_template = ChatPromptTemplate.from_template(REPORT_CATEGORIZATION_PROMPT)
        prompt = prompt_template.format(
            title=title,
            description=description,
            categories=categories_text
        )

        # Get response from model
        response = await self.model.ainvoke(prompt)

        # Parse the JSON response to get category IDs
        category_ids = self._parse_category_response(response.strip())

        return category_ids




    ###### HELPERS ########

    def _format_categories_for_prompt(self, categories: List[CategoryNode], level: int = 0) -> str:
        """
        Format category nodes into a readable string for the prompt.
        Handles nested categories recursively.

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

            lines.append("")  # Empty line between categories

        return "\n".join(lines)

    def _parse_category_response(self, response: str) -> List[int]:
        """
        Parse the AI's response to extract category IDs.
        Expects a JSON array like [1, 3, 7]

        Args:
            response (str): The raw response from the model

        Returns:
            List[int]: List of category IDs
        """
        try:
            # Try to find JSON array in the response
            # Sometimes the model might add extra text, so we extract the array
            start_idx = response.find('[')
            end_idx = response.rfind(']')

            if start_idx != -1 and end_idx != -1:
                json_str = response[start_idx:end_idx + 1]
                category_ids = json.loads(json_str)

                # Ensure all items are integers
                return [int(cat_id) for cat_id in category_ids]
            else:
                # No array found, return empty list
                return []
        except (json.JSONDecodeError, ValueError) as e:
            # If parsing fails, return empty list
            print(f"Error parsing category response: {e}")
            return []

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
                # Description might span multiple lines, so capture everything after "Description:"
                description = line[12:].strip()
                # Join remaining lines as part of description
                if i + 1 < len(lines):
                    remaining = "\n".join(lines[i + 1 :]).strip()
                    if remaining:
                        description = (
                            description + "\n" + remaining if description else remaining
                        )
                break

        return title, description
