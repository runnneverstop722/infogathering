import requests
import json
import xml.etree.ElementTree as ET
import pandas as pd
from bs4 import BeautifulSoup
from config import API_KEY  # Import the API key from config.py
import re

# Step 1: User input and URL handling
urls = []  # Store user-entered URLs here
api_key = API_KEY  # Use the imported API key

# Function to validate URLs
def is_valid_url(url):
    regex = re.compile(
        r'^(https?://)?(www\.)?(youtube\.com|youtu\.?be)/.+$'
    )
    return re.match(regex, url) is not None

# Prompt user to enter URLs
print("Enter URLs (separated by commas):")
url_input = input("URLs: ")
url_list = [url.strip() for url in url_input.split(',')]

# Validate and add URLs to the list
for url in url_list:
    if is_valid_url(url):
        urls.append(url)
    else:
        print(f"Invalid URL: {url}")

if not urls:
    print("No valid URLs entered. Exiting.")
    exit()

# Step 2: Extract information from URLs
def extract_info(url, api_key):
    try:
        video_id = url.split('v=')[1].split('&')[0]  # Extract video ID
        api_url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet&id={video_id}&key={api_key}"
        response = requests.get(api_url)
        data = response.json()

        # Check if the response contains the expected fields
        if 'items' in data and len(data['items']) > 0:
            title = data['items'][0]['snippet']['title']
            comments = {}  # Use a dictionary to store comments by their ID

            # Fetch comments
            api_url = f"https://www.googleapis.com/youtube/v3/commentThreads?part=snippet&videoId={video_id}&key={api_key}&maxResults=100"
            response = requests.get(api_url)
            data = response.json()

            for item in data['items']:
                comment_id = item['snippet']['topLevelComment']['id']
                comment_text = item['snippet']['topLevelComment']['snippet']['textDisplay']
                like_count = item['snippet']['topLevelComment']['snippet']['likeCount']
                # Replace <br> tags with newline characters
                comment_text = comment_text.replace('<br>', '\n')
                # Clean the comment text
                clean_comment = BeautifulSoup(comment_text, "html.parser").get_text()
                if comment_id in comments:
                    comments[comment_id]['text'] += "\n" + clean_comment
                    comments[comment_id]['like_count'] += like_count
                else:
                    comments[comment_id] = {'text': clean_comment, 'like_count': like_count, 'title': title}
            return title, comments
        else:
            print(f"No video found for video ID {video_id}")
            return None, None
    except Exception as e:
        print(f"Error fetching data from {url}: {e}")
        return None, None

# Step 3: Categorize comments
def categorize_comments(comments):
    categories = {
        "EV Performance": [],
        "Connected Service": [],
        "Interior Design": [],
        "Exterior Design": [],
        "Driving Performance": [],
        "Fuel-efficient Performance": [],
        "NVH Performance": []
    }

    for comment_id, comment_data in comments.items():
        comment = comment_data['text']
        like_count = comment_data['like_count']
        title = comment_data['title']
        if any(keyword in comment.lower() for keyword in ["チャージ", "チャージャー", "Chademo", "充電器", "充電", "電気", "EV", "バッテリー", "V2H", "H2V"]):
            categories["EV Performance"].append((title, comment, like_count))
        if any(keyword in comment.lower() for keyword in ["app", "アプリ", "Mercedes me", "メルセデスMe", "コネクテッド", "Connected"]):
            categories["Connected Service"].append((title, comment, like_count))
        if any(keyword in comment.lower() for keyword in ["インテリア", "室内", "狭い", "質感"]):
            categories["Interior Design"].append((title, comment, like_count))
        if any(keyword in comment.lower() for keyword in ["エクステリア", "外見", "ボディ", "塗装", "ステップ"]):
            categories["Exterior Design"].append((title, comment, like_count))
        if any(keyword in comment.lower() for keyword in ["加速", "減速", "走行", "巡航", "追い越し", "高速", "低速", "ワインディング"]):
            categories["Driving Performance"].append((title, comment, like_count))
        if any(keyword in comment.lower() for keyword in ["燃費"]):
            categories["Fuel-efficient Performance"].append((title, comment, like_count))
        if any(keyword in comment.lower() for keyword in ["ノイズ", "振動"]):
            categories["NVH Performance"].append((title, comment, like_count))

    return categories

# Step 4: Export to XML
def create_xml(categories):
    root = ET.Element("data")
    for category, comments in categories.items():
        category_element = ET.SubElement(root, "category", name=category)
        ET.SubElement(category_element, "commentCount").text = str(len(comments))
        for title, comment, like_count in comments:
            comment_element = ET.SubElement(category_element, "comment")
            ET.SubElement(comment_element, "title").text = title
            comment_element.text = comment
            ET.SubElement(comment_element, "likeCount").text = str(like_count)
    tree = ET.ElementTree(root)
    tree.write("output.xml", encoding="utf-8", xml_declaration=True)

# Step 4: Export to CSV
def create_csv(categories):
    rows = []
    for category, comments in categories.items():
        for title, comment, like_count in comments:
            rows.append([title, category, comment, like_count])
    df = pd.DataFrame(rows, columns=["Title", "Category", "Comment", "LikeCount"])
    df.to_csv("output.csv", index=False, encoding="utf-8")

# Step 4: Export to XLSX
def create_xlsx(categories):
    rows = []
    for category, comments in categories.items():
        for title, comment, like_count in comments:
            rows.append([title, category, comment, like_count])
    df = pd.DataFrame(rows, columns=["Title", "Category", "Comment", "LikeCount"])
    df.to_excel("output.xlsx", index=False, engine='openpyxl')

# Example usage:
if __name__ == "__main__":
    output_format = input("Enter output format (csv, xlsx, xml): ").lower()
    all_comments = {}
    for url in urls:
        title, comments = extract_info(url, api_key)
        if title:
            for comment_id, comment_data in comments.items():
                all_comments[comment_id] = comment_data
    if all_comments:
        categories = categorize_comments(all_comments)
        if output_format == "xml":
            create_xml(categories)
        elif output_format == "csv":
            create_csv(categories)
        elif output_format == "xlsx":
            create_xlsx(categories)
        else:
            print("Invalid output format. Please choose from 'csv', 'xlsx', or 'xml'.")
        # Print the number of comments per category
        for category, comments in categories.items():
            print(f"{category}: {len(comments)} comments")
