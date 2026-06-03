import pytest

import src.check_application_difficulty as check_application_difficulty

@pytest.mark.parametrize(
    ("questions", "expected_status", "expected_unknown_q"),
    [
        (
            [   
                "what are your salary expectations?",
                "please review and acknowledge beyondtrust's",
            ],
            "medium",
            [],
        ),
        (
            [   
                "who referred you to this job",
                "why are you interested in working for our mock company?",
            ],
            "hard",
            [],
        ),
        (
            ["what time zone are you in"],
            "easy",
            [],
        ),
        (
            ["who do you trust the most in this world?"],
            "unknown",
            ["who do you trust the most in this world?"],
        )
    ]
)
def test_check_key_phrases(questions, expected_status, expected_unknown_q):
    
    status, unknown_q = check_application_difficulty.evaluate_difficulty(questions)

    assert status == expected_status 
    assert unknown_q == expected_unknown_q

    



