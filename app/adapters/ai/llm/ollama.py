from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate

from app.adapters.ai.llm.prompts import REPORT_SUMMARIZATION_PROMPT

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

    async def categorize_report(self, title: str, description: str):
        #TODO: this is what i need to iron out properly. let me see that we rank this cleanly and push it to our stream. 
        pass




    ###### HELPERS ########

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
