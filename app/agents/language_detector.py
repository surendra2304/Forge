"""
Language and Framework Classifier and AI-Universe Prompt Router for Project FORGE.
"""

from enum import Enum
import re
from typing import List, Optional, Tuple


class TargetLanguage(str, Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    FULLSTACK = "fullstack"


class TargetFramework(str, Enum):
    FASTAPI = "fastapi"
    FLASK = "flask"
    EXPRESS = "express"
    REACT = "react"
    NEXTJS = "nextjs"
    VUE = "vue"
    CLI = "cli"
    SCRIPT = "script"
    STATIC_WEB = "static_web"


class LanguageDetector:
    """Classifies software requirements and goals into target language and framework."""

    @classmethod
    def detect(cls, goal: str, requirements: Optional[List[str]] = None) -> Tuple[TargetLanguage, TargetFramework]:
        combined_text = f"{goal} {' '.join(requirements or [])}".lower()

        # Check for full-stack composite indicators
        is_fullstack = ("frontend" in combined_text and "backend" in combined_text) or \
                       ("react" in combined_text and "fastapi" in combined_text) or \
                       ("next.js" in combined_text and "express" in combined_text) or \
                       ("full stack" in combined_text or "fullstack" in combined_text)
        if is_fullstack:
            return TargetLanguage.FULLSTACK, TargetFramework.REACT

        # Framework detection
        if "next.js" in combined_text or "nextjs" in combined_text or "next js" in combined_text:
            return TargetLanguage.TYPESCRIPT, TargetFramework.NEXTJS

        if "react" in combined_text:
            if "typescript" in combined_text or "ts" in combined_text:
                return TargetLanguage.TYPESCRIPT, TargetFramework.REACT
            return TargetLanguage.JAVASCRIPT, TargetFramework.REACT

        if "vue" in combined_text or "vue.js" in combined_text or "vuejs" in combined_text:
            return TargetLanguage.JAVASCRIPT, TargetFramework.VUE

        if "express" in combined_text or "express.js" in combined_text or "node.js" in combined_text or "nodejs" in combined_text:
            if "typescript" in combined_text:
                return TargetLanguage.TYPESCRIPT, TargetFramework.EXPRESS
            return TargetLanguage.JAVASCRIPT, TargetFramework.EXPRESS

        if "typescript" in combined_text or ".ts" in combined_text:
            return TargetLanguage.TYPESCRIPT, TargetFramework.EXPRESS

        if "flask" in combined_text:
            return TargetLanguage.PYTHON, TargetFramework.FLASK

        if "fastapi" in combined_text or "api" in combined_text or "rest" in combined_text:
            return TargetLanguage.PYTHON, TargetFramework.FASTAPI

        if "cli" in combined_text or "command line" in combined_text or "argparse" in combined_text:
            return TargetLanguage.PYTHON, TargetFramework.CLI

        if "html" in combined_text or "landing page" in combined_text or "portfolio" in combined_text or "website" in combined_text:
            return TargetLanguage.PYTHON, TargetFramework.STATIC_WEB

        # Default fallback
        return TargetLanguage.PYTHON, TargetFramework.SCRIPT


class LanguagePromptRouter:
    """Generates language-specific prompts for AI-Universe reasoning personas."""

    @classmethod
    def format_persona_prompt(
        cls,
        language: TargetLanguage,
        framework: TargetFramework,
        filename: str,
        purpose: str,
    ) -> str:
        """Construct specialized prompt with framework idioms and conventions."""
        lang_name = language.value.capitalize()
        framework_name = framework.value.capitalize()

        return (
            f"Write complete, production-grade {lang_name} code for `{filename}` "
            f"following modern {framework_name} best practices and design patterns.\n"
            f"Purpose: {purpose}\n"
            f"Language: {lang_name}\n"
            f"Framework: {framework_name}\n"
            f"Ensure strict syntax adherence, robust error handling, type definitions, and modular structure."
        )
