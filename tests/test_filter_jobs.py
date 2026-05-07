import pandas as pd
import pytest
from unittest.mock import patch

import config
from src.filter_jobs import (
    classify,
    skill_score,
    has_skill_blacklist,
    has_experience_blacklist,
    get_company,
    filter_jobs,
)


@pytest.mark.parametrize(
    "text, expected_skills",
    [
        (
            "python aws python docker",
            {"python", "aws", "docker"},
        ),
        (
            "kuku lajava kubernetes sql java",
            {"kubernetes", "sql", "java"},
        ),
        (
            "nothing relevant here",
            set(),
        ),
    ],
)
def test_skill_score(text, expected_skills):
    score, skills = skill_score(text)

    assert skills == expected_skills
    assert score == len(expected_skills)


@pytest.mark.parametrize(
    "text, expected",
    [
        ("this job involves frontend work", "frontend"),
        ("backend python api work", None),
        ("php developer needed", "php developer"),
        ("seniority not required", None),
    ],
)
def test_has_skill_blacklist(text, expected):
    result = has_skill_blacklist(text)

    assert result == expected


@pytest.mark.parametrize(
    "text, expected",
    [
        (
            "we are hiring a senior software engineer",
            "senior",
        ),
        (
            "you will work with senior engineers on projects",
            None,
        ),
        (
            "looking for a principal engineer",
            "principal engineer",
        ),
    ],
)
def test_has_experience_blacklist(text, expected):
    result = has_experience_blacklist(text)

    assert result == expected


@pytest.mark.parametrize(
    "url, expected",
    [
        (
            "https://boards.greenhouse.io/stripe/jobs/123",
            "stripe",
        ),
        (
            "invalid-url",
            "unknown",
        ),
    ],
)
def test_get_company(url, expected):
    assert get_company(url) == expected


@pytest.mark.parametrize(
    "title, text, expected_status, expected_reason",
    [
        (
            "junior python engineer",
            "python aws docker sql",
            "approved",
            None,
        ),
        (
            "senior engineer",
            "python aws docker",
            "rejected",
            "experience blacklist",
        ),
        (
            "frontend dev",
            "frontend javascript",
            "rejected",
            "skill blacklist",
        ),
    ],
)
@patch("src.filter_jobs.fetch_content")
def test_classify(
    mock_fetch,
    title,
    text,
    expected_status,
    expected_reason,
):
    mock_fetch.return_value = (title, text)

    result = classify("http://test.com")

    assert result["status"] == expected_status

    if expected_reason:
        assert expected_reason in result["reason"]


@patch("src.filter_jobs.time.sleep", return_value=None)
@patch("src.filter_jobs.classify")
@patch("src.filter_jobs.load_jobs")
def test_filter_jobs_basic(mock_load, mock_classify, _):
    mock_load.side_effect = [
        pd.DataFrame({"url": ["u1", "u2"]}),
        pd.DataFrame({"url": []}),
    ]

    mock_classify.side_effect = [
        {
            "status": "approved",
            "url": "u1",
            "skills_matched": 5,
        },
        {
            "status": "rejected",
            "url": "u2",
            "skills_matched": 1,
        },
    ]

    df, processed_rows, total = filter_jobs()

    assert total == 2
    assert len(df) == 2
    assert len(processed_rows) == 2
