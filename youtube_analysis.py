import pandas as pd
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googletrans import Translator
from tqdm import tqdm
from config import API_KEY, VIDEO_IDS, MODEL_NAMES

class YouTubeCommentAnalyzer:
    def __init__(self, api_key):
        self.youtube = build('youtube', 'v3', developerKey=api_key)
        self.translator = Translator()

    def get_video_title(self, video_id):
        try:
            response = self.youtube.videos().list(
                part='snippet',
                id=video_id
            ).execute()
            title = response['items'][0]['snippet']['title']
            return title
        except HttpError as e:
            print(f"An HTTP error {e.resp.status} occurred:\n{e.content}")
            return None

    def get_comments(self, video_id):
        comments = []
        title = self.get_video_title(video_id)
        model_name = self.extract_model_name(title)
        try:
            results = self.youtube.commentThreads().list(
                part='snippet',
                videoId=video_id,
                textFormat='plainText',
                maxResults=100
            ).execute()
            
            while results:
                for item in results['items']:
                    snippet = item['snippet']['topLevelComment']['snippet']
                    comment = snippet['textDisplay'].replace("\n", " ")
                    like_count = snippet.get('likeCount', 0)
                    comments.append((model_name, comment, like_count))
                if 'nextPageToken' in results:
                    results = self.youtube.commentThreads().list(
                        part='snippet',
                        videoId=video_id,
                        textFormat='plainText',
                        pageToken=results['nextPageToken'],
                        maxResults=100
                    ).execute()
                else:
                    break
        except HttpError as e:
            print(f"An HTTP error {e.resp.status} occurred:\n{e.content}")
        return comments

    def extract_model_name(self, title):
        for model in MODEL_NAMES:
            if model in title:
                return model
        if "Mercedes Me" in title:
            return "Mercedes Me app"
        return "Other"

    def filter_comments(self, comments):
        return [c for c in comments if len(c[1].split()) > 2]

    def translate_comments(self, comments):
        translated_comments = []
        for model_name, comment, like_count in tqdm(comments, desc="Translating comments"):
            try:
                translated = self.translator.translate(comment, dest='en')
                translated_comments.append((model_name, translated.text, like_count))
            except Exception as e:
                print(f"Translation error: {e}")
        return translated_comments

    def save_comments_to_csv(self, video_comments, file_path):
        df = pd.DataFrame(video_comments, columns=['Model Name', 'Comment', 'LikeCount'])
        df.to_csv(file_path, index=False)

    def analyze_comments(self, comments):
        impressions = {
            'positive': {'good': 0, 'better': 0, 'best': 0},
            'negative': {'bad': 0, 'worse': 0, 'worst': 0},
            'neutral': 0
        }
        total_comments = len(comments)
        keywords = {
            'design': [],
            'performance': [],
            'connectivity': [],
            'positive': [],
            'negative': [],
            'neutral': [],
            'others': []
        }
        for model_name, comment, like_count in comments:
            if 'good' in comment:
                impressions['positive']['good'] += 1
                keywords['positive'].append((model_name, comment, like_count))
            elif 'better' in comment:
                impressions['positive']['better'] += 1
                keywords['positive'].append((model_name, comment, like_count))
            elif 'best' in comment:
                impressions['positive']['best'] += 1
                keywords['positive'].append((model_name, comment, like_count))
            elif 'bad' in comment:
                impressions['negative']['bad'] += 1
                keywords['negative'].append((model_name, comment, like_count))
            elif 'worse' in comment:
                impressions['negative']['worse'] += 1
                keywords['negative'].append((model_name, comment, like_count))
            elif 'worst' in comment:
                impressions['negative']['worst'] += 1
                keywords['negative'].append((model_name, comment, like_count))
            else:
                impressions['neutral'] += 1
                keywords['neutral'].append((model_name, comment, like_count))
            
            if 'design' in comment:
                keywords['design'].append((model_name, comment, like_count))
            if 'performance' in comment:
                keywords['performance'].append((model_name, comment, like_count))
            if 'connectivity' in comment or 'app' in comment:
                keywords['connectivity'].append((model_name, comment, like_count))
            else:
                keywords['others'].append((model_name, comment, like_count))
        
        return impressions, keywords, total_comments

    def create_insights_dataframes(self, model_name, impressions, keywords, total_comments):
        insights_data = []

        for key, key_comments in keywords.items():
            if key in ['positive', 'negative', 'neutral']:
                continue
            percentage = (len(key_comments) / total_comments) * 100
            insights_data.append({
                'Aspect': key,
                'Percentage': f"{percentage:.1f}%",
                'Positive': "\n".join([comment for _, comment, _ in key_comments if 'good' in comment or 'better' in comment or 'best' in comment]),
                'Negative': "\n".join([comment for _, comment, _ in key_comments if 'bad' in comment or 'worse' in comment or 'worst' in comment]),
                'Neutral': "\n".join([comment for _, comment, _ in key_comments if 'good' not in comment and 'better' not in comment and 'best' not in comment and 'bad' not in comment and 'worse' not in comment and 'worst' not in comment])
            })
        
        impressions_df = pd.DataFrame([
            {'Subject': f'Impressions of {model_name}'},
            {'Impression': 'Positive', 'Category': 'Good', 'Count': impressions['positive']['good'], 'Percentage': f"{(impressions['positive']['good'] / total_comments) * 100:.1f}%"},
            {'Impression': 'Positive', 'Category': 'Better', 'Count': impressions['positive']['better'], 'Percentage': f"{(impressions['positive']['better'] / total_comments) * 100:.1f}%"},
            {'Impression': 'Positive', 'Category': 'Best', 'Count': impressions['positive']['best'], 'Percentage': f"{(impressions['positive']['best'] / total_comments) * 100:.1f}%"},
            {'Impression': 'Negative', 'Category': 'Bad', 'Count': impressions['negative']['bad'], 'Percentage': f"{(impressions['negative']['bad'] / total_comments) * 100:.1f}%"},
            {'Impression': 'Negative', 'Category': 'Worse', 'Count': impressions['negative']['worse'], 'Percentage': f"{(impressions['negative']['worse'] / total_comments) * 100:.1f}%"},
            {'Impression': 'Negative', 'Category': 'Worst', 'Count': impressions['negative']['worst'], 'Percentage': f"{(impressions['negative']['worst'] / total_comments) * 100:.1f}%"},
            {'Impression': 'Neutral', 'Count': impressions['neutral'], 'Percentage': f"{(impressions['neutral'] / total_comments) * 100:.1f}%"}
        ])

        detailed_insights_df = pd.DataFrame(insights_data)
        
        return impressions_df, detailed_insights_df

    def save_to_excel(self, file_path, video_comments, all_model_data):
        with pd.ExcelWriter(file_path) as writer:
            df = pd.DataFrame(video_comments, columns=['Model Name', 'Comment', 'LikeCount'])
            df.to_excel(writer, sheet_name='Raw comments', index=False)
            for model_name, (impressions_df, detailed_insights_df) in all_model_data.items():
                impressions_df.to_excel(writer, sheet_name=f'{model_name} Impressions', index=False)
                detailed_insights_df.to_excel(writer, sheet_name=f'{model_name} Detailed Insights', index=False)

def main():
    analyzer = YouTubeCommentAnalyzer(API_KEY)
    
    video_comments = []

    for video_id in tqdm(VIDEO_IDS, desc="Processing videos"):
        comments = analyzer.get_comments(video_id)
        filtered_comments = analyzer.filter_comments(comments)
        translated_comments = analyzer.translate_comments(filtered_comments)
        for model_name, comment, like_count in translated_comments:
            video_comments.append([model_name, comment, like_count])

    all_model_data = {}
    for model_name in MODEL_NAMES + ['Mercedes Me app', 'Other']:
        model_comments = [(mn, c, lc) for mn, c, lc in video_comments if mn == model_name]
        if model_comments:
            impressions, keywords, total_comments = analyzer.analyze_comments(model_comments)
            impressions_df, detailed_insights_df = analyzer.create_insights_dataframes(model_name, impressions, keywords, total_comments)
            all_model_data[model_name] = (impressions_df, detailed_insights_df)
    
    # Add insights for 'Mercedes Me'
    mercedes_me_comments = [(mn, c, lc) for mn, c, lc in video_comments if 'connectivity' in c or 'app' in c or mn == 'Mercedes Me app']
    if mercedes_me_comments:
        impressions, keywords, total_comments = analyzer.analyze_comments(mercedes_me_comments)
        impressions_df, detailed_insights_df = analyzer.create_insights_dataframes('Mercedes Me', impressions, keywords, total_comments)
        all_model_data['Mercedes Me'] = (impressions_df, detailed_insights_df)
    
    excel_file_path = 'youtube_analysis_results.xlsx'
    analyzer.save_to_excel(excel_file_path, video_comments, all_model_data)
    
    print(f"Analysis results saved to {excel_file_path}")

if __name__ == "__main__":
    main()
