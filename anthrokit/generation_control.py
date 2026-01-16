"""
Generation Control Module 

Domain-agnostic wrapper for LLM generation with quality control.

Phase 1 (Current):
- K=1 generation (no overgeneration)
- Validation hooks for domain-specific rules
- Comprehensive metadata logging
- Zero performance/cost overhead

Phase 2 (Future):
- K>1 overgeneration
- Tone scoring and ranking
- Best candidate selection

"""

from typing import Dict, List, Optional, Callable, Tuple, Any
from datetime import datetime
import os


def _get_llm_backend():
    """
    Determine which LLM backend to use (OpenAI or Ollama).
    
    Returns:
        Tuple of (backend_name, client/base_url)
    """
    # Check for OpenAI
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=openai_key)
            return ("openai", client)
        except ImportError:
            pass
    
    # Check for Ollama
    ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    try:
        import requests
        response = requests.get(f"{ollama_base_url}/api/tags", timeout=2)
        if response.status_code == 200:
            return ("ollama", ollama_base_url)
    except Exception:
        pass
    
    return (None, None)


def _call_openai(model_name: str, prompt: str, user_input: str, temperature: float, max_tokens: int, client):
    """Call OpenAI API using SDK v1.x."""
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_input}
        ],
        temperature=temperature,
        max_tokens=max_tokens
    )
    return response.choices[0].message.content


def _call_ollama(model_name: str, prompt: str, user_input: str, temperature: float, max_tokens: int, base_url: str):
    """Call Ollama API."""
    import requests
    
    # Ollama uses different model names
    # Map common OpenAI models to Ollama equivalents
    model_map = {
        "gpt-4": "llama3.1:latest",
        "gpt-4o": "llama3.1:latest",
        "gpt-4o-mini": "llama3.1:8b",
        "gpt-3.5-turbo": "llama3.1:8b"
    }
    ollama_model = model_map.get(model_name, model_name)
    
    payload = {
        "model": ollama_model,
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_input}
        ],
        "temperature": temperature,
        "options": {
            "num_predict": max_tokens
        },
        "stream": False
    }
    
    response = requests.post(
        f"{base_url}/api/chat",
        json=payload,
        timeout=120
    )
    response.raise_for_status()
    
    result = response.json()
    return result["message"]["content"]


def generate_with_control(
    prompt: str,
    user_input: str,
    final_tone_config: Dict[str, float],
    model_name: str = "gpt-4",
    k: int = 1,
    validators: Optional[List[Callable[[str], bool]]] = None,
    temperature: float = 0.7,
    max_tokens: int = 500,
    openai_api_key: Optional[str] = None
) -> Tuple[str, Dict[str, Any]]:
    """
    Domain-agnostic generation control wrapper.
    
    Supports multiple LLM backends:
    - OpenAI (if OPENAI_API_KEY is set)
    - Ollama (if running locally at OLLAMA_BASE_URL)
    
    Phase 1: Single generation (K=1) with validation and logging.
    Phase 2: Multi-generation (K>1) with tone scoring and selection.
    
    Args:
        prompt: System prompt with tone instructions
        user_input: User's message/query
        final_tone_config: Tone parameters actually used (for logging)
        model_name: LLM identifier (e.g., "gpt-4", "llama3.1:latest")
        k: Number of candidates to generate (Phase 1: always 1)
        validators: Optional list of domain-specific validation functions
        temperature: Sampling temperature for generation
        max_tokens: Maximum response length
        openai_api_key: Optional API key (defaults to environment variable)
    
    Returns:
        Tuple of (response_text, generation_metadata)
        
    Example:
        >>> validators = [check_no_guarantees, check_policy_compliance]
        >>> response, metadata = generate_with_control(
        ...     prompt=system_prompt,
        ...     user_input="I need a loan",
        ...     final_tone_config={"warmth": 0.85, "empathy": 0.72},
        ...     validators=validators
        ... )
        >>> print(metadata["validation_results"])
        {'check_no_guarantees': True, 'check_policy_compliance': True}
    """
    # Set API key if provided
    if openai_api_key:
        os.environ["OPENAI_API_KEY"] = openai_api_key
    
    # Determine backend
    backend, backend_info = _get_llm_backend()
    
    if backend is None:
        raise ValueError(
            "No LLM backend available. Please either:\n"
            "1. Set OPENAI_API_KEY environment variable, or\n"
            "2. Start Ollama service (see install_ollama_linux.sh)"
        )
    
    # Phase 1: Single generation
    start_time = datetime.now()
    
    try:
        if backend == "openai":
            response_text = _call_openai(model_name, prompt, user_input, temperature, max_tokens, backend_info)
        elif backend == "ollama":
            response_text = _call_ollama(model_name, prompt, user_input, temperature, max_tokens, backend_info)
        else:
            raise ValueError(f"Unknown backend: {backend}")
        
        generation_success = True
        error_message = None
        
    except Exception as e:
        response_text = f"I apologize, but I encountered an error. Please try again."
        generation_success = False
        error_message = str(e)
    
    end_time = datetime.now()
    generation_time = (end_time - start_time).total_seconds()
    
    # Run validators (domain-specific safety checks)
    validation_results = {}
    if validators and generation_success:
        for validator in validators:
            try:
                validation_results[validator.__name__] = validator(response_text)
            except Exception as e:
                validation_results[validator.__name__] = {
                    "passed": False,
                    "error": str(e)
                }
    
    # Compile comprehensive metadata for logging
    generation_metadata = {
        "generation_k": k,
        "selection_method": "single",  # Phase 1: no selection, just validation
        "backend": backend,  # "openai" or "ollama"
        "model_name": model_name,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "tone_config_used": final_tone_config,
        "validation_results": validation_results,
        "generation_success": generation_success,
        "generation_time_seconds": generation_time,
        "timestamp": start_time.isoformat()
    }
    
    if error_message:
        generation_metadata["error_message"] = error_message
    
    return response_text, generation_metadata


# ============================================================================
# Domain-Specific Validators
# ============================================================================
# These are example validators. Each domain application should define its own.

def check_no_guarantees(response: str) -> bool:
    """
    Validator: Ensure no loan approval guarantees.
    Domain: Financial services (loan applications)
    
    Args:
        response: Generated text to validate
    
    Returns:
        True if no guarantees found, False otherwise
    """
    forbidden_phrases = [
        "guaranteed",
        "definitely approved",
        "promise you",
        "will be approved",
        "assured approval",
        "100% approval"
    ]
    
    response_lower = response.lower()
    return not any(phrase in response_lower for phrase in forbidden_phrases)


def check_no_medical_advice(response: str) -> bool:
    """
    Validator: Ensure no medical diagnoses or prescriptions.
    Domain: Healthcare (symptom checkers)
    
    Args:
        response: Generated text to validate
    
    Returns:
        True if no medical advice found, False otherwise
    """
    forbidden_phrases = [
        "you have",
        "diagnosed with",
        "you are suffering from",
        "take this medication",
        "prescribe",
        "medical diagnosis"
    ]
    
    response_lower = response.lower()
    return not any(phrase in response_lower for phrase in forbidden_phrases)


def check_no_homework_answers(response: str) -> bool:
    """
    Validator: Ensure doesn't give direct homework solutions.
    Domain: Education (tutoring systems)
    
    Args:
        response: Generated text to validate
    
    Returns:
        True if no direct answers found, False otherwise
    """
    forbidden_phrases = [
        "the answer is",
        "the solution is",
        "here's the answer",
        "the correct answer",
        "= " # Avoid giving final calculations
    ]
    
    response_lower = response.lower()
    return not any(phrase in response_lower for phrase in forbidden_phrases)


def check_response_length(min_words: int = 10, max_words: int = 200):
    """
    Validator factory: Check response is appropriate length.
    Domain: Universal
    
    Args:
        min_words: Minimum word count
        max_words: Maximum word count
    
    Returns:
        Validator function
    """
    def validator(response: str) -> bool:
        word_count = len(response.split())
        return min_words <= word_count <= max_words
    
    validator.__name__ = f"check_response_length_{min_words}_{max_words}"
    return validator


# ============================================================================
# Phase 2 Functions (Future Implementation)
# ============================================================================
# These are stubs for Phase 2 - not implemented yet.

def score_tone_match(candidate: str, target_config: Dict[str, float]) -> float:
    """
    Phase 2: Score how well candidate matches target tone.
    
    NOT IMPLEMENTED - Future work.
    
    Would extract linguistic features from candidate and compare to
    target_config values for warmth, empathy, formality, etc.
    
    Args:
        candidate: Generated response text
        target_config: Target tone parameters
    
    Returns:
        Score from 0.0 to 1.0 (higher = better match)
    """
    raise NotImplementedError("Phase 2 feature - tone scoring not yet implemented")


def score_fidelity(candidate: str, validators: List[Callable]) -> float:
    """
    Phase 2: Score fidelity to domain requirements.
    
    NOT IMPLEMENTED - Future work.
    
    Would run all validators and compute aggregate fidelity score.
    
    Args:
        candidate: Generated response text
        validators: List of validation functions
    
    Returns:
        Score from 0.0 to 1.0 (higher = more compliant)
    """
    raise NotImplementedError("Phase 2 feature - fidelity scoring not yet implemented")


def generate_k_best(
    prompt: str,
    user_input: str,
    final_tone_config: Dict[str, float],
    k: int = 5,
    validators: Optional[List[Callable]] = None,
    **kwargs
) -> Tuple[str, Dict[str, Any]]:
    """
    Phase 2: Generate K candidates, score, and select best.
    
    NOT IMPLEMENTED - Future work.
    
    Would generate multiple candidates, score each for tone match
    and fidelity, then select the best one.
    
    Args:
        prompt: System prompt
        user_input: User message
        final_tone_config: Target tone parameters
        k: Number of candidates to generate
        validators: Domain validation functions
    
    Returns:
        Tuple of (best_response, metadata_with_all_scores)
    """
    raise NotImplementedError("Phase 2 feature - K-best generation not yet implemented")
