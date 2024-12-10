import feedparser
from newspaper import Article
from transformers import pipeline, AutoTokenizer
from flask import Flask, request, jsonify, render_template
import torch
import json
from dotenv import load_dotenv
import os
from datetime import datetime
import nltk



cache_dir = os.getenv("CACHE_DIR", "/home/user/.cache/huggingface/hub") 

model = os.getenv("MODEL", "microsoft/Phi-3.5-mini-instruct")
tokenizer = AutoTokenizer.from_pretrained(model, cache_dir=cache_dir)
action = os.getenv("MODEL_ACTION", "text-generation")
pipe = pipeline(
    action,
    model=model,
    tokenizer=tokenizer,
    device_map="auto",
    trust_remote_code=True
)

# Function to extract content from article URL
def fetch_article_content(url):
    try:
        article = Article(url)
        article.download()
        article.parse()
        return article.text
    except Exception as e:
        return f"Error fetching article content: {str(e)}"
    
    
def fetch_article(url):
    try:
        article = Article(url)
        article.download()
        article.parse()
        # article.nlp()
        # generate_article()
        return {
            "title":article.title,
            "authors": article.authors, 
            "published":  article.publish_date,
            "description": article.text,
            "image":article.top_image,
            "movies":article.movies,
            "link":url,
          #  "keywords":article.keywords,
           # "summary":article.summary
            }
    except Exception as e:
        return f"Error fetching article content: {str(e)}"
    
    

# Function to fetch RSS feed
def fetch_rss_feed(url):
    feed = feedparser.parse(url)
    return feed.entries


# Function to generate news article from content
def generate_article(content):
    prompt = (
        "Generate a detailed and well-structured news article using HTML tags for formatting. Include only the content that belongs inside the <body> tag. Use <h1> for the main title, <h2> for subheadings, <p> for paragraphs, and <ul> or <ol> for lists where necessary. Focus on creating professional, engaging, and informative content based on the input below." 
        "Do not explicitly reference or include the input content directly; instead, use it as inspiration to craft original content. Return only the HTML body content."
        f"Input content: {content}"
        "Output: Return only the content within the <body>. also do not include ```html"
    )
    messages = [
        {"role": "user", "content": prompt}
    ]
    
    generation_args = {
        "max_new_tokens": 500,
        "return_full_text": False,
        "temperature": 0.0,
        "do_sample": False,
    }
    
    try:
        result = pipe(messages, **generation_args) 
        return result[0]['generated_text']
    except Exception as e:
        return f"Error generating article: {str(e)}"

def determine_category(user_input, rss_categories):
    categories = list(rss_categories.keys())

    categories_text = ', '.join(categories)
    prompt = (
        f"Classify the following user input into one of these categories: {categories_text}."
        "Return only the category name, and if the input doesn't relate to any category, return an empty string ('')."
        "Do not include any additional explanation or context."
        f"User Input: {user_input}"
    )
    
    messages = [
        {"role": "user", "content": prompt}
    ]

    generation_args = {
        "max_new_tokens": 50,
        "return_full_text": False,
        "temperature": 0.0,
        "do_sample": False,
    }
    result = pipe(messages, **generation_args) 
    generated_text = result[0]['generated_text']
    print(f"Model output: {generated_text}")
    for category in categories:
        if category.lower().strip() == generated_text.lower().strip():
            return category
    return None

def format_published_date(published_parsed):
    if published_parsed:
        try:
            dt = datetime(*published_parsed[:6]) 
            return dt.strftime("%Y-%m-%d %H:%M:%S") 
        except Exception as e:
            print(f"Error formatting date: {e}")
            return ""
    return ""

def get_feed_url(file_path):
    # Check if the file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file at {file_path} does not exist.")
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except json.JSONDecodeError:
        raise ValueError(f"Error decoding JSON from the file at {file_path}.")
    except Exception as e:
        raise Exception(f"An error occurred: {str(e)}")

def detect_feed_type(feed_url):
    feed = feedparser.parse(feed_url)
    if feed.version == "atom10":
        return "Atom 1.0"
    elif feed.version == "rss20":
        return "RSS 2.0"
    elif feed.version == "rss10":
        return "RSS 1.0"
    elif feed.version == "rss09":
        return "RSS 0.9"
    else:
        return "Unknown or unsupported feed type"    