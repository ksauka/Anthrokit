"""
Session tracking for AnthroKit adaptive research.

This module tracks:
- Which app version the user interacted with
- Anthropomorphism level/preset used
- User session metadata
- Interaction outcomes

Creates detailed logs for research analysis.
"""

import streamlit as st
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import json
import hashlib
import uuid
import os
import requests
import base64


# Session log file (local fallback only)
SESSION_LOG_PATH = Path(__file__).parent.parent / "data" / "session_tracking.jsonl"

# GitHub storage configuration (from Streamlit secrets)
def _get_github_config() -> tuple[str, str]:
    """Get GitHub token and repo from Streamlit secrets or environment.
    
    Returns:
        (github_token, github_repo) tuple
    """
    try:
        # Try Streamlit secrets first (for deployed apps)
        github_token = st.secrets.get("GITHUB_TOKEN")
        github_repo = st.secrets.get("GITHUB_REPO")
    except:
        # Fall back to environment variables (for local dev)
        github_token = os.getenv("GITHUB_TOKEN")
        github_repo = os.getenv("GITHUB_REPO")
    
    return github_token, github_repo


def get_or_create_session_id() -> str:
    """Get or create a unique session ID for this user session.
    
    Returns:
        Unique session ID (persists across page reloads)
    """
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    return st.session_state.session_id


def get_or_create_user_id(ip_address: Optional[str] = None) -> str:
    """Get or create a pseudo-anonymous user ID.
    
    Uses hashed IP or generates random ID for user tracking across sessions.
    
    Args:
        ip_address: Optional IP address to hash
        
    Returns:
        User ID (persists in session state)
    """
    if 'user_id' not in st.session_state:
        if ip_address:
            # Hash IP for pseudo-anonymity
            st.session_state.user_id = hashlib.sha256(
                ip_address.encode()
            ).hexdigest()[:16]
        else:
            # Generate random ID
            st.session_state.user_id = f"user_{uuid.uuid4().hex[:8]}"
    
    return st.session_state.user_id


def get_app_name() -> str:
    """Detect which app script is currently running.
    
    Returns:
        App name (e.g., "app.py", "app_adaptive.py", "app_condition_2.py")
    """
    # Get the script path from Streamlit
    import __main__
    script_path = getattr(__main__, '__file__', 'unknown')
    return Path(script_path).name


def track_session_start(
    app_name: Optional[str] = None,
    preset_name: Optional[str] = None,
    preset_config: Optional[Dict[str, Any]] = None,
    user_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Track the start of a user session.
    
    Args:
        app_name: Name of the app (auto-detected if None)
        preset_name: Name of preset used (e.g., "HighA", "LowA", "adaptive")
        preset_config: Full preset configuration
        user_id: User identifier
        metadata: Additional metadata (domain, experiment_id, etc.)
        
    Returns:
        Session tracking record
    """
    session_id = get_or_create_session_id()
    
    if user_id is None:
        user_id = get_or_create_user_id()
    
    if app_name is None:
        app_name = get_app_name()
    
    # Create tracking record
    record = {
        "event": "session_start",
        "session_id": session_id,
        "user_id": user_id,
        "app_name": app_name,
        "preset_name": preset_name,
        "preset_config": preset_config or {},
        "timestamp": datetime.now().isoformat(),
        "metadata": metadata or {}
    }
    
    # Store in session state
    st.session_state.session_tracking = record
    
    # Log to file
    _append_to_log(record)
    
    return record


def track_interaction(
    interaction_type: str,
    details: Optional[Dict[str, Any]] = None
):
    """Track a user interaction within the session.
    
    Args:
        interaction_type: Type of interaction (e.g., "message_sent", "button_clicked")
        details: Additional details about the interaction
        
    Examples:
        track_interaction("question_asked", {"topic": "loan_decision"})
        track_interaction("explanation_viewed", {"type": "counterfactual"})
    """
    if 'session_tracking' not in st.session_state:
        # Session not started, initialize with minimal info
        track_session_start()
    
    record = {
        "event": "interaction",
        "session_id": st.session_state.session_id,
        "user_id": st.session_state.get('user_id'),
        "app_name": st.session_state.session_tracking.get('app_name'),
        "interaction_type": interaction_type,
        "details": details or {},
        "timestamp": datetime.now().isoformat()
    }
    
    _append_to_log(record)


def track_session_end(
    participant_id: Optional[str] = None,
    outcomes: Optional[Dict[str, float]] = None,
    feedback: Optional[Dict[str, Any]] = None,
    personality_traits: Optional[Dict[str, float]] = None,
    base_preset: Optional[Dict[str, Any]] = None,
    personality_adjustments: Optional[Dict[str, float]] = None,
    final_tone_config: Optional[Dict[str, Any]] = None,
    condition_label: Optional[str] = None,
    anthropomorphism_level: Optional[str] = None,
    personality_adaptation: Optional[str] = None,
    generation_metadata: Optional[Dict[str, Any]] = None
):
    """Track the end of a user session with complete treatment documentation.
    
    This logs the TREATMENT (what AnthroKit delivered), not outcomes.
    Outcomes are measured separately in Qualtrics and linked via session_id.
    
    Args:
        participant_id: Prolific ID for data linkage and integrity verification
        outcomes: Optional outcome metrics (if collected in-app)
        feedback: Optional user feedback
        personality_traits: Raw TIPI Big 5 scores (1-7 scale)
        base_preset: Original preset BEFORE personality adjustments
        personality_adjustments: Computed deltas from trait-to-token mapping
        final_tone_config: ACTUAL tone values used (base + adjustments)
        condition_label: Human-readable condition (e.g., "HighA_Adapted")
        anthropomorphism_level: "high" or "low"
        personality_adaptation: "enabled" or "disabled"
        generation_metadata: Metadata from generation_control (Phase 1)
        
    Example:
        track_session_end(
            personality_traits={'extraversion': 6.5, 'agreeableness': 5.5, ...},
            base_preset={'warmth': 0.70, 'empathy': 0.55, ...},
            personality_adjustments={'warmth': +0.30, 'empathy': +0.17, ...},
            final_tone_config={'warmth': 0.85, 'empathy': 0.72, ...},
            condition_label="HighA_Adapted",
            anthropomorphism_level="high",
            personality_adaptation="enabled",
            generation_metadata={...}
        )
    """
    if 'session_tracking' not in st.session_state:
        return
    
    session_id = st.session_state.session_id
    
    record = {
        "event": "session_end",
        "session_id": session_id,
        "participant_id": participant_id,  # Prolific ID for data linkage
        "user_id": st.session_state.get('user_id'),
        "timestamp": datetime.now().isoformat(),
        "duration_seconds": _calculate_session_duration(),
        
        # Experimental condition
        "condition_label": condition_label or st.session_state.session_tracking.get('preset_name'),
        "anthropomorphism_level": anthropomorphism_level,
        "personality_adaptation": personality_adaptation,
        "app_version": st.session_state.session_tracking.get('app_name'),
        
        # Treatment documentation (what AnthroKit delivered)
        "personality_traits": personality_traits or {},
        "base_preset": base_preset or st.session_state.session_tracking.get('preset_config'),
        "personality_adjustments": personality_adjustments or {},
        "final_tone_config": final_tone_config or st.session_state.session_tracking.get('preset_config'),
        
        # Generation Control metadata (Phase 1)
        "generation_metadata": generation_metadata or {},
        
        # Optional: outcomes if collected in-app (usually in Qualtrics instead)
        "outcomes": outcomes or {},
        "feedback": feedback or {}
    }
    
    _append_to_log(record)


def get_session_summary() -> Dict[str, Any]:
    """Get summary of current session tracking.
    
    Returns:
        Dictionary with session metadata
    """
    if 'session_tracking' not in st.session_state:
        return {}
    
    return {
        "session_id": st.session_state.session_id,
        "user_id": st.session_state.get('user_id'),
        "app_name": st.session_state.session_tracking.get('app_name'),
        "preset_name": st.session_state.session_tracking.get('preset_name'),
        "preset_config": st.session_state.session_tracking.get('preset_config'),
        "start_time": st.session_state.session_tracking.get('timestamp')
    }


def _append_to_log(record: Dict[str, Any]):
    """Append record to GitHub repo (private) or local file as fallback."""
    github_token, github_repo = _get_github_config()
    
    if github_token and github_repo:
        # Save to GitHub (primary method for Streamlit Cloud)
        success = _save_to_github(record, github_token, github_repo)
        if success:
            return  # Successfully saved to GitHub
        else:
            print("⚠️ GitHub save failed, falling back to local file")
    
    # Fallback: Save to local file (for development/testing)
    SESSION_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(SESSION_LOG_PATH, 'a') as f:
        f.write(json.dumps(record) + '\n')


def _save_to_github(record: Dict[str, Any], github_token: str, github_repo: str) -> bool:
    """Save session record to GitHub repo.
    
    Creates/appends to: logs/session_tracking.jsonl
    
    Args:
        record: Session record dictionary
        github_token: GitHub personal access token
        github_repo: Repository in format 'owner/repo'
        
    Returns:
        True if saved successfully, False otherwise
    """
    try:
        # File path in repo
        file_path = "logs/session_tracking.jsonl"
        api_url = f"https://api.github.com/repos/{github_repo}/contents/{file_path}"
        
        headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        # Get existing file content
        r = requests.get(api_url, headers=headers, timeout=10)
        
        if r.status_code == 200:
            # File exists - append to it
            file_data = r.json()
            sha = file_data['sha']
            existing_content = base64.b64decode(file_data['content']).decode('utf-8')
            new_content = existing_content + json.dumps(record) + '\n'
        elif r.status_code == 404:
            # File doesn't exist - create it
            sha = None
            new_content = json.dumps(record) + '\n'
        else:
            print(f"GitHub API error (GET): {r.status_code} {r.text}")
            return False
        
        # Upload updated content
        data = {
            "message": f"Log session: {record.get('session_id', 'unknown')[:8]}",
            "content": base64.b64encode(new_content.encode()).decode(),
            "branch": "main"
        }
        if sha:
            data["sha"] = sha
        
        r = requests.put(api_url, headers=headers, json=data, timeout=10)
        
        if r.status_code in [200, 201]:
            print(f"✅ Session logged to GitHub: {github_repo}/logs/")
            return True
        else:
            print(f"GitHub API error (PUT): {r.status_code} {r.text}")
            return False
            
    except Exception as e:
        print(f"Error saving to GitHub: {e}")
        return False


def _calculate_session_duration() -> float:
    """Calculate session duration in seconds."""
    if 'session_tracking' not in st.session_state:
        return 0.0
    
    start_time_str = st.session_state.session_tracking.get('timestamp')
    if not start_time_str:
        return 0.0
    
    start_time = datetime.fromisoformat(start_time_str)
    duration = (datetime.now() - start_time).total_seconds()
    return duration


# ========== ANALYTICS FUNCTIONS ==========

def load_all_sessions() -> list[Dict[str, Any]]:
    """Load all session tracking records from log file.
    
    Returns:
        List of session records
    """
    if not SESSION_LOG_PATH.exists():
        return []
    
    sessions = []
    with open(SESSION_LOG_PATH, 'r') as f:
        for line in f:
            try:
                sessions.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    
    return sessions


def get_sessions_by_app(app_name: str) -> list[Dict[str, Any]]:
    """Get all sessions for a specific app.
    
    Args:
        app_name: Name of the app (e.g., "app_adaptive.py")
        
    Returns:
        List of session records for that app
    """
    all_sessions = load_all_sessions()
    return [s for s in all_sessions if s.get('app_name') == app_name]


def get_sessions_by_preset(preset_name: str) -> list[Dict[str, Any]]:
    """Get all sessions using a specific preset.
    
    Args:
        preset_name: Name of preset (e.g., "HighA", "LowA")
        
    Returns:
        List of session records with that preset
    """
    all_sessions = load_all_sessions()
    return [s for s in all_sessions if s.get('preset_name') == preset_name]


def get_sessions_by_user(user_id: str) -> list[Dict[str, Any]]:
    """Get all sessions for a specific user.
    
    Args:
        user_id: User identifier
        
    Returns:
        List of session records for that user
    """
    all_sessions = load_all_sessions()
    return [s for s in all_sessions if s.get('user_id') == user_id]


def get_anthropomorphism_distribution() -> Dict[str, int]:
    """Get distribution of anthropomorphism levels across all sessions.
    
    Returns:
        Dictionary mapping preset names to counts
    """
    all_sessions = load_all_sessions()
    session_starts = [s for s in all_sessions if s.get('event') == 'session_start']
    
    distribution = {}
    for session in session_starts:
        preset = session.get('preset_name', 'unknown')
        distribution[preset] = distribution.get(preset, 0) + 1
    
    return distribution


def get_app_usage_stats() -> Dict[str, Dict[str, Any]]:
    """Get usage statistics per app.
    
    Returns:
        Dictionary mapping app names to statistics
    """
    all_sessions = load_all_sessions()
    session_starts = [s for s in all_sessions if s.get('event') == 'session_start']
    session_ends = [s for s in all_sessions if s.get('event') == 'session_end']
    
    stats = {}
    
    for session in session_starts:
        app = session.get('app_name', 'unknown')
        if app not in stats:
            stats[app] = {
                "total_sessions": 0,
                "completed_sessions": 0,
                "presets_used": set(),
                "avg_outcomes": {}
            }
        
        stats[app]["total_sessions"] += 1
        preset = session.get('preset_name')
        if preset:
            stats[app]["presets_used"].add(preset)
    
    # Add completion and outcome data
    for session in session_ends:
        app = session.get('app_name', 'unknown')
        if app in stats:
            stats[app]["completed_sessions"] += 1
            
            # Aggregate outcomes
            outcomes = session.get('outcomes', {})
            for metric, value in outcomes.items():
                if metric not in stats[app]["avg_outcomes"]:
                    stats[app]["avg_outcomes"][metric] = []
                stats[app]["avg_outcomes"][metric].append(value)
    
    # Convert sets to lists and calculate averages
    for app in stats:
        stats[app]["presets_used"] = list(stats[app]["presets_used"])
        
        for metric in stats[app]["avg_outcomes"]:
            values = stats[app]["avg_outcomes"][metric]
            stats[app]["avg_outcomes"][metric] = {
                "mean": sum(values) / len(values) if values else 0,
                "count": len(values)
            }
    
    return stats


def export_analytics(output_path: Optional[Path] = None) -> Dict[str, Any]:
    """Export analytics report.
    
    Args:
        output_path: Optional path to save JSON report
        
    Returns:
        Analytics report dictionary
    """
    report = {
        "generated_at": datetime.now().isoformat(),
        "total_sessions": len([s for s in load_all_sessions() if s.get('event') == 'session_start']),
        "anthropomorphism_distribution": get_anthropomorphism_distribution(),
        "app_usage": get_app_usage_stats(),
        "all_sessions": load_all_sessions()
    }
    
    if output_path:
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
    
    return report


__all__ = [
    "get_or_create_session_id",
    "get_or_create_user_id",
    "get_app_name",
    "track_session_start",
    "track_interaction",
    "track_session_end",
    "get_session_summary",
    "load_all_sessions",
    "get_sessions_by_app",
    "get_sessions_by_preset",
    "get_sessions_by_user",
    "get_anthropomorphism_distribution",
    "get_app_usage_stats",
    "export_analytics",
]
