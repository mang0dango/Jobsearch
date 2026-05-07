import pandas as pd
import pytest
from unittest.mock import patch
from unittest.mock import Mock

import config

@patch("src.fetch_jobs.driver")
def test_find_jobs(mock_driver):
    from src.fetch_jobs import find_jobs

    mock_job = Mock()
    mock_btn = Mock()

    mock_btn.get_attribute.return_value = "http://job1.com"

    mock_job.find_element.return_value = mock_btn

    mock_driver.find_elements.return_value = [mock_job]

    result = find_jobs()

    assert result == {"http://job1.com"}

