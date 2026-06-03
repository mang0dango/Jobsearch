import csv
import requests
from bs4 import BeautifulSoup
import pandas as pd

from config import (
    UNKNOWN_QUESTIONS,
    REJECTED_JOBS,
    BOILERPLATE_QUESTIONS,
    EASY_KEY_PHRASES,
    MEDIUM_KEY_PHRASES,
    HARD_KEY_PHRASES,
)

ALL_KEY_PHRASES = EASY_KEY_PHRASES + MEDIUM_KEY_PHRASES + HARD_KEY_PHRASES

def record(unknown_questions: list[str]):
    """ Write the questions which the code could not understand in a separate file to help adjust the text analysis for the future. """
    
    if unknown_questions: 
        with open(UNKNOWN_QUESTIONS, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(unknown_questions)

def fetch_questions(url: str) -> list[str]:
    """ Fetch all the job application form questions. """

    questions = []

    try:

        res = requests.get(url, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")

        text_q_wrappers = soup.find_all("div", class_="input-wrapper") 
        dropdown_q_wrappers = soup.find_all("div", class_="select__container")
        wrappers = text_q_wrappers + dropdown_q_wrappers

        for wrapper in wrappers:
            label = wrapper.find("label")

            if label:
                question = label.get_text(strip=True)
                if "*" in question: 
                    normalized_q = question.lower().replace("*","")
                    questions.append(normalized_q)
        
        return questions
    except Exception as e:
        print(e)
        return []

def evaluate_difficulty(questions: list[str]) -> (str, list[str]):
    """ Check if the job application form has any questions that are not boilerplate questions, such as name, etc.
    If there are more complex customized questions, then evaluate complexity of the questions and overall form based on common key words that denote the nature of the question. 
    For questions that the companies wrote themselves instead of boilerplate questions, the wording might change while referring to the same topic. """ 

    status = "unassigned"
    unknown_questions = []    
    custom_questions = [q for q in questions if q not in BOILERPLATE_QUESTIONS]

    if custom_questions:
        for q in custom_questions:
            if not any(phrase in q for phrase in ALL_KEY_PHRASES):
                status = "unknown"
                unknown_questions.append(q)
            elif any(phrase in q for phrase in HARD_KEY_PHRASES):
                if status == "unassigned" or status == "easy" or status == "medium":
                    status = "hard"
                    print(f"Question marked as hard: {q}")
            elif any(phrase in q for phrase in MEDIUM_KEY_PHRASES):
                if status == "unassigned" or status == "easy":
                    status = "medium"
                    print(f"Question marked as medium: {q}")
            elif any(phrase in q for phrase in EASY_KEY_PHRASES):
                if status == "unassigned":
                    status = "easy"
    elif questions:
        status = "boilerplate"

    return status, unknown_questions

def main():
    count = 0
    df = pd.read_csv(REJECTED_JOBS)
    urls = df["url"].values.tolist()
    
    breakpoint()
    for url in urls:
        count += 1
        if count > 10:
            print(f"\n\nEvaluating url: {url}")
            questions = fetch_questions(url)
            difficulty, unknown_q = evaluate_difficulty(questions)
            print(f"\nQuestions: {questions}\n")
            print(f"Difficulty: {difficulty}")
            print(f"Unknown Questions: {unknown_q}")
            #record(unknown_q)
        if count > 20:
            exit()


if __name__ == "__main__":
    main()
