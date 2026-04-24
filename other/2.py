import pandas as pd

def load_seen_jobs() -> list[Union[int,set[int]]]:
    filepath = "seen_jobs.csv"

    if not os.path.isfile(filepath):
        return [0, ]
    else:
        df = pd.read_csv("file.csv")
            row_count = len(df) - 1



