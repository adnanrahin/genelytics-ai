from __future__ import annotations

from typing import Any

from genelytics.config.settings import LLMSettings


def create_chat_model(settings: LLMSettings, **overrides: Any):
    """Build a LangChain chat model from config — no provider defaults in code.

    Provider is taken from settings.provider (YAML / env). Supported:
      ollama | openai | openai_compatible | bedrock
    """
    if settings is None:
        raise ValueError(
            "LLMSettings is required. Load config via AnalyticsEngine.from_env() "
            "or load_settings(); providers are not hard-coded."
        )

    provider = (overrides.get("provider") or settings.provider or "").strip().lower()
    if not provider:
        raise ValueError("llm.provider is required in config.")

    model = overrides.get("model") or settings.model
    if not model:
        raise ValueError("llm.model is required in config.")

    temperature = overrides.get("temperature", settings.temperature)
    base_url = overrides.get("base_url", settings.base_url)
    api_key = overrides.get("api_key", settings.api_key)
    options = {**(settings.options or {}), **(overrides.get("options") or {})}

    if provider == "ollama":
        return _create_ollama(
            model=model,
            base_url=base_url,
            temperature=temperature,
            options=options,
        )

    if provider in {"openai", "openai_compatible"}:
        return _create_openai(
            model=model,
            base_url=base_url,
            api_key=api_key,
            temperature=temperature,
            max_tokens=overrides.get("max_tokens", settings.max_tokens),
            options=options,
        )

    if provider in {"bedrock", "aws_bedrock", "amazon_bedrock"}:
        return _create_bedrock(
            settings,
            model=model,
            temperature=temperature,
            max_tokens=overrides.get("max_tokens", settings.max_tokens),
            options=options,
            overrides=overrides,
        )

    raise ValueError(
        f"Unsupported LLM provider '{provider}'. "
        "Configure llm.provider in YAML as one of: "
        "ollama, openai, openai_compatible, bedrock."
    )


def _create_ollama(
    *,
    model: str,
    base_url: str | None,
    temperature: float,
    options: dict[str, Any],
):
    try:
        from langchain_ollama import ChatOllama
    except ImportError:
        try:
            from langchain_community.chat_models.ollama import ChatOllama
        except ImportError as exc:  # pragma: no cover
            raise ImportError(
                "Ollama support requires langchain-ollama. "
                "Install with: pip install langchain-ollama"
            ) from exc

    if not base_url:
        raise ValueError("llm.base_url is required for provider=ollama.")

    kwargs: dict[str, Any] = {
        "base_url": base_url,
        "model": model,
        "temperature": temperature,
        **options,
    }
    return ChatOllama(**kwargs)


def _create_openai(
    *,
    model: str,
    base_url: str | None,
    api_key: str | None,
    temperature: float,
    max_tokens: int | None,
    options: dict[str, Any],
):
    from langchain_openai import ChatOpenAI

    kwargs: dict[str, Any] = {
        "model": model,
        "temperature": temperature,
        "api_key": api_key or "EMPTY",
        **options,
    }
    if base_url:
        kwargs["base_url"] = base_url
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens
    return ChatOpenAI(**kwargs)


def _create_bedrock(
    settings: LLMSettings,
    *,
    model: str,
    temperature: float,
    max_tokens: int | None,
    options: dict[str, Any],
    overrides: dict[str, Any],
):
    region = (
        overrides.get("region_name")
        or overrides.get("region")
        or settings.resolved_region()
    )
    if not region:
        raise ValueError(
            "llm.region (or llm.region_name) is required for provider=bedrock."
        )

    try:
        from langchain_aws import ChatBedrockConverse
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "AWS Bedrock support requires langchain-aws and boto3. "
            "Install with: pip install 'genelytics[bedrock]'"
        ) from exc

    model_id = overrides.get("model_id") or settings.resolved_model_id() or model
    kwargs: dict[str, Any] = {
        "model_id": model_id,
        "region_name": region,
        "temperature": temperature,
        **options,
    }
    profile = overrides.get(
        "credentials_profile_name", settings.credentials_profile_name
    )
    if profile:
        kwargs["credentials_profile_name"] = profile

    # Explicit keys only if provided (otherwise boto3 default chain / profile)
    access_key = overrides.get("aws_access_key_id", settings.aws_access_key_id)
    secret_key = overrides.get("aws_secret_access_key", settings.aws_secret_access_key)
    session_token = overrides.get("aws_session_token", settings.aws_session_token)
    if access_key:
        kwargs["aws_access_key_id"] = access_key
    if secret_key:
        kwargs["aws_secret_access_key"] = secret_key
    if session_token:
        kwargs["aws_session_token"] = session_token
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens
    stop = overrides.get("provider_stop_sequences", settings.provider_stop_sequences)
    if stop:
        kwargs["provider_stop_sequences"] = stop

    return ChatBedrockConverse(**kwargs)
