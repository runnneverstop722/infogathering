import re

def is_valid_url(url):
    regex = re.compile(
        r'^(https?://)?(www\.)?(youtube\.com|youtu\.?be)/.+$'
    )
    return re.match(regex, url) is not None
