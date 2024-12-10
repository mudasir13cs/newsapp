from flask import Flask, request, jsonify, render_template
import torch
import json
from dotenv import load_dotenv
from helper import fetch_article, determine_category, get_feed_url, detect_feed_type, fetch_rss_feed, format_published_date


load_dotenv()

torch.cuda.empty_cache()
app = Flask(__name__)
file_path = 'rss_categories.json'
rss_categories = get_feed_url(file_path)

@app.route('/generate-news', methods=['POST'])
def generate_news():
    user_input = request.json.get('user_input')

    category = determine_category(user_input, rss_categories)
    print(category)

    if category and category in rss_categories:
        print(f"name {category}")
        rss_urls = rss_categories[category]
        generated_articles = []

        for url in rss_urls:
            feed_type = detect_feed_type(url)
            print(f"Feed Type for {url}: {feed_type}")
            
            feed_entries = fetch_rss_feed(url)
            for entry in feed_entries[:]:
                article = {
                    "title": entry.title,
                    "link": entry.link,
                }

                if feed_type == "Atom 1.0":
                    article.update({
                        "image": entry.media_image if hasattr(entry, "media_image") else None,
                        "description": entry.summary if hasattr(entry, "summary") else None,
                        "published": format_published_date(entry.published_parsed) if hasattr(entry, "published_parsed") else "",
                    })
                elif feed_type in ["RSS 2.0", "RSS 1.0", "RSS 0.9"]:
                    article.update({
                        "image": entry.media_image if hasattr(entry, "media_image") else None,
                        "description": entry.description if hasattr(entry, "description") else None,
                        "published": format_published_date(entry.published_parsed) if hasattr(entry, "published_parsed") else "",
                    })
                else:
                    article.update({
                        "description": "Unsupported feed type; limited data available.",
                        "published": "",
                        "image": None,
                    })

                generated_articles.append(article)

        if generated_articles:
            print(generated_articles)
            return jsonify({"category": category, "articles": generated_articles}), 200
        else:
            return jsonify({"error": "No articles found."}), 404
    else:
        return jsonify({"error": "Content not found for the given category."}), 404

@app.route('/article-detail', methods=['POST'])
def article_detail():
    article_link = request.json.get('article_link')

    if not article_link:
        return jsonify({"error": "Article link is required."}), 400
    article_content = fetch_article(article_link)
    if article_content:
        return jsonify({"article": article_content}), 200
    else:
        return jsonify({"error": "Unable to fetch article content."}), 404

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
