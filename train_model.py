import json
import nltk
from nltk.tokenize import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from joblib import dump


def load_categories():
    """Load categories from categories.json or return defaults."""
    try:
        with open('categories.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            'academic': ['research', 'thesis', 'paper', 'study'],
            'finance': ['invoice', 'receipt', 'bank', 'statement'],
            'developer': ['code', 'script', 'program', 'software'],
            'personal': ['photo', 'music', 'video', 'diary'],
            'business': ['contract', 'agreement', 'proposal', 'report'],
        }


def prepare_dataset(categories):
    texts = []
    labels = []
    for label, keywords in categories.items():
        for keyword in keywords:
            texts.append(keyword)
            labels.append(label)
    return texts, labels


def train_and_save():
    nltk.download('punkt', quiet=True)
    nltk.download('punkt_tab', quiet=True)
    categories = load_categories()
    texts, labels = prepare_dataset(categories)

    vectorizer = TfidfVectorizer(tokenizer=word_tokenize)
    X = vectorizer.fit_transform(texts)

    model = MultinomialNB()
    model.fit(X, labels)

    dump(vectorizer, 'vectorizer.joblib')
    dump(model, 'model.joblib')


if __name__ == '__main__':
    train_and_save()
