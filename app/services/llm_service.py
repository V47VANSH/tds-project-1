from openai import OpenAI
from app.config import settings
import logging
import json

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self):
        self.client = OpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url
        )
        self.model = settings.llm_model
    
    async def generate_app(self, brief: str, attachments: dict, round_num: int) -> dict:
        """
        Generate app files based on the brief using LLM
        """
        logger.info(f"Generating app for round {round_num}")
        
        prompt = self._create_prompt(brief, attachments, round_num)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert web developer. Generate complete, working HTML/CSS/JS applications based on user requirements. Return your response as a JSON object with file paths as keys and file contents as values."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.7,
            )
            
            content = response.choices[0].message.content
            files = json.loads(content)
            
            # Ensure we have at least index.html
            if "index.html" not in files:
                raise ValueError("Generated files must include index.html")
            
            return files
            
        except Exception as e:
            logger.error(f"Error generating app: {e}")
            raise
    
    def _create_prompt(self, brief: str, attachments: dict, round_num: int) -> str:
        """
        Create the prompt for the LLM
        """
        if round_num == 1:
            prompt = f"""
Create a complete, minimal working web application based on this brief:

{brief}

Requirements:
- Generate a single-page application with HTML, CSS, and JavaScript
- The app must be fully functional and self-contained
- Include proper styling and responsive design
- Add comments explaining key functionality
- Make it visually appealing and user-friendly

Attachments (if any):
{json.dumps(attachments, indent=2)}

Return a JSON object where keys are file paths (e.g., "index.html", "styles.css", "script.js") and values are the complete file contents.
"""
        else:
            prompt = f"""
Update the existing web application with these new requirements:

{brief}

Previous attachments (if any):
{json.dumps(attachments, indent=2)}

Requirements:
- Modify or extend the existing application
- Maintain all previous functionality unless explicitly asked to change it
- Ensure the app remains fully functional
- Update styling if needed
- Add comments for new functionality

Return a JSON object where keys are file paths and values are the complete file contents. Include ALL files (modified and unmodified).
"""
        
        return prompt
    
    async def generate_readme(self, task_name: str, brief: str, round_num: int) -> str:
        """
        Generate a comprehensive README.md
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a technical writer. Create clear, comprehensive README files for web applications."
                    },
                    {
                        "role": "user",
                        "content": f"""
Create a README.md for this project:

Project Name: {task_name}
Brief: {brief}
Round: {round_num}

Include:
- Project title and brief description
- Features list
- Setup instructions (if any)
- Usage guide
- Technical details
- License (MIT)

Make it clear, professional, and well-formatted in Markdown.
"""
                    }
                ],
                temperature=0.7,
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating README: {e}")
            # Fallback README
            return f"""# {task_name}

## Description
{brief}

## Features
- Minimal working application
- Responsive design
- Modern UI

## Setup
1. Clone this repository
2. Open `index.html` in a web browser
3. No build steps required

## Usage
Open the application in your web browser and follow the on-screen instructions.

## License
MIT License
"""