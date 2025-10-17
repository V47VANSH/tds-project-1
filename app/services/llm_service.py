from openai import OpenAI
from app.config import settings
import logging
import json
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self):
        self.client = OpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url
        )
        self.model = settings.llm_model
    
    async def generate_app(self, brief: str, attachments: dict, round_num: int, 
                          previous_rounds: Optional[List[dict]] = None,
                          repo_files: Optional[Dict[str, str]] = None,
                          checks: Optional[List[str]] = None) -> dict:
        """
        Generate app files based on the brief using LLM
        """
        logger.info(f"Generating app for round {round_num}")
        
        prompt = self._create_prompt(brief, attachments, round_num, previous_rounds, repo_files, checks)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert web developer. Generate complete, working HTML/CSS/JS applications that EXACTLY meet user requirements. Every specification must be implemented precisely. All checks must pass. Return your response as a JSON object with file paths as keys and file contents as values."
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
    
    def _create_prompt(self, brief: str, attachments: dict, round_num: int,
                      previous_rounds: Optional[List[dict]] = None,
                      repo_files: Optional[Dict[str, str]] = None,
                      checks: Optional[List[str]] = None) -> str:
        """
        Create the prompt for the LLM
        """
        # Parse attachments to make them more accessible
        attachment_info = ""
        if attachments:
            attachment_info = "\n=== ATTACHMENTS ===\n"
            attachment_info += "The following attachments are provided as data URIs. Use them in your application:\n\n"
            print({json.dumps(attachments, indent=2)})
            attachment_info += f"{json.dumps(attachments, indent=2)}\n"

            
            # for filename, data_uri in attachments.items():
            #     attachment_info += f"File: {filename}\n"
            #     if isinstance(data_uri, str) and data_uri.startswith("data:"):
            #         # Extract the MIME type
            #         mime_type = data_uri.split(';')[0].replace('data:', '')
            #         attachment_info += f"Format: {mime_type}\n"
            #         attachment_info += "Instructions: Decode the base64 content as needed for your application.\n"
            #         attachment_info += "Example: `const content = atob(dataURI.split(',')[1]);`\n"
            #     else:
            #         attachment_info += f"Content: {data_uri}\n"

            #     attachment_info += "\n"

        # Format checks prominently
        checks_info = ""
        if checks:
            checks_info = "\n=== ⚠️ MANDATORY CHECKS - MUST ALL PASS ⚠️ ===\n"
            checks_info += "Your application WILL BE TESTED against these exact checks:\n\n"
            for i, check in enumerate(checks, 1):
                checks_info += f"{i}. {check}\n"
            checks_info += "\nIMPORTANT: Every single check must pass EXACTLY. Pay attention to:\n"
            checks_info += "- Exact element IDs\n"
            checks_info += "- Exact text content and values\n"
            checks_info += "- Exact page titles\n"
            checks_info += "- Correct calculations from data\n"
            checks_info += "- Case sensitivity and formatting\n\n"
        
        if round_num == 1:
            prompt = f"""
Create a complete, fully functional web application that STRICTLY meets ALL requirements.

=== USER BRIEF ===
{brief}

{checks_info}

{attachment_info}

=== CRITICAL REQUIREMENTS ===
You MUST ensure the application meets these exact specifications. Each requirement will be verified:

1. The application must be fully functional and work correctly
2. All HTML elements with specific IDs must exist exactly as specified
3. All text content must match exactly (including numbers, formatting, case)
4. All page titles, headings, and labels must match exactly as specified
5. If attachments are provided, you MUST handle them correctly:
   - For CSV files: Use JavaScript to decode the base64 content and parse it as CSV
   - For images: Use the data URI directly in your HTML as the image source
   - For JSON files: Decode the base64 content and parse it as JSON
   - Always follow the specific requirements in the brief for processing the data

6. All calculations must be accurate to the exact decimal places shown
7. The application must be self-contained and work immediately when opened

=== ATTACHMENT HANDLING ===
Data URIs are in the format: data:[<MIME type>][;base64],<data>
Decode base64 content as needed for each file type.

=== TECHNICAL REQUIREMENTS ===
- Generate a single-page application with HTML, CSS, and JavaScript
- Include all necessary code inline (no external dependencies)
- If processing data files (CSV, JSON, etc.), include the logic to parse and use them
- For images, use data URIs directly in your HTML/CSS
- Use proper error handling
- Add clear comments explaining the logic
- Make it visually clean and professional
- Ensure responsive design

=== FILE STRUCTURE ===
Return a JSON object where:
- Keys are file paths (e.g., "index.html", "styles.css", "script.js")
- Values are the complete file contents
- You MUST include "index.html" at minimum

IMPORTANT: Read the brief and checks carefully. Implement EXACTLY what is requested. Every detail matters and will be tested.
"""
        else:
            prompt = f"""
Update the existing web application to meet these NEW requirements while maintaining previous functionality.

=== NEW REQUIREMENTS (CURRENT ROUND) ===
{brief}

{checks_info}

{attachment_info}

"""
            # Add previous rounds data
            if previous_rounds:
                prompt += "\n=== PREVIOUS ROUNDS HISTORY ===\n"
                for prev_round in previous_rounds:
                    prompt += f"\n--- Round {prev_round['round']} ---\n"
                    prompt += f"Brief: {prev_round['brief']}\n"
                    if prev_round.get('checks'):
                        prompt += f"Required Checks (must still pass):\n"
                        for check in prev_round['checks']:
                            prompt += f"  ✓ {check}\n"
                    if prev_round.get('attachments'):
                        prompt += f"Attachments: {list(prev_round['attachments'].keys())}\n"
                prompt += "\n"
            
            # Add current repo code
            if repo_files:
                prompt += "\n=== CURRENT REPOSITORY CODE ===\n"
                for file_path, content in repo_files.items():
                    # Limit content length for very large files
                    display_content = content if len(content) < 5000 else content[:5000] + "\n... (truncated)"
                    prompt += f"\nFile: {file_path}\n```\n{display_content}\n```\n"
                prompt += "\n"
            
            prompt += f"""
=== ATTACHMENT HANDLING ===
Data URIs are in the format: data:[<MIME type>][;base64],<data>
Decode the base64 content as needed for each file type.


=== CRITICAL REQUIREMENTS ===
1. Implement ALL new requirements from the current brief
2. Maintain ALL functionality from previous rounds
3. Ensure all previous checks still pass
4. Verify new checks will pass EXACTLY
5. Update or add files as needed
6. Keep the application fully functional
7. Properly decode and handle any attachments

=== TECHNICAL REQUIREMENTS ===
- Modify or extend existing files as needed
- Ensure backward compatibility unless explicitly told to change
- Add proper error handling for new features
- Update comments to reflect changes
- Maintain clean, professional styling

=== OUTPUT FORMAT ===
Return a JSON object with ALL files (both modified and unmodified):
- Keys: file paths
- Values: complete file contents
- Include ALL necessary files for the app to work

IMPORTANT: Every requirement and check must be met exactly. Read carefully and implement precisely. All checks will be tested.
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
            return f"# {task_name}\n\n{brief}\n\n---\n\nRound: {round_num}\n\nFeatures:\n- TODO: List features here\n\n## Setup Instructions\n- TODO: Provide setup instructions\n\n## Usage\n- TODO: Explain how to use the app\n\n## Technical Details\n- TODO: Add technical details\n\n## License\nMIT License"            # Fallback README            logger.error(f"Error generating README: {e}")            return f"""# {task_name}
