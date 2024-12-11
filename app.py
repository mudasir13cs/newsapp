from flask import Flask, request, jsonify, render_template
import torch
import json
from dotenv import load_dotenv
from helper import fetch_article, determine_category, get_feed_url, detect_feed_type, fetch_rss_feed, extract_image_from_description, format_published_date


load_dotenv()

torch.cuda.empty_cache()
app = Flask(__name__)
file_path = 'rss_categories.json'
rss_categories = get_feed_url(file_path)

@app.route('/generate-news', methods=['POST'])
def generate_news():
    user_input = request.json.get('user_input')
    
    isDescription = request.json.get('description') if hasattr(request.json, "description") else True
    
    

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
                description = None
                article = {
                    "title": entry.title,
                    "link": entry.link,
                }

                if feed_type == "Atom 1.0":
                    if isDescription :
                        description = entry.summary if hasattr(entry, "summary") else None
                    
                    article.update({
                        "image": entry.media_image if hasattr(entry, "media_image") else extract_image_from_description(entry.summary if hasattr(entry, "summary") else None),
                        "description": description,
                        "published": format_published_date(entry.published_parsed) if hasattr(entry, "published_parsed") else "",
                    })
                elif feed_type in ["RSS 2.0", "RSS 1.0", "RSS 0.9"]:
                    if isDescription :
                        description = entry.summary if hasattr(entry, "summary") else None
                        
                    article.update({
                        "image": entry.media_image if hasattr(entry, "media_image") else extract_image_from_description(entry.summary if hasattr(entry, "summary") else None),
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
            return jsonify({"data":{"category": category, "articles": generated_articles}, "message": "Success.",  "isSuccess": True}), 200
        else:
            return jsonify({"message": "No articles found.", "isSuccess": False}), 200
    else:
        return jsonify({"message": "Content not found for the given context.", "isSuccess": False}), 200

@app.route('/article-detail', methods=['POST'])
def article_detail():
    article_link = request.json.get('article_link')

    if not article_link:
        return jsonify({"message": "Article link is required.", "isSuccess": False}), 200
    article_content = fetch_article(article_link)
    if article_content:
        return jsonify({"data":{"article": article_content},  "message": "Success.", "isSuccess": True}), 200
    else:
        return jsonify({"message": "Unable to fetch article content.", "isSuccess": False}), 200

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
