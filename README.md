# News Analysis Application

This project is a Flask web application that integrates with the News API and OpenAI's GPT-4 model to fetch, process, and analyze news articles. Users can search for news articles based on a query and date range, and the application will summarize the articles, extract key points, analyze sentiment, and classify their topics.

## Table of Contents

- [Features](#features)
- [Technologies Used](#technologies-used)
- [Setup](#setup)
- [Usage](#usage)
- [Code Explanation](#code-explanation)
- [License](#license)

## Features

- **Search Articles**: Users can search for news articles by keyword and specify a date range.
- **Article Summarization**: The application summarizes the content of the articles using OpenAI's GPT-4 model.
- **Key Points Extraction**: Key points from each article are extracted for quick understanding.
- **Sentiment Analysis**: The sentiment of each article is classified as positive, neutral, or negative.
- **Topic Classification**: Articles are categorized into relevant topics based on their content.
- **Pagination**: Users can view multiple batches of articles, making it easier to browse large datasets.

## Technologies Used

- **Python**: The main programming language used for developing the application.
- **Flask**: A lightweight web framework for building web applications in Python.
- **OpenAI API**: Used for generating summaries and performing analysis on the article content.
- **NewsAPI**: A service that provides access to news articles from various sources.
- **HTML/CSS**: For front-end rendering of the application.

## Setup

### Prerequisites

Make sure you have Python 3.6 or later installed on your machine. You can download it from [python.org](https://www.python.org/downloads/).

### Clone the Repository

1. Clone this repository:

   ```bash
   git clone https://github.com/yourusername/news-analysis-app.git

Navigate to the project directory:

bash
Copy code
cd news-analysis-app
Install Required Packages
It is recommended to create a virtual environment to manage dependencies. You can create one using the following commands:

bash
Copy code
python -m venv venv
Then, activate the virtual environment:

On Windows:

bash
Copy code
venv\Scripts\activate
On macOS/Linux:

bash
Copy code
source venv/bin/activate
Install the required packages:

bash
Copy code
pip install Flask requests openai newsapi-python
Set Up API Keys
In the app.py file, set your API keys:

python
Copy code
openai.api_key = "your_openai_api_key"  # Replace with your OpenAI API key
NEWS_API_KEY = "your_news_api_key"  # Replace with your News API key
Run the Application
Run the application using the following command:

bash
Copy code
python app.py
Open your browser and go to http://127.0.0.1:5000 to access the application.

## Usage
Search Articles: Enter your search query and select the date range using the provided input fields.
View Results: Click the "Search" button to fetch news articles. The results will include summaries, key points, sentiment analysis, and topics.
Next Batch: Use the "Next Batch" button to fetch additional articles if available.
Code Explanation
The code consists of several key components that work together to fetch, process, and analyze news articles.

Imports
The necessary libraries are imported at the beginning of the app.py file:
## Code Explanation
python
Copy code
from flask import Flask, render_template, request, session
import os
import requests
import openai
import re
from typing import List, Dict
from newsapi import NewsApiClient
API Key Setup
API keys for OpenAI and News API are defined for authentication:

python
Copy code
openai.api_key = "your_openai_api_key"
NEWS_API_KEY = "your_news_api_key"
Flask App Initialization
A Flask application is initialized, and a secret key is set for session management:

python
Copy code
app = Flask(__name__)
app.secret_key = 'your_secret_key'
Constants
Constants such as BATCH_SIZE define how many articles are fetched in each request:

python
Copy code
BATCH_SIZE = 5  # Number of articles to fetch each time
Data Collection
The fetch_news_articles function retrieves news articles based on the user's query and date range. It handles pagination by using the page parameter:

python
Copy code
def fetch_news_articles(query: str, from_date: str, to_date: str, page: int) -> List[Dict]:
    try:
        all_articles = newsapi.get_everything(
            q=query,
            from_param=from_date,
            to=to_date,
            sort_by='publishedAt',
            language='en',
            page_size=BATCH_SIZE,
            page=page
        )
        articles = all_articles.get('articles', [])
        return [
            {
                "title": article["title"],
                "date": article["publishedAt"],
                "content": article["content"],
                "source": article["source"]["name"],
                "url": article["url"]
            }
            for article in articles if article.get("content")
        ]
    except Exception as e:
        print(f"Error fetching news articles: {e}")
        return []
Article Processing
The clean_text function removes HTML tags and special characters from the article content:

python
Copy code
def clean_text(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)  # Remove HTML tags
    text = re.sub(r"[^a-zA-Z0-9\s]", "", text)  # Remove special characters
    text = re.sub(r"\s+", " ", text).strip()  # Clean whitespace
    return text
The preprocess_articles function processes each article and cleans the content:

python
Copy code
def preprocess_articles(articles: List[Dict]) -> List[Dict]:
    processed_articles = []
    for article in articles:
        cleaned_content = clean_text(article["content"]) if article["content"] else ""
        processed_articles.append({
            "title": article["title"],
            "date": article["date"],
            "content": cleaned_content,
            "source": article["source"],
            "url": article["url"]
        })
    return processed_articles
LLM Integration
The get_llm_analysis function interacts with the OpenAI API to perform various analyses on the article content:

python
Copy code
def get_llm_analysis(article_content: str, prompt_template: str) -> str:
    prompt = prompt_template.format(article_content=article_content)
    messages = [{"role": "user", "content": prompt}]
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=messages,
            max_tokens=150,
            temperature=0.2,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
        return response.choices[0].message['content'].strip()
    except Exception as e:
        print(f"Error processing with LLM: {e}")
        return "Analysis could not be generated."
Specific Analysis Functions
Functions for specific analyses call get_llm_analysis with tailored prompts:

python
Copy code
def summarize_article(article_content: str) -> str:
    prompt_template = "Please summarize the following article: {article_content}"
    return get_llm_analysis(article_content, prompt_template)

def extract_key_points(article_content: str) -> str:
    prompt_template = "Extract key points from the following article: {article_content}"
    return get_llm_analysis(article_content, prompt_template)

def sentiment_analysis(article_content: str) -> str:
    prompt_template = "What is the sentiment of the following article? (positive, neutral, negative): {article_content}"
    return get_llm_analysis(article_content, prompt_template)

def classify_topic(article_content: str) -> str:
    prompt_template = "Classify the topic of the following article: {article_content}"
    return get_llm_analysis(article_content, prompt_template)
Flask Routes
The main routes handle requests from users. The index route processes searches and displays results:

python
Copy code
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        search_query = request.form['search_query']
        from_date = request.form['from_date']
        to_date = request.form['to_date']
        
        if search_query and from_date and to_date:
            session['current_page'] = 1
            session['search_query'] = search_query
            session['from_date'] = from_date
            session['to_date'] = to_date
            
            articles = fetch_news_articles(search_query, from_date, to_date, session['current_page'])
            if not articles:
                return render_template('index.html', message="No articles found.")

            processed_articles = preprocess_articles(articles)
            session['results'] = process_batch(processed_articles)
            session['has_next_batch'] = len(articles) == BATCH_SIZE

            return render_template('index.html', results=session['results'], has_next_batch=session['has_next_batch'])

    results = session.get('results', [])
    has_next_batch = session.get('has_next_batch', False)
    return render_template('index.html', results=results, has_next_batch=has_next_batch)

@app.route('/next_batch', methods=['POST'])
def next_batch():
    current_page = session.get('current_page', 1) + 1
    session['current_page'] = current_page
    
    articles = fetch_news_articles(session['search_query'], session['from_date'], session['to_date'], current_page)
    if not articles:
        return {'success': False, 'message': 'No more articles available.'}
    
    processed_articles = preprocess_articles(articles)
    session['results'].extend(process_batch(processed_articles))
    session['has_next_batch'] = len(articles) == BATCH_SIZE
    
    return {'success': True, 'results': session['results'], 'has_next_batch': session['has_next_batch']}
Running the Application
Finally, the application runs if executed directly:

python
Copy code
if __name__ == "__main__":
    app.run(debug=True)
License
This project is licensed under the MIT License. See the LICENSE file for details.
