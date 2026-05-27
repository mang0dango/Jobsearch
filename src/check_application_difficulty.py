import csv
import requests
from bs4 import BeautifulSoup

def check_application_difficulty(url):
    """ Classify how hard the job application questions are or how long applying might take based on the number of questions. """

    STANDARD_QUESTIONS = [
        'first name', 'last name', 'preferred first name', 'email',
        'phone', 'start date year', 'end date year', 'linkedin profile',
        'website', 'country', 'school', 'degree', 'discipline', 'start date month',
        'end date month', 'gender', 'are you hispanic/latino?', 'veteran status',
        'disability status']
    EASY_QUESTIONS = ['do you currently possess an active ts/sci clearance?'] 
    MEDIUM_QUESTIONS = []
    HARD_QUESTIONS = []
    ALL_QUESTIONS =  STANDARD_QUESTIONS + EASY_QUESTIONS + MEDIUM_QUESTIONS + HARD_QUESTIONS

    def fetch_questions(url):
        """ Fetch all the job application questions. """

        questions = []

        try:

            res = requests.get(url, timeout=10)
            soup = BeautifulSoup(res.text, "html.parser")

            print("trying to fetch questions")

            text_q_wrappers = soup.find_all("div", class_="input-wrapper") 
            dropdown_q_wrappers = soup.find_all("div", class_="select__container")
            wrappers = text_q_wrappers + dropdown_q_wrappers

            for wrapper in wrappers:
                label = wrapper.find("label")

                if label:
                    question = label.get_text(strip=True).lower()
                    if "*" in question: 
                        questions.append(question.replace("*", ""))
            
            print(questions)
            
            return questions
        except Exception as e:
            print(e)
            return []

    def record_unknown(questions):
        """ Write the questions which are not yet assigned a difficulty setting to a separate file so they can be added. """

        unknown_questions = []

        for q in questions:
            if q not in ALL_QUESTIONS:
                unknown_questions.append(q)

        with open('../data/unknown_questions.csv', 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(unknown_questions)

    def evaluate(questions):
        """ Assign a difficulty marker. """

        difficulty = "unknown"
        
        if questions:
            if any(q not in ALL_QUESTIONS for q in questions):
                record_unknown(questions)
            elif any(q in HARD_QUESTIONS for q in questions):
                difficulty = "hard"
            elif any(q in MEDIUM_QUESTIONS for q in questions) or len(questions) > 20:
                difficulty = "medium"
            elif any(q in EASY_QUESTIONS for q in questions):
                difficulty = "easy"

        return difficulty

    questions = fetch_questions(url)
    difficulty = evaluate(questions)

    return difficulty

def main():
    url = "https://job-boards.greenhouse.io/kepora/jobs/4250590009?gh_src=my.greenhouse.search,,19,approved"
    print(check_application_difficulty(url))

if __name__ == "__main__":
    main()
