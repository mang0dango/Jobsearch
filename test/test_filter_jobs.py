import pytest
from unittest.mock import patch

from src import config
from src.filter_jobs import (
    classify,
    skill_score,
    has_skill_blacklist,
    has_experience_blacklist,
)


# ─── skill_score ────────────────────────────────────────────────────────────

def test_skill_score_counts_unique_matches():
    from src.filter_jobs import skill_score

    text = "python aws python docker"
    score, skills = skill_score(text)

    assert score == len(skills)
    assert "python" in skills
    assert "aws" in skills


# ─── has_skill_blacklist ────────────────────────────────────────────────────

def test_skill_blacklist_detects_word():
    from src.filter_jobs import has_skill_blacklist

    text = "this job involves frontend work"
    result = has_skill_blacklist(text)

    assert result == "frontend"


def test_skill_blacklist_no_match():
    from src.filter_jobs import has_skill_blacklist

    text = "backend python api work"
    result = has_skill_blacklist(text)

    assert result is None


# ─── has_experience_blacklist ───────────────────────────────────────────────

def test_experience_blacklist_detected():
    from src.filter_jobs import has_skill_blacklist

    text = "we are hiring a senior software engineer"
    result = has_experience_blacklist(text)

    assert result == "senior"


def test_experience_blacklist_ignored_if_collaborative():
    from src.filter_jobs import has_skill_blacklist

    text = "you will work with senior engineers on projects"
    result = has_experience_blacklist(text)

    assert result is None


# ─── get_company ────────────────────────────────────────────────────────────

def test_get_company_valid_url():
    from src.filter_jobs import get_company

    url = "https://boards.greenhouse.io/stripe/jobs/123"
    company = get_company(url)

    assert company == "stripe"


def test_get_company_invalid_url():
    from src.filter_jobs import get_company

    url = "invalid-url"
    company = get_company(url)

    assert company == "unknown"


# ─── classify (mock fetch_content) ──────────────────────────────────────────

@patch("src.filter_jobs.fetch_content")
def test_classify_approved(mock_fetch):
    from src.filter_jobs import classify

    mock_fetch.return_value = (
        "junior python engineer",
        "python aws docker sql"
    )

    result = classify("http://test.com")

    assert result["status"] == "approved"
    assert result["skills_matched"] >= config.MIN_NUMBER_OF_SKILLS_MATCHED


@patch("src.filter_jobs.fetch_content")
def test_classify_rejected_by_experience(mock_fetch):
    from src.filter_jobs import classify

    mock_fetch.return_value = (
        "senior engineer",
        "python aws docker"
    )

    result = classify("http://test.com")

    assert result["status"] == "rejected"
    assert "experience blacklist" in result["reason"]


@patch("src.filter_jobs.fetch_content")
def test_classify_rejected_by_skill(mock_fetch):
    from src.filter_jobs import (
        fetch_content,
        classify,
    )

    mock_fetch.return_value = (
        "frontend dev",
        "frontend javascript"
    )

    result = classify("http://test.com")

    assert result["status"] == "rejected"
    assert "skill blacklist" in result["reason"]


# ─── filter_jobs (heavy mocking) ────────────────────────────────────────────

@patch("src.filter_jobs.time.sleep", return_value=None)
@patch("src.filter_jobs.classify")
@patch("src.filter_jobs.load_jobs")
def test_filter_jobs_basic(mock_load, mock_classify, _):
    from src.filter_jobs import (
        time,
        classify,
        load_jobs,
        filter_jobs,
    )
    import pandas as pd

    mock_load.side_effect = [
        pd.DataFrame({"url": ["u1", "u2"]}),  # unfiltered
        pd.DataFrame({"url": []})             # processed
    ]

    mock_classify.side_effect = [
        {"status": "approved", "url": "u1", "skills_matched": 5},
        {"status": "rejected", "url": "u2", "skills_matched": 1},
    ]

    df, processed_rows, total = filter_jobs()

    assert total == 2
    assert len(df) == 2
    assert len(processed_rows) == 2
