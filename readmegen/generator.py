"""README generator — builds a prompt from scan results and calls an LLM."""

from __future__ import annotations

import os
import sys
from typing import Optional

from readmegen.scanner import ScanResult


# ---------------------------------------------------------------------------
# Prompt templates
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
You are an expert technical writer who creates outstanding README files for \
open-source projects. You write clear, concise, developer-friendly documentation.

Rules:
- Use Markdown formatting (or reStructuredText if requested).
- Write in second person ("you") for instructions.
- Be specific: use actual package names, commands, file paths from the scan.
- Include real code snippets when useful.
- Keep it professional but approachable.
- Do NOT hallucinate features or files that don't exist in the scan data.
"""

USER_PROMPT_TEMPLATE = """\
Generate a comprehensive README for the following project.

{context}

--- Requirements ---
Output Format: {format}
Style: {style}
Include Badges: {badges}
Include Table of Contents: {toc}
Include API Documentation: {api_docs}
Include Contributing Section: {contributing}
Include License Section: {license_section}

Generate ONLY the README content — no explanations or meta-commentary.
"""

RST_ADDENDUM = """
Use reStructuredText (.rst) formatting instead of Markdown.
Use proper rst headings (===, ---, ~~~), directives, and roles.
"""

STYLE_HINTS = {
    "professional": "Use a professional, polished tone suitable for enterprise projects.",
    "casual": "Use a friendly, casual tone with occasional humor. Still technically accurate.",
    "minimal": "Be extremely concise. Only essential sections. No fluff.",
}


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------


class ReadmeGenerator:
    """Generate README content using OpenAI or Anthropic APIs."""

    def __init__(self, provider: Optional[str] = None, model: Optional[str] = None):
        self.provider = provider or self._detect_provider()
        self.model = model or self._default_model()

    def generate(
        self,
        scan_result: ScanResult,
        output_format: str = "md",
        include_badges: bool = True,
        include_toc: bool = True,
        include_api_docs: bool = True,
        include_contributing: bool = True,
        include_license: bool = True,
        style: str = "professional",
    ) -> str:
        context = scan_result.to_prompt_context()

        user_prompt = USER_PROMPT_TEMPLATE.format(
            context=context,
            format="Markdown" if output_format == "md" else "reStructuredText",
            style=STYLE_HINTS.get(style, STYLE_HINTS["professional"]),
            badges=include_badges,
            toc=include_toc,
            api_docs=include_api_docs,
            contributing=include_contributing,
            license_section=include_license,
        )

        if output_format == "rst":
            user_prompt += RST_ADDENDUM

        if self.provider == "openai":
            return self._call_openai(user_prompt)
        elif self.provider == "anthropic":
            return self._call_anthropic(user_prompt)
        elif self.provider == "gemini":
            return self._call_gemini(user_prompt)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")

    # --- Provider calls ---
    def _call_gemini(self, user_prompt: str) -> str:
            try:
                from google import genai
                from google.genai import types
                import os
            except ImportError:
                print("Error: google-generativeai package not installed. Run: pip install google-generativeai", file=sys.stderr)
                sys.exit(1)

            # Configure the API key from environment variables
            api_key = os.environ.get("GOOGLE_API_KEY")
            if not api_key:
                print("Error: GOOGLE_API_KEY environment variable not set.", file=sys.stderr)
                sys.exit(1)
                
            client = genai.Client(api_key=api_key)
            # Initialize the model with the system prompt
            response = client.models.generate_content(
                model=self.model,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    max_output_tokens= 4096,
                    top_k= 2,
                    top_p= 0.5,
                    temperature= 0.5,
                ),
            )
            return response.text if response.text else ""

    def _call_openai(self, user_prompt: str) -> str:
        try:
            from openai import OpenAI
        except ImportError:
            print("Error: openai package not installed. Run: pip install openai", file=sys.stderr)
            sys.exit(1)

        client = OpenAI()  # uses OPENAI_API_KEY env var
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=4096,
            temperature=0.4,
        )
        return response.choices[0].message.content or ""

    def _call_anthropic(self, user_prompt: str) -> str:
        try:
            from anthropic import Anthropic
        except ImportError:
            print("Error: anthropic package not installed. Run: pip install anthropic", file=sys.stderr)
            sys.exit(1)

        client = Anthropic()  # uses ANTHROPIC_API_KEY env var
        response = client.messages.create(
            model=self.model,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
            max_tokens=4096,
            temperature=0.4,
        )
        return response.content[0].text

    # --- Helpers ---

    def _detect_provider(self) -> str:
        if os.environ.get("ANTHROPIC_API_KEY"):
            return "anthropic"
        if os.environ.get("OPENAI_API_KEY"):
            return "openai"
        if os.environ.get("GOOGLE_API_KEY"):
            return "gemini"
        print(
            "Error: Set OPENAI_API_KEY or ANTHROPIC_API_KEY or GOOGLE_API_KEY environment variable.",
            file=sys.stderr,
        )
        sys.exit(1)

    def _default_model(self) -> str:
        if self.provider == "anthropic":
            return "claude-sonnet-4-6"
        elif self.provider == "gemini":
            return "gemini-2.5-flash"
        return "gpt-4o"
