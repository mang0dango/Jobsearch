import os
import sys
import pytest
from unittest.mock import Mock, patch, call

import src.fetch_jobs as fetch_jobs


@patch("src.fetch_jobs.webdriver.Chrome")
def test_create_driver(mock_chrome):
    """Should create Chrome driver with correct service + options."""

    driver = fetch_jobs.create_driver()

    assert driver == mock_chrome.return_value
    mock_chrome.assert_called_once()

    args, kwargs = mock_chrome.call_args
    assert "service" in kwargs
    assert "options" in kwargs


@patch("src.fetch_jobs.time.sleep", return_value=None)
@patch("src.fetch_jobs.input", side_effect=["yes"])
def test_login_success(mock_input, _sleep):
    """Should detect login success after user confirmation."""

    fake_driver = Mock()
    fake_driver.current_url = "https://my.greenhouse.io/jobs"

    with patch.object(fetch_jobs, "driver", fake_driver):
        fetch_jobs.ensure_greenhouse_logged_in()

        assert fake_driver.get.called


@patch("src.fetch_jobs.sys.exit", side_effect=SystemExit)
@patch("src.fetch_jobs.input", side_effect=["no"])
@patch("src.fetch_jobs.time.sleep", return_value=None)
def test_login_exit(mock_sleep, mock_input, mock_exit):
    """Should exit when user declines login."""

    fake_driver = Mock()
    fake_driver.current_url = "https://my.greenhouse.io/sign_in"

    with patch.object(fetch_jobs, "driver", fake_driver):
        with pytest.raises(SystemExit):
            fetch_jobs.ensure_greenhouse_logged_in()

    mock_exit.assert_called_once_with(1)

@patch("src.fetch_jobs.time.sleep", return_value=None)
def test_login_already_logged_in(_sleep):
    """Should skip prompt if already logged in."""

    fake_driver = Mock()
    fake_driver.current_url = "https://my.greenhouse.io/jobs"

    with patch.object(fetch_jobs, "driver", fake_driver):
        fetch_jobs.ensure_greenhouse_logged_in()


@patch("src.fetch_jobs.time.sleep", return_value=None)
def test_load_greenhouse(_sleep):
    """Should navigate to query URL."""

    fake_driver = Mock()

    with patch.object(fetch_jobs, "driver", fake_driver):
        fetch_jobs.load_greenhouse("https://example.com/search")

        fake_driver.get.assert_called_once_with(
            "https://example.com/search"
        )


@patch("src.fetch_jobs.random.randint", return_value=2)
@patch("src.fetch_jobs.time.sleep", return_value=None)
def test_scroll_page(_sleep, _randint):
    """Should execute JS scroll command."""

    fake_driver = Mock()

    with patch.object(fetch_jobs, "driver", fake_driver):
        fetch_jobs.scroll_page()

        fake_driver.execute_script.assert_called_once()


@patch("src.fetch_jobs.random.randint", return_value=2)
@patch("src.fetch_jobs.time.sleep", return_value=None)
def test_click_load_more_button_success(_sleep, _randint):
    """Should click load more button when present."""

    fake_button = Mock()

    fake_driver = Mock()
    fake_driver.find_elements.return_value = [fake_button]

    with patch.object(fetch_jobs, "driver", fake_driver):
        result = fetch_jobs.click_load_more_button()

        assert result is True
        assert fake_driver.execute_script.called


@patch("src.fetch_jobs.time.sleep", return_value=None)
def test_click_load_more_button_not_found(_sleep):
    """Should return False when no button exists."""

    fake_driver = Mock()
    fake_driver.find_elements.return_value = []

    with patch.object(fetch_jobs, "driver", fake_driver):
        result = fetch_jobs.click_load_more_button()

        assert result is False


@patch("src.fetch_jobs.time.sleep", return_value=None)
def test_click_load_more_button_exception(_sleep):
    """Should handle click failure gracefully."""

    fake_button = Mock()

    fake_driver = Mock()
    fake_driver.find_elements.return_value = [fake_button]
    fake_driver.execute_script.side_effect = Exception("fail")

    with patch.object(fetch_jobs, "driver", fake_driver):
        result = fetch_jobs.click_load_more_button()

        assert result is False


def test_collect_visible_jobs():
    """Should extract hrefs from DOM elements."""

    fake_job = Mock()
    fake_link = Mock()
    fake_link.get_attribute.return_value = "https://job.com/1"

    fake_job.find_element.return_value = fake_link

    fake_driver = Mock()
    fake_driver.find_elements.return_value = [fake_job]

    with patch.object(fetch_jobs, "driver", fake_driver):
        result = fetch_jobs.collect_visible_jobs()

        assert "https://job.com/1" in result


def test_collect_visible_jobs_missing_href():
    """Should skip invalid job entries."""

    fake_job = Mock()
    fake_job.find_element.side_effect = Exception("fail")

    fake_driver = Mock()
    fake_driver.find_elements.return_value = [fake_job]

    with patch.object(fetch_jobs, "driver", fake_driver):
        result = fetch_jobs.collect_visible_jobs()

        assert result == set()


@patch("src.fetch_jobs.random.randint", return_value=2)
@patch("src.fetch_jobs.time.sleep", return_value=None)
def test_collect_jobs_basic_flow(_sleep, _randint):
    """Should collect jobs and respect max limit."""

    fake_driver = Mock()

    fake_driver.find_elements.return_value = []

    with patch.object(fetch_jobs, "driver", fake_driver), \
         patch("src.fetch_jobs.collect_visible_jobs", return_value={"a", "b"}), \
         patch("src.fetch_jobs.click_load_more_button", return_value=False), \
         patch("src.fetch_jobs.scroll_page"):

        result = fetch_jobs.collect_jobs(max_jobs=2)

        assert len(result) <= 2


@patch("src.fetch_jobs.random.randint", return_value=2)
@patch("src.fetch_jobs.time.sleep", return_value=None)
def test_collect_jobs_stagnation_break(_sleep, _randint):
    """Should stop when no new jobs are found repeatedly."""

    fake_driver = Mock()

    with patch.object(fetch_jobs, "driver", fake_driver), \
         patch("src.fetch_jobs.collect_visible_jobs", return_value=set()), \
         patch("src.fetch_jobs.scroll_page"), \
         patch("src.fetch_jobs.click_load_more_button"):

        result = fetch_jobs.collect_jobs(max_jobs=10)

        assert isinstance(result, set)


def test_save_all_jobs_creates_csv(tmp_path):
    """Should create directory and save CSV."""

    file_path = tmp_path / "data/jobs.csv"

    jobs = {"a", "b", "c"}

    fetch_jobs.save_all_jobs(jobs, file_path=str(file_path))

    assert file_path.exists()

    content = file_path.read_text()
    assert "url" in content


@patch("src.fetch_jobs.save_all_jobs")
@patch("src.fetch_jobs.collect_jobs", return_value={"a"})
@patch("src.fetch_jobs.load_greenhouse")
@patch("src.fetch_jobs.ensure_greenhouse_logged_in")
@patch("src.fetch_jobs.create_driver")
def test_main_flow(
    mock_driver,
    mock_login,
    mock_load,
    mock_collect,
    mock_save,
):
    """Should run pipeline without crashing."""

    mock_driver.return_value = Mock()

    with patch("src.fetch_jobs.config.GREENHOUSE_SEARCHES", ["q1", "q2"]):
        fetch_jobs.main()

        mock_login.assert_called_once()
        assert mock_load.call_count == 2
        mock_save.assert_called_once()
