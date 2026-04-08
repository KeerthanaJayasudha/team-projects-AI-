import pandas as pd

def load_file(file):

    name = file.name.lower()

    if name.endswith(".csv"):
        df = pd.read_csv(file)

    elif name.endswith(".xlsx"):
        df = pd.read_excel(file)

    elif name.endswith(".json"):
        df = pd.read_json(file)

    else:
        return None

    return df