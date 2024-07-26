from youtube_extractor import YouTubeCommentExtractor
from config import API_KEY

if __name__ == "__main__":
    extractor = YouTubeCommentExtractor(API_KEY)
    extractor.run()
