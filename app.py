# conda activate isolated_langchain_env

import os
import re
import logging
from flask import Flask, render_template, request, session
from typing import List, Dict
from newsapi import NewsApiClient
import openai

# Set up logging
logging.basicConfig(level=logging.INFO)

# Load API keys from environment variables
openai.api_key = os.getenv("OPENAI_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY") 

# Initialize News API Client
newsapi = NewsApiClient(api_key=NEWS_API_KEY)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", 'default_secret_key')  # Default for development

# Constants
BATCH_SIZE = 5  # Number of articles to fetch each time

# 1. Data Collection (API Integration)
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
        logging.error(f"Error fetching news articles: {e}")
        return []

# 2. Article Processing
def clean_text(text: str) -> str:
    # Remove HTML tags and special characters, and clean up whitespace
    text = re.sub(r"<[^>]+>", "", text)  # Remove HTML tags
    text = re.sub(r"[^\w\s]", "", text)  # Remove special characters, keeping letters and digits
    text = re.sub(r"\s+", " ", text).strip()  # Clean up whitespace
    return text

def preprocess_articles(articles: List[Dict]) -> List[Dict]:
    processed_articles = []
    for article in articles:
        cleaned_content = clean_text(article.get("content", ""))  # Default to empty string if None
        processed_articles.append({
            "title": article["title"],
            "date": article["date"],
            "content": cleaned_content,
            "source": article["source"],
            "url": article["url"]
        })
    return processed_articles

# 3. LLM Integration
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
        logging.error(f"Error processing with LLM: {e}")
        return "Analysis could not be generated."

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

# Flask routes
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        search_query = request.form.get('search_query')
        from_date = request.form.get('from_date')
        to_date = request.form.get('to_date')
        
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
    session['current_page'] += 1  # Increment the page number
    search_query = session['search_query']
    from_date = session['from_date']
    to_date = session['to_date']

    articles = fetch_news_articles(search_query, from_date, to_date, session['current_page'])
    if not articles:
        return render_template('index.html', message="No more articles found.")

    processed_articles = preprocess_articles(articles)
    if 'results' in session:
        session['results'].extend(process_batch(processed_articles))
    else:
        session['results'] = process_batch(processed_articles)

    session['has_next_batch'] = len(articles) == BATCH_SIZE

    return render_template('index.html', results=session['results'], has_next_batch=session['has_next_batch'])

def process_batch(processed_articles: List[Dict]) -> List[Dict]:
    results = []
    for article in processed_articles:
        summary = summarize_article(article["content"])
        key_points = extract_key_points(article["content"])
        sentiment = sentiment_analysis(article["content"])
        topic = classify_topic(article["content"])

        results.append({
            "title": article["title"],
            "summary": summary,
            "key_points": key_points,
            "sentiment": sentiment,
            "topic": topic,
            "source": article["source"],
            "date": article["date"],
            "url": article["url"]
        })
    return results

if __name__ == "__main__":
    app.run(debug=True)
