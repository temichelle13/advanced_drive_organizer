import os
import shutil
import hashlib
import logging
import json
import tkinter as tk
from tkinter import simpledialog, messagebox
from tqdm import tqdm
import concurrent.futures
import pytesseract
from PIL import Image
from PyPDF2 import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from logging.handlers import RotatingFileHandler
from nltk.tokenize import word_tokenize

# Set up logging with RotatingFileHandler
log_handler = RotatingFileHandler('file_organizer.log', maxBytes=1000000, backupCount=5)
logging.basicConfig(handlers=[log_handler], level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load and save categories from/to a JSON file
def load_categories():
    try:
        with open('categories.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            'academic': ['research', 'thesis', 'paper', 'study'],
            'finance': ['invoice', 'receipt', 'bank', 'statement'],
            'developer': ['code', 'script', 'program', 'software'],
            'personal': ['photo', 'music', 'video', 'diary'],
            'business': ['contract', 'agreement', 'proposal', 'report'],
        }
    except json.JSONDecodeError:
        logging.error('Error decoding categories.json. Ensure it is a valid JSON file.')
        return {}

def save_categories(categories):
    with open('categories.json', 'w') as f:
        json.dump(categories, f)

categories = load_categories()
review_later_folder = 'review_later'

# Compute hash for duplicates
def compute_hash(file_path):
    hash_algo = hashlib.sha256()
    try:
        with open(file_path, 'rb') as f:
            if os.path.getsize(file_path) > 10 * 1024 * 1024:  # Files larger than 10MB
                hash_algo.update(f.read(8192))  # First 8KB
                f.seek(-8192, os.SEEK_END)  # Last 8KB
                hash_algo.update(f.read(8192))
            else:
                while chunk := f.read(8192):
                    hash_algo.update(chunk)
    except Exception as e:
        logging.error(f'Error computing hash for file {file_path}: {e}')
    return hash_algo.hexdigest()

# Train a placeholder text classifier (to be replaced with a real model)
def train_text_classifier():
    # This is a placeholder. In a real scenario, you'd load a pre-trained model.
    vectorizer = TfidfVectorizer()
    model = MultinomialNB()
    return vectorizer, model

vectorizer, model = train_text_classifier()

# Categorize file based on content
def categorize_file(file_name, file_content):
    try:
        tokens = word_tokenize(file_content.lower())
        tokens = [word for word in tokens if word.isalnum()]

        text_vector = vectorizer.transform([' '.join(tokens)])
        predicted_category = model.predict(text_vector)[0]

        for category in categories.keys():
            if category in predicted_category:
                return category
    except Exception as e:
        logging.error(f'Error categorizing file {file_name}: {e}')
    return None

# Move file with error handling
def move_file(src_path, dest_dir):
    try:
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)
        shutil.move(src_path, dest_dir)
        logging.info(f'Moved file {src_path} to {dest_dir}')
    except PermissionError:
        logging.error(f'Permission denied while moving {src_path}.')
    except Exception as e:
        logging.error(f'Error moving file {src_path}: {e}')

# Handle duplicates
def handle_duplicates(file_path, duplicates_dir):
    file_hash = compute_hash(file_path)
    duplicate_path = os.path.join(duplicates_dir, file_hash)
    try:
        if os.path.exists(duplicate_path):
            dest_dir = os.path.join(duplicates_dir, file_hash[:2], file_hash[2:4], file_hash)
            move_file(file_path, dest_dir)
            logging.info(f'Found duplicate: {file_path}')
        else:
            os.makedirs(duplicate_path)
            shutil.move(file_path, duplicate_path)
            logging.info(f'Hash directory created for {file_path}')
    except Exception as e:
        logging.error(f'Error handling duplicates for file {file_path}: {e}')

# Extract text for review
def extract_text(file_path):
    try:
        if file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
            text = pytesseract.image_to_string(Image.open(file_path))
        elif file_path.lower().endswith('.pdf'):
            text = ""
            with open(file_path, 'rb') as file:
                reader = PdfReader(file)
                for page_num in range(len(reader.pages)):
                    page = reader.pages[page_num]
                    text += page.extract_text()
        else:
            with open(file_path, 'r', errors='ignore') as file:
                text = file.read()
        return text
    except Exception as e:
        logging.error(f'Error extracting text from file {file_path}: {e}')
        return ""

# Prompt user for action (batched)
def prompt_user_for_action_batch(files):
    root = tk.Tk()
    root.withdraw()  # Hide the main window

    for file_path, extracted_text in files.items():
        message = f"File: {file_path}\nExtracted Text: {extracted_text[:500]}...\n\nChoose an action:"
        user_input = simpledialog.askstring("Categorize File", message)

        if user_input:
            if user_input.lower() == "review later":
                move_file(file_path, review_later_folder)
            else:
                categories[user_input.lower()] = categories.get(user_input.lower(), [])
                move_file(file_path, os.path.join('categorized_files', user_input.lower()))
        else:
            move_file(file_path, review_later_folder)

    root.destroy()

# Update progress with tqdm
def update_progress(tqdm_instance, total):
    tqdm_instance.update(1)

# Process directory with multithreading
def process_file(file_path, duplicates_dir):
    try:
        if os.path.isfile(file_path):
            with open(file_path, 'r', errors='ignore') as file:
                file_content = file.read()
            category = categorize_file(os.path.basename(file_path), file_content)

            if category:
                dest_dir = os.path.join('categorized_files', category)
                move_file(file_path, dest_dir)
            else:
                extracted_text = extract_text(file_path)
                prompt_user_for_action_batch({file_path: extracted_text})

            handle_duplicates(file_path, duplicates_dir)
    except PermissionError:
        logging.error(f'Permission denied for file {file_path}. Skipping.')
    except Exception as e:
        logging.error(f'Error processing file {file_path}: {e}')

def process_directory(directory, duplicates_dir):
    total_files = sum([len(files) for r, d, files in os.walk(directory)])
    with tqdm(total=total_files, desc="Processing files") as pbar:
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            for root, _, files in os.walk(directory):
                for file_name in files:
                    file_path = os.path.join(root, file_name)
                    futures.append(executor.submit(process_file, file_path, duplicates_dir))

            for future in concurrent.futures.as_completed(futures):
                update_progress(pbar, total_files)

# Main script execution with command-line arguments
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='File Organizer Script')
    parser.add_argument('--source', required=True, help='Path to the source directory')
    parser.add_argument('--duplicates', required=True, help='Path to the duplicates directory')
    args = parser.parse_args()

    source_directory = args.source
    duplicates_directory = args.duplicates

    if not os.path.exists(review_later_folder):
        os.makedirs(review_later_folder)

    process_directory(source_directory, duplicates_directory)
    logging.info('File organization completed')
