import pandas as pd
import pytest
from unittest.mock import Mock, patch

from src.filter_jobs import (
    classify,
    fetch_content,
    filter_jobs,
    get_company,
    has_experience_blacklist,
    has_skill_blacklist,
    load_jobs,
    skill_score,
    upload,
    fetch_questions,
    record,
    evaluate_difficulty,
)


@patch("src.filter_jobs.requests.get")
def test_fetch_content_success(mock_get):
    """Should return normalized title and page text."""

    mock_response = Mock()
    mock_response.text = """
    <html>
        <h1>Junior Python Engineer</h1>
        <body>Python AWS Docker</body>
    </html>
    """

    mock_get.return_value = mock_response

    title, text = fetch_content("https://example.com")
    
    assert title == "junior python engineer"
    assert "python aws docker" in text


@patch("src.filter_jobs.requests.get")
def test_fetch_content_request_failure(mock_get):
    """Should safely return empty strings on request failure."""

    mock_get.side_effect = Exception("network error")

    title, text = fetch_content("https://example.com")

    assert title == ""
    assert text == ""


@pytest.mark.parametrize(
    ("text", "expected_skills"),
    [
        (
            "python aws docker sql",
            {"python", "aws", "docker", "sql"},
        ),
        (
            "java kubernetes sql",
            {"java", "kubernetes", "sql"},
        ),
        (
            "nothing useful here",
            set(),
        ),
    ],
)
def test_skill_score(text, expected_skills):
    score, skills = skill_score(text)

    assert skills == expected_skills
    assert score == len(expected_skills)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("frontend developer role", "frontend"),
        ("php developer needed", "php developer"),
        ("backend python api work", None),
        ("FrontEnd developer", None),  # function is case-sensitive currently
    ],
)
def test_has_skill_blacklist(text, expected):
    assert has_skill_blacklist(text) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (
            "we are hiring a senior software engineer",
            "senior",
        ),
        (
            "looking for a principal engineer",
            "principal engineer",
        ),
        (
            "you will work with senior engineers",
            None,
        ),
        (
            "mentor junior engineers while working with senior developers",
            None,
        ),
        (
            "5+ years of experience required",
            "5+ years",
        ),
    ],
)
def test_has_experience_blacklist(text, expected):
    assert has_experience_blacklist(text) == expected


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        (
            "https://boards.greenhouse.io/stripe/jobs/123",
            "stripe",
        ),
        (
            "https://boards.greenhouse.io/openai/jobs/456",
            "openai",
        ),
        (
            "invalid-url",
            "unknown",
        ),
        (
            "",
            "unknown",
        ),
    ],
)
def test_get_company(url, expected):
    assert get_company(url) == expected


def test_load_jobs_success(tmp_path):
    path = tmp_path / "jobs.csv"

    df = pd.DataFrame({"url": ["u1", "u2"]})
    df.to_csv(path, index=False)

    result = load_jobs(path)

    assert len(result) == 2
    assert list(result["url"]) == ["u1", "u2"]


def test_load_jobs_missing_file(tmp_path):
    path = tmp_path / "missing.csv"

    result = load_jobs(path)

    assert result.empty
    assert list(result.columns) == ["url"]


def test_upload_creates_file(tmp_path):
    path = tmp_path / "output.csv"

    rows = [
        {"url": "u1", "skills_matched": 5},
        {"url": "u2", "skills_matched": 2},
    ]

    upload(path, rows)

    result = pd.read_csv(path)

    assert len(result) == 2
    assert "url" in result.columns


def test_upload_deduplicates_urls(tmp_path):
    path = tmp_path / "output.csv"

    existing = pd.DataFrame(
        [
            {"url": "u1", "skills_matched": 1},
        ]
    )
    existing.to_csv(path, index=False)

    rows = [
        {"url": "u1", "skills_matched": 5},
        {"url": "u2", "skills_matched": 3},
    ]

    upload(path, rows)

    result = pd.read_csv(path)

    assert len(result) == 2
    assert set(result["url"]) == {"u1", "u2"}


def test_upload_no_rows(tmp_path):
    path = tmp_path / "output.csv"

    upload(path, [])

    assert not path.exists()


@pytest.mark.parametrize(
    (
        "url",
        "title",
        "text",
        "expected_status",
        "reason_contains",
    ),
    [
        (
            "https://boards.greenhouse.io/company/jobs/1",
            "junior python engineer",
            "python aws docker sql",
            "approved",
            None,
        ),
        (
            "https://boards.greenhouse.io/company/jobs/1",
            "senior engineer",
            "python aws docker",
            "rejected",
            "experience blacklist",
        ),
        (
            "https://boards.greenhouse.io/company/jobs/1",
            "frontend developer",
            "frontend javascript react",
            "rejected",
            "skill blacklist",
        ),
        (
            "https://boards.greenhouse.io/company/jobs/1",
            "python engineer",
            "python",
            "rejected",
            "only",
        ),
        (
            "https://example.com/job",
            "python engineer",
            "python aws docker",
            "unfiltered",
            "not default greenhouse url",
        ),
    ],
)
@patch("src.filter_jobs.fetch_content")
def test_classify(
    mock_fetch,
    url,
    title,
    text,
    expected_status,
    reason_contains,
):
    mock_fetch.return_value = (title, text)

    result = classify(url)

    assert result["status"] == expected_status
    assert result["url"] == url
    assert "company" in result
    assert "date_found" in result

    if reason_contains:
        assert reason_contains in result["reason"]


@patch("src.filter_jobs.fetch_content")
def test_classify_approved_contains_skills_list(mock_fetch):
    """Approved jobs should include a comma-separated skills list."""

    mock_fetch.return_value = (
        "python engineer",
        "python aws docker sql",
    )

    result = classify(
        "https://boards.greenhouse.io/company/jobs/1"
    )

    assert result["status"] == "approved"
    assert "skills_list" in result
    assert isinstance(result["skills_list"], str)


@patch("src.filter_jobs.time.sleep", return_value=None)
@patch("src.filter_jobs.classify")
@patch("src.filter_jobs.load_jobs")
def test_filter_jobs_basic_flow(
    mock_load,
    mock_classify,
    _mock_sleep,
):
    """Should process only unprocessed jobs."""

    fetched_jobs = pd.DataFrame(
        {"url": ["u1", "u2", "u3"]}
    )

    processed_jobs = pd.DataFrame(
        {"url": ["u2"]}
    )

    mock_load.side_effect = [
        fetched_jobs,
        processed_jobs,
    ]

    mock_classify.side_effect = [
        {"url": "u1", "status": "approved"},
        {"url": "u3", "status": "rejected"},
    ]

    df, processed_rows, total = filter_jobs()

    assert total == 2
    assert len(df) == 2
    assert len(processed_rows) == 2

    processed_urls = {
        row["url"] for row in processed_rows
    }

    assert processed_urls == {"u1", "u3"}


@patch("src.filter_jobs.time.sleep", return_value=None)
@patch("src.filter_jobs.load_jobs")
def test_filter_jobs_general_exception(
    mock_load,
    _mock_sleep,
):
    """Should safely handle unexpected exceptions."""

    mock_load.side_effect = Exception("boom")

    df, processed_rows, total = filter_jobs()

    assert df == None
    assert processed_rows == []
    assert total == 0

@patch("src.filter_jobs.requests.get")
def test_fetch_questions_extracts_required_questions(mock_get):
    """Should extract and normalize required form questions."""

    mock_response = Mock()
    mock_response.text = """
    <div class="input-wrapper">
        <label>What is your name? *</label>
    </div>

    <div class="select__container">
        <label>Preferred location *</label>
    </div>

    <div class="input-wrapper">
        <label>Optional question</label>
    </div>
    """

    mock_get.return_value = mock_response

    result = fetch_questions("https://example.com")

    assert result == [
        "what is your name? ",
        "preferred location "
    ]

@patch("src.filter_jobs.csv.writer")
@patch("builtins.open")
def test_record_writes_unknown_questions(
    mock_open,
    mock_writer,
):
    """Should write unknown questions to csv."""

    record(["question one"])

    mock_open.assert_called_once()

    mock_writer.return_value.writerow.assert_called_once_with(
        ["question one"]
    )


@pytest.mark.parametrize(
    ("questions", "expected"),
    [
        (["alien quantum interview"], "unknown"),
        (["who referred you to this role"], "easy"),
        (["what are your salary expectations"], "medium"),
        (["name all the tools like expedian"], "medium"),
        (["name at least 3 examples of how exceeded in your previous role"], "hard"),
        (["how would you explain this project"], "hard"),
        (["first name", "email"], "boilerplate"),
    ],
)
@patch("src.filter_jobs.record")
@patch("src.filter_jobs.fetch_questions")
def test_evaluate_difficulty_single_questions(mock_fetch_questions, mock_record, questions, expected):
    """
    Single-question classification cases.
    Ensures base mapping from question → difficulty is correct.
    """

    mock_fetch_questions.return_value = questions

    assert evaluate_difficulty("url") == expected


@pytest.mark.parametrize(
    ("questions", "expected"),
    [
        # easy + medium → medium
        (
            ["time zone", "what is your salary expectation"],
            "medium",
        ),

        # easy + hard → hard
        (
            ["time zone", "how would you explain your project"],
            "hard",
        ),

        # medium + hard → hard
        (
            ["what is your salary expectation", "how would you explain your project"],
            "hard",
        ),

        # boilerplate + easy → easy
        (
            ["first name", "time zone"],
            "easy",
        ),

        # boilerplate + medium → medium
        (
            ["email", "what is your salary expectation"],
            "medium",
        ),

        # boilerplate + hard → hard
        (
            ["first name", "how would you explain your project"],
            "hard",
        ),

        # unknown + anything → unknown
        (
            ["alien question", "time zone"],
            "unknown",
        ),

        (
            ["alien question", "what is your salary expectation"],
            "unknown",
        ),

        (
            ["alien question", "how would you explain your project"],
            "unknown",
        ),

        # 3-way mix → hard wins
        (
            [
                "time zone",
                "what is your salary expectation",
                "how would you explain your project",
            ],
            "hard",
        ),

        # shuffled order should not matter
        (
            [
                "how would you explain your project",
                "what time is your availability",
                "what is your salary expectation",
            ],
            "hard",
        ),

        # repeated same category
        (
            [
                "your time zone",
                "your time zone",
                "your time zone",
            ],
            "easy",
        ),

        # multiple unknowns
        (
            [
                "alien question",
                "quantum giraffe interview",
                "neural banana protocol",
            ],
            "unknown",
        ),
    ],
)
@patch("src.filter_jobs.record")
@patch("src.filter_jobs.fetch_questions")
def test_evaluate_difficulty_multi_question_cases(mock_fetch_questions, mock_record, questions, expected):
    """
    Multi-question interaction tests.
    Ensures correct priority resolution:
    unknown > hard > medium > easy > boilerplate
    """

    mock_fetch_questions.return_value = questions

    assert evaluate_difficulty("url") == expected

