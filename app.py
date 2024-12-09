import feedparser
from newspaper import Article
from transformers import pipeline, AutoTokenizer
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# Set up the Phi-3 pipeline
model = "microsoft/Phi-3.5-mini-instruct"
tokenizer = AutoTokenizer.from_pretrained(model)
pipe = pipeline(
    "text-generation",
    model=model,
    tokenizer=tokenizer,
    device=0  # Use appropriate device (0 for GPU, -1 for CPU)
)

# Define categories and their corresponding RSS feeds
rss_categories = {
    "Technology": [
        "https://rss.cnn.com/rss/cnn_tech.rss",
        "https://feeds.bbci.co.uk/news/technology/rss.xml"
    ],
    "Sports": [
        "https://rss.cnn.com/rss/cnn_sport.rss",
        "https://feeds.bbci.co.uk/sport/rss.xml"
    ],
    "News": [
        "https://rss.cnn.com/rss/cnn_topstories.rss",
        "https://feeds.bbci.co.uk/news/rss.xml"
    ],
    "Pakistan": [
        "https://www.dawn.com/rss",
        "https://www.geo.tv/rss"
    ],
}

# Function to fetch RSS feed
def fetch_rss_feed(url):
    feed = feedparser.parse(url)
    return feed.entries

# Function to extract content from article URL
def fetch_article_content(url):
    article = Article(url)
    article.download()
    article.parse()
    return article.text

# Function to generate news article from content
def generate_article(content):
    prompt = f"Write a detailed news article based on the following content: {content}"
    result = pipe(prompt, max_new_tokens=500, temperature=0.7, do_sample=True)
    return result[0]['generated_text']

# Function to determine category based on user input
def determine_category(user_input):
    # Simple category matching based on keywords (could be extended)
    if "sport" in user_input.lower() or "sports" in user_input.lower():
        return "Sports"
    elif "pakistan" in user_input.lower():
        return "Pakistan"
    elif "technology" in user_input.lower():
        return "Technology"
    elif "news" in user_input.lower() or "update" in user_input.lower():
        return "News"
    else:
        return None  # No match found

# Route to handle user input and generate news articles
@app.route('/generate-news', methods=['POST'])
def generate_news():
    # Get the user's text input
    user_input = request.json.get('user_input')

    # Determine the category based on user input
    category = determine_category(user_input)

    if category and category in rss_categories:
        # Fetch the RSS feed URLs for the category
        rss_urls = rss_categories[category]

        # Fetch and generate articles for the category
        generated_articles = []
        for url in rss_urls:
            feed_entries = fetch_rss_feed(url)
            for entry in feed_entries:
                article_content = fetch_article_content(entry.link)
                generated_article = generate_article(article_content)
                generated_articles.append(generated_article)

        # Return the generated articles as a JSON response
        return jsonify({"category": category, "articles": generated_articles}), 200
    else:
        # If no match found, return an error
        return jsonify({"error": "Content not found for the given category."}), 404

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
