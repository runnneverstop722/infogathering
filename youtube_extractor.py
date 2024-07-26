import requests
import json
import xml.etree.ElementTree as ET
import pandas as pd
from bs4 import BeautifulSoup
from utils import is_valid_url

class YouTubeCommentExtractor:
    def __init__(self, api_key):
        self.api_key = api_key
        self.urls = []

    def get_urls(self):
        print("Enter URLs (separated by commas):")
        url_input = input("URLs: ")
        url_list = [url.strip() for url in url_input.split(',')]
        for url in url_list:
            if is_valid_url(url):
                self.urls.append(url)
            else:
                print(f"Invalid URL: {url}")
        if not self.urls:
            print("No valid URLs entered. Exiting.")
            exit()

    def extract_info(self, url):
        try:
            video_id = url.split('v=')[1].split('&')[0]
            api_url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet&id={video_id}&key={self.api_key}"
            response = requests.get(api_url)
            data = response.json()

            if 'items' in data and len(data['items']) > 0:
                title = data['items'][0]['snippet']['title']
                comments = self.fetch_comments(video_id, title)
                return title, comments
            else:
                print(f"No video found for video ID {video_id}")
                return None, None
        except Exception as e:
            print(f"Error fetching data from {url}: {e}")
            return None, None

    def fetch_comments(self, video_id, title):
        comments = {}
        api_url = f"https://www.googleapis.com/youtube/v3/commentThreads?part=snippet&videoId={video_id}&key={self.api_key}&maxResults=100"
        response = requests.get(api_url)
        data = response.json()

        for item in data['items']:
            comment_id = item['snippet']['topLevelComment']['id']
            comment_text = item['snippet']['topLevelComment']['snippet']['textDisplay']
            like_count = item['snippet']['topLevelComment']['snippet']['likeCount']
            comment_text = comment_text.replace('<br>', '\n')
            clean_comment = BeautifulSoup(comment_text, "html.parser").get_text()
            if comment_id in comments:
                comments[comment_id]['text'] += "\n" + clean_comment
                comments[comment_id]['like_count'] += like_count
            else:
                comments[comment_id] = {'text': clean_comment, 'like_count': like_count, 'title': title}
        return comments

    def categorize_comments(self, comments):
        categories = {
            "Charging": [],
            "Battery": [],
            "EV Service": [],
            "Driving Performance": [],
            "Connected Service": [],
            "Electric device": [],
            "Interior Design": [],
            "Exterior Design": [],
            "NVH Performance": []
        }

        for comment_id, comment_data in comments.items():
            comment = comment_data['text']
            like_count = comment_data['like_count']
            title = comment_data['title']
            if any(keyword in comment.lower() for keyword in ["チャージ", "チャージャー", "Chademo", "充電", "電気", "EV", "バッテリー"]):
                categories["Charging"].append((title, comment, like_count))
            if any(keyword in comment.lower() for keyword in ["バッテリー", "Battery"]):
                categories["Battery"].append((title, comment, like_count))
            if any(keyword in comment.lower() for keyword in ["V2H", "H2V"]):
                categories["EV Service"].append((title, comment, like_count))
            if any(keyword in comment.lower() for keyword in ["加速", "減速", "走行", "巡航", "追い越し", "高速", "中速", "低速", "ワインディング"]):
                categories["Driving Performance"].append((title, comment, like_count))
            if any(keyword in comment.lower() for keyword in ["app", "アプリ", "メルセデスミー", "MercedesMe", "メルセデスMe", "コネクテッド", "Connected", "リモート", "Remote"]):
                categories["Connected Service"].append((title, comment, like_count))
            if any(keyword in comment.lower() for keyword in ["navi", "ナビ", "電子デバイス", "スクリーン", "液晶"]):
                categories["Electric device"].append((title, comment, like_count))
            if any(keyword in comment.lower() for keyword in ["インテリア", "室内", "車内", "狭い", "広い", "質感", "パネル", "ボタン", "タッチ"]):
                categories["Interior Design"].append((title, comment, like_count))
            if any(keyword in comment.lower() for keyword in ["エクステリア", "デザイン", "外見", "ボディ", "全幅", "サイズ", "ダサ", "かっこ", "格好"]):
                categories["Exterior Design"].append((title, comment, like_count))
            if any(keyword in comment.lower() for keyword in ["ノイズ", "振動", "インバーター", "高周波", "異音"]):
                categories["NVH Performance"].append((title, comment, like_count))

        return categories

    def create_xml(self, categories):
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

    def create_csv(self, categories):
        rows = []
        for category, comments in categories.items():
            for title, comment, like_count in comments:
                rows.append([title, category, comment, like_count])
        df = pd.DataFrame(rows, columns=["Title", "Category", "Comment", "LikeCount"])
        df.to_csv("output.csv", index=False, encoding="utf-8")

    def run(self):
        self.get_urls()
        output_format = input("Enter output format (csv, xml): ").lower()
        all_comments = {}
        for url in self.urls:
            title, comments = self.extract_info(url)
            if title:
                for comment_id, comment_data in comments.items():
                    all_comments[comment_id] = comment_data
        if all_comments:
            categories = self.categorize_comments(all_comments)
            if output_format == "xml":
                self.create_xml(categories)
            elif output_format == "csv":
                self.create_csv(categories)
            else:
                print("Invalid output format. Please choose from 'csv' or 'xml'.")
            for category, comments in categories.items():
                print(f"{category}: {len(comments)} comments")
