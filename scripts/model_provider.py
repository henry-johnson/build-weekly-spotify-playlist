"""Abstract AI provider interface for pluggable language models and image generation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class AIProvider(ABC):
    """Abstract base class for AI service providers."""

    @abstractmethod
    def generate_text(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str,
        temperature: float = 0.7,
    ) -> dict[str, Any]:
        """Generate text using the provider's text generation API.

        Args:
            system_prompt: System context for the model.
            user_prompt: User-provided input prompt.
            model: Model identifier (provider-specific).
            temperature: Sampling temperature (0.0 to 2.0).

        Returns:
            Response dict with at least a "choices" key containing parsed response.

        Raises:
            Exception: On API errors, network failures, or invalid responses.
        """
        ...

    @abstractmethod
    def generate_image(
        self,
        prompt: str,
        model: str,
        size: str = "1024",
        quality: str = "standard",
    ) -> dict[str, Any]:
        """Generate an image using the provider's image generation API.

        Args:
            prompt: Natural language description of the image to generate.
            model: Model identifier (provider-specific).
            size: Image size (e.g., "1024", "512").
            quality: Quality level ("standard" or "hd").

        Returns:
            Response dict with at least a "data" key containing image data.
            Data should include "b64_json" or "url" fields.

        Raises:
            Exception: On API errors, network failures, or invalid responses.
        """
        ...
