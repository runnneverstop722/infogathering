import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import xml.etree.ElementTree as ET

# Step 1: User input and URL handling
urls = []  # Store user-entered URLs here

# Step 2: Extract information from URLs
def extract_info(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Step 3: Specific information extraction
        title = soup.title.string.strip()

        # Example: Extract comments (modify as needed)
        comments = [comment.text.strip() for comment in soup.find_all('div', class_='comment')]

        # Example: Extract keywords (modify as needed)
        keywords = ['keyword1', 'keyword2']

        return title, comments, keywords
    except Exception as e:
        print(f"Error fetching data from {url}: {e}")
        return None, None, None

# Step 4: Export to XML
def create_xml(title, comments, keywords):
    root = ET.Element("data")
    ET.SubElement(root, "title").text = title
    for comment in comments:
        ET.SubElement(root, "comment").text = comment
    for keyword in keywords:
        ET.SubElement(root, "keyword").text = keyword
    tree = ET.ElementTree(root)
    tree.write("output.xml")

# Step 5: Share via email
def send_email(recipients):
    sender_email = "your_email@example.com"
    subject = "Web Scraping Results"
    body = "Please find the attached XML file."

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = ", ".join(recipients)
    msg['Subject'] = subject

    with open("output.xml", "rb") as attachment:
        part = MIMEText(body, "plain")
        msg.attach(part)

        part = MIMEText(attachment.read(), "xml")
        part.add_header('Content-Disposition', 'attachment', filename="output.xml")
        msg.attach(part)

    # Send email using smtplib (configure SMTP server details)

# Example usage:
if __name__ == "__main__":
    url1 = "https://example.com/page1"
    url2 = "https://example.com/page2"
    urls.extend([url1, url2])

    for url in urls:
        title, comments, keywords = extract_info(url)
        if title:
            create_xml(title, comments, keywords)

    recipients = ["recipient1@example.com", "recipient2@example.com"]
    send_email(recipients)