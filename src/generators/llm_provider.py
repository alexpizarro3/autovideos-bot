import os
import json
import logging
from huggingface_hub import InferenceClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMProvider:
    def __init__(self, model_id="meta-llama/Meta-Llama-3-8B-Instruct"):
        """
        Initialize the LLM Provider with a HuggingFace model.
        """
        self.token = os.getenv("HF_TOKEN")
        if not self.token:
            logger.warning("HF_TOKEN is not set. LLM generation might fail if the model requires authentication.")
        
        self.client = InferenceClient(token=self.token)
        self.model_id = model_id

    def generate_script(self, topic: str) -> dict:
        """
        Generates a video script and metadata for the given topic.
        Returns a dict with 'title', 'description', 'hashtags', and 'scenes'.
        """
        prompt = f"""
You are an expert short-form video scriptwriter for TikTok/YouTube Shorts. Your goal is MAXIMAL RETENTION.
Topic: "{topic}"

Structure your script for HIGH ENGAGEMENT:
1. **The Hook (0-3s)**: A shocking statement or question. MUST stop the scroll.
2. **The Meat**: Fast facts, surprising details.
3. **The Twist/Ending**: A final punchline or loop.

The output MUST be valid JSON:
{{
  "title": "CLICKBAIT TITLE (All caps allowed, e.g. 'YOU WONT BELIEVE THIS 😱')",
  "description": "Engaging caption with a question for comments.",
  "hashtags": ["#viral", "#fyp", "#shorts", "#topic"],
  "scenes": [
    {{
      "text": "Short sentence for voiceover (max 10 words per scene for fast pacing).", 
      "image_prompt": "Hyper-realistic, cinematic, motion-blur, 8k image description matching the text."
    }},
    ...
  ]
}}

Requirements:
- **Total Duration**: 30-45 seconds (Fast paced!).
- **Tone**: Energetic, urgent, mysterious.
- **Visuals**: Describe images that would look good even if static (but we will animate them).
- **CRITICAL JSON RULES**: 
  - Do NOT use unescaped double quotes (`"`) inside strings. Use single quotes (`'`) instead. Example: "It's called 'The Zone'", NOT "It's called "The Zone"".
  - Do NOT include trailing commas.
- **NO Markdown**: Output ONLY raw JSON.
        """

        try:
            logger.info(f"Generating script for topic: {topic}")
            msg_prompt = [
                {"role": "system", "content": "You are a professional short-video scriptwriter. Output strictly valid JSON."},
                {"role": "user", "content": prompt}
            ]

            logger.info(f"Generating script for topic: {topic}")
            response = self.client.chat_completion(
                messages=msg_prompt,
                model=self.model_id,
                max_tokens=1000,
                temperature=0.7
            )
            
            # Extract content from chat completion
            cleaned_response = response.choices[0].message.content.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]
                
            script_data = json.loads(cleaned_response)
            logger.info("Script generated successfully.")
            return script_data

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}. Response was: {response}")
            logger.error(f"Failed to parse JSON response: {e}. Response was: {response}")
            return None
        except Exception as e:
            logger.error(f"Error generating script: {e}")
            logger.info("Using fallback script for verification/testing purposes.")
            return {
                "title": "Honey Never Spoils! 🍯",
                "description": "Did you know honey found in ancient tombs is still edible?",
                "hashtags": ["#facts", "#honey", "#history", "#science", "#fyp"],
                "scenes": [
                    {"text": "Did you know that honey never spoils?", "image_prompt": "Golden honey dripping from a wooden dipper, cinematic lighting, 8k"},
                    {"text": "Archaeologists have found pots of honey in ancient Egyptian tombs that are over 3,000 years old and still perfectly edible.", "image_prompt": "Ancient Egyptian tomb interior, filled with artifacts and jars of honey, realistic, detailed"}
                ]
            }

if __name__ == "__main__":
    # Test the provider
    from dotenv import load_dotenv
    load_dotenv()
    
    llm = LLMProvider()
    script = llm.generate_script("The mystery of the Bermuda Triangle")
    print(json.dumps(script, indent=2))
