# -*- coding: utf-8 -*-
"""OpenAI-compatible HTTP client for Gamma.

This client implements a minimal subset of the OpenAI chat completion API using only
the Python standard library. It is deliberately lightweight and has no external
dependencies, making it safe to import in environments where the full OpenAI SDK
is unavailable.

The implementation focuses on correctness, secret safety, and testability.
"""

import json
import os
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any, List, Mapping, Optional, Union

from ..errors import UnsupportedOperationError


class BackendError(RuntimeError):
    """Raised when the HTTP request to the OpenAI‑compatible endpoint fails.

    The original exception is attached as ``__cause__`` for debugging purposes.
    """


class OpenAICompatibleClient:
    """Simple OpenAI‑compatible client.

    Parameters
    ----------
    url: str
        Base URL of the server (e.g. ``http://localhost:1234/v1``).
    api_key: str | None, default ``None``
        Direct API key value. If ``None`` and ``api_key_env`` is supplied the
        environment variable will be read.
    api_key_env: str | None, default ``None``
        Name of the environment variable that holds the API key.
    model: str | None, default ``None``
        Model identifier to include in every request.
    timeout: float, default ``120.0``
        Network timeout in seconds.
    transcript_dir: str | Path | bool | None, default ``None``
        If truthy, the client will optionally store request/response transcripts
        for debugging. The implementation currently records transcripts only
        when a ``Path`` is supplied; other truthy values are ignored to keep the
        client lightweight.
    """

    def __init__(
        self,
        url: str,
        api_key: Optional[str] = None,
        api_key_env: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 120.0,
        transcript_dir: Union[str, Path, bool, None] = None,
        response_dir: Union[str, Path, bool, None] = None,
    ) -> None:
        self.base_url = url.rstrip('/')
        # Resolve API key from env if needed
        if api_key is None and api_key_env:
            api_key = os.getenv(api_key_env)
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self._history: List[Mapping[str, Any]] = []
        self.transcript_path: Optional[Path] = None
        if isinstance(transcript_dir, (str, Path)):
            self.transcript_path = Path(transcript_dir)
            self.transcript_path.mkdir(parents=True, exist_ok=True)
        self._response_path: Optional[Path] = None
        if isinstance(response_dir, (str, Path)):
            self._response_path = Path(response_dir)
            self._response_path.mkdir(parents=True, exist_ok=True)

    # ---------------------------------------------------------------------
    # Helper utilities
    # ---------------------------------------------------------------------
    def _make_endpoint(self) -> str:
        """Return the full chat‑completion endpoint.

        If the base URL already ends with ``/v1`` the endpoint is
        ``<base>/chat/completions``; otherwise ``/v1/chat/completions`` is
        appended, ensuring exactly one slash between parts.
        """
        if self.base_url.endswith('/v1'):
            return f"{self.base_url}/chat/completions"
        # Normalise to avoid double slashes
        return f"{self.base_url}/v1/chat/completions"

    def _record_transcript(self, request: dict, response: dict) -> None:
        if self.transcript_path is None:
            return
        idx = len(self._history)
        path = self.transcript_path / f"transcript_{idx}.json"
        with path.open('w', encoding='utf-8') as fp:
            json.dump({"request": request, "response": response}, fp, indent=2)

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------
    def send(
        self,
        prompt: str,
        system: Optional[str] = None,
        messages: Optional[List[Mapping[str, Any]]] = None,
        temperature: float = 0.1,
        max_tokens: int = 1024,
        **kwargs: Any,
    ) -> Mapping[str, Any]:
        """Send a chat completion request.

        Parameters are translated into the OpenAI ``chat/completions`` payload.
        ``prompt`` is treated as a user message; ``system`` may be supplied to
        prepend a system message. ``messages`` can be used to provide a full list
        of prior messages, in which case ``prompt`` is appended as the final
        user entry.
        """
        # Build the messages list
        payload_messages: List[Mapping[str, str]] = []
        if messages:
            payload_messages.extend(messages)
        if system:
            payload_messages.append({"role": "system", "content": system})
        # Append the user prompt as the final message
        payload_messages.append({"role": "user", "content": prompt})

        request_body: dict = {
            "model": self.model,
            "messages": payload_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        request_body.update(kwargs)
        data = json.dumps(request_body).encode('utf-8')
        req = urllib.request.Request(
            self._make_endpoint(),
            data=data,
            method='POST',
            headers={
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            },
        )
        if self.api_key:
            req.add_header('Authorization', f'Bearer {self.api_key}')
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read()
                response = json.loads(raw.decode('utf-8'))
        except (urllib.error.URLError, urllib.error.HTTPError) as exc:
            raise BackendError('OpenAI‑compatible request failed') from exc

        # Record history (redacted) and optional transcript
        self._history.append({
            "url": req.full_url,
            "model": self.model,
            "request": request_body,
            "response": response,
        })
        self._record_transcript(request_body, response)
        # Write response artifact if enabled
        if getattr(self, "_response_path", None):
            idx = len(self._history) - 1
            response_file = self._response_path / f"response_{idx}.json"
            response_file.write_text(json.dumps(response, indent=2), encoding='utf-8')
        return response

    def read(self) -> List[Mapping[str, Any]]:
        """Return a copy of the interaction history.

        The history entries contain the request payload and the server response.
        """
        return list(self._history)

    def status(self) -> Mapping[str, Any]:
        """Return a minimal status dictionary.

        The API key is never exposed – it is represented as ``"REDACTED"`` when
        present.
        """
        return {
            "url": self.base_url,
            "model": self.model,
            "api_key": "REDACTED" if self.api_key else None,
        }

    # ---------------------------------------------------------------------
    # Low‑rank stubs – intentionally unsupported
    # ---------------------------------------------------------------------
    def lora(self, *_, **__):  # pragma: no cover
        raise UnsupportedOperationError('Low‑rank Lora not supported by OpenAI client')

    def dora(self, *_, **__):  # pragma: no cover
        raise UnsupportedOperationError('Low‑rank Dora not supported by OpenAI client')

    def sft(self, *_, **__):  # pragma: no cover
        raise UnsupportedOperationError('SFT not supported by OpenAI client')
