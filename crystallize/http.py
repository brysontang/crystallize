"""Instrumented HTTP client for Crystallize.

Wraps the requests library to track field provenance for audit.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from .protocol import ProtocolEvent, SENSITIVE_FIELDS, determine_provenance

# Type for response objects (we don't want to import requests at module level)
ResponseType = Any


class InstrumentedHTTP:
    """HTTP client that tracks field provenance for audit.

    Use this via ctx.http in your experiment function to enable protocol auditing.

    Example
    -------
    >>> def my_experiment(config, ctx):
    ...     response = ctx.http.post(
    ...         "https://api.openai.com/v1/chat/completions",
    ...         json={"model": config["model"], "messages": [...]}
    ...     )
    ...     return response.json()
    """

    def __init__(
        self,
        config: Dict[str, Any],
        config_name: str,
        config_fingerprint: str,
    ):
        """Initialize the instrumented HTTP client.

        Parameters
        ----------
        config : dict
            The experiment config (for provenance checking)
        config_name : str
            Name of the config
        config_fingerprint : str
            Fingerprint of the config
        """
        self._config = config
        self._config_name = config_name
        self._config_fingerprint = config_fingerprint
        self._events: List[ProtocolEvent] = []
        self._session: Optional[Any] = None

    @property
    def events(self) -> List[ProtocolEvent]:
        """Get all recorded protocol events."""
        return self._events.copy()

    def _get_session(self) -> Any:
        """Lazily import and create requests session."""
        if self._session is None:
            try:
                import requests

                self._session = requests.Session()
            except ImportError:
                raise ImportError(
                    "The 'requests' library is required for ctx.http. "
                    "Install it with: pip install requests"
                )
        return self._session

    def _analyze_fields(
        self,
        json_body: Optional[Dict[str, Any]],
        data: Optional[Dict[str, Any]],
    ) -> Dict[str, Dict[str, Any]]:
        """Analyze field provenance in request body.

        Parameters
        ----------
        json_body : dict, optional
            JSON body of the request
        data : dict, optional
            Form data of the request

        Returns
        -------
        dict
            Field analysis {field_name: {value, source}}
        """
        fields: Dict[str, Dict[str, Any]] = {}
        body = json_body or data or {}

        # Analyze each field in the request
        for field_name, value in body.items():
            source = determine_provenance(
                field_name=field_name,
                value=value,
                config=self._config,
                present_in_request=True,
            )
            fields[field_name] = {"value": value, "source": source}

        # Check for sensitive fields that are MISSING from the request
        for sensitive_field in SENSITIVE_FIELDS:
            if sensitive_field not in body:
                # Only mark as implicit_default if this looks like an API call
                # (we check for common LLM API fields)
                llm_api_indicators = {"messages", "prompt", "input", "model"}
                if any(indicator in body for indicator in llm_api_indicators):
                    fields[sensitive_field] = {
                        "value": None,
                        "source": "implicit_default",
                    }

        return fields

    def _record_event(
        self,
        method: str,
        url: str,
        json_body: Optional[Dict[str, Any]],
        data: Optional[Dict[str, Any]],
    ) -> None:
        """Record a protocol event for this request."""
        fields = self._analyze_fields(json_body, data)

        event = ProtocolEvent.create(
            config_name=self._config_name,
            config_fingerprint=self._config_fingerprint,
            method=method,
            url=url,
            fields=fields,
        )
        self._events.append(event)

    def request(
        self,
        method: str,
        url: str,
        **kwargs: Any,
    ) -> ResponseType:
        """Make an HTTP request with provenance tracking.

        Parameters
        ----------
        method : str
            HTTP method (GET, POST, etc.)
        url : str
            Request URL
        **kwargs
            Additional arguments passed to requests

        Returns
        -------
        Response
            requests.Response object
        """
        session = self._get_session()

        # Extract body for analysis
        json_body = kwargs.get("json")
        data = kwargs.get("data") if isinstance(kwargs.get("data"), dict) else None

        # Record the event before making the request
        self._record_event(method, url, json_body, data)

        # Make the actual request
        return session.request(method, url, **kwargs)

    def get(self, url: str, **kwargs: Any) -> ResponseType:
        """Make a GET request with provenance tracking."""
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> ResponseType:
        """Make a POST request with provenance tracking."""
        return self.request("POST", url, **kwargs)

    def put(self, url: str, **kwargs: Any) -> ResponseType:
        """Make a PUT request with provenance tracking."""
        return self.request("PUT", url, **kwargs)

    def patch(self, url: str, **kwargs: Any) -> ResponseType:
        """Make a PATCH request with provenance tracking."""
        return self.request("PATCH", url, **kwargs)

    def delete(self, url: str, **kwargs: Any) -> ResponseType:
        """Make a DELETE request with provenance tracking."""
        return self.request("DELETE", url, **kwargs)

    def head(self, url: str, **kwargs: Any) -> ResponseType:
        """Make a HEAD request with provenance tracking."""
        return self.request("HEAD", url, **kwargs)

    def options(self, url: str, **kwargs: Any) -> ResponseType:
        """Make an OPTIONS request with provenance tracking."""
        return self.request("OPTIONS", url, **kwargs)


class NoAuditHTTP:
    """Placeholder HTTP client that raises errors when used.

    This is used when audit="none" to make it clear that
    HTTP calls are not being tracked.
    """

    def __getattr__(self, name: str) -> Callable[..., None]:
        """Raise error for any method call."""

        def _raise(*args: Any, **kwargs: Any) -> None:
            raise RuntimeError(
                "ctx.http is not available when audit='none'. "
                "Either set audit='calls' in explore(), or use the "
                "requests library directly (but this will result in "
                "'unknown' provenance and block VALID integrity status)."
            )

        return _raise
