import streamlit as st
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import quote
from bs4 import BeautifulSoup, NavigableString
import requests
import google.generativeai as genai
import os

def extract_info(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    original_question = ""

    header = soup.find('div', class_='lia-message-subject').text.strip()

    question = soup.find('div', class_='lia-message-body-content').text.strip()
    original_question = header + " " + question
    # Find comments and kudos counts
    comments = soup.find_all('div', class_='lia-message-body-content')
    kudos_counts = [int(count.text) for count in
                    soup.find_all('span', class_='MessageKudosCount lia-component-kudos-widget-message-kudos-count')]

    # Combine comments and kudos counts into a list of tuples
    comment_kudos = list(zip(comments, kudos_counts))[1:]

    # Sort by kudos count in descending order and extract the 2 most liked comments
    top_comments = sorted(comment_kudos, key=lambda x: x[1], reverse=True)[:2]

    # Extract accepted solutions
    accepted_solutions = []
    for comment in soup.find_all('div', class_='lia-message-body-content')[1:]:
        checkmark_div = comment.find('div', class_='lia-message-body-accepted-solution-checkmark')
        if checkmark_div:
            # Get the parent element containing the checkmark and solution text
            solution_container = checkmark_div.parent

            # Find the iframe element and extract the link
            iframe = solution_container.find('iframe')
            link = iframe.get('src') if iframe else None  # Get link if iframe exists

            # Extract child elements (including text nodes and tags)
            children = list(solution_container.children)

            # Extract text content from child elements
            text_parts = []
            for child in children:
                if isinstance(child, NavigableString):
                    text_parts.append(child.strip())
                elif child.name not in ['iframe', 'br']:
                    text_parts.append(child.text.strip())

                    # Insert the link at the position where the iframe was (if it exists)
            if link:
                # Find the index where the iframe WOULD HAVE BEEN before it was removed
                iframe_index = -1
                for i, child in enumerate(children):
                    if child == iframe:
                        iframe_index = i
                        break

                if iframe_index != -1:
                    text_parts.insert(iframe_index + 1, f"\n\nLink: {link}\n\n")
                else:
                    text_parts.append(f"\n\nLink: {link}\n\n")

                    # Join the text parts to form the final solution text
            solution_text = '\n'.join(text_parts)

            accepted_solutions.append(solution_text)

    return original_question, top_comments, accepted_solutions

def get_top_5_links(search_query):
    """
    Simulates searching for a query and retrieving top 5 page links.
    """
    encoded_query = quote(search_query, safe='')

    # Construct the search URL with the specific format (fixed path)
    simulated_search_url = f"https://help.autodesk.com/view/CIV3D/2024/ENU/?query={encoded_query}"

    try:
        # Set up WebDriver (replace with your actual WebDriver path if needed)
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
        driver.get(simulated_search_url)

        # Wait for the content to load (adjust the wait time as necessary)
        time.sleep(1)  # You might need to adjust this based on page load time

        # Find the element containing the instructions (inspect the page to get the correct selector)
        links = driver.find_elements(By.TAG_NAME, "a")  # Replace with the actual ID or other selector
        top_5_links = [link.get_attribute("href") for link in links[2:7]]

        driver.quit()  # Close the browser
        return top_5_links

    except Exception as e:
        return None

def extract_text_from_autodesk_help(url):
    try:
        # Set up WebDriver (replace with your actual WebDriver path if needed)
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
        driver.get(url)

        # Wait for the content to load (adjust the wait time as necessary)
        time.sleep(1)  # You might need to adjust this based on page load time

        # Find the element containing the instructions (inspect the page to get the correct selector)
        content_element = driver.find_element(By.CLASS_NAME, "caas_body")  # Replace with the actual ID or other selector
        extracted_text = content_element.text

        driver.quit()  # Close the browser
        return extracted_text

    except Exception as e:
        return None

def extract_content_from_autodesk_help(url):
    try:
        # Set up WebDriver
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
        driver.get(url)

        time.sleep(1)  # Adjust wait time as needed

        # Initialize empty lists for different content types
        extracted_text = []
        image_urls = []
        video_urls = []

        # Extract Text
        content_elements = driver.find_elements(By.CLASS_NAME, "caas_body")  # Adjust selector if needed
        for element in content_elements:
            extracted_text.append(element.text)

        # Extract Image URLs (Adjust selectors as needed)
        image_elements = driver.find_elements(By.TAG_NAME, "img")
        for img in image_elements[1:]:
            image_url = img.get_attribute("src")
            if image_url:
                image_urls.append(image_url)

        # Extract Video URLs (Adjust selectors and logic as needed)
        video_elements = driver.find_elements(By.TAG_NAME, "video")  # Or by other element types
        for video in video_elements:
            video_url = video.get_attribute("src")  # Or extract from child elements like 'source'
            if video_url:
                video_urls.append(video_url)

        driver.quit()

        return extracted_text, image_urls, video_urls

    except Exception as e:
        return None, None, None  # Return None for all types on error

def ask_question_on_autodesk_and_generate_prompt(question):
    prompt = ""
    prompt += "Here's some information from 5 different sources. The sources are either the Autodesk Civil 3D documentation or threads from the Civil 3D support forum. Information from the documentation starts with text from article and include links to any images or video in the article. The information from the forum starts with the original question and includes the top 2 most liked responses and the accepted solutions. "
    prompt += f"Use the information given to answer this question: {question}."
    top_5_links = get_top_5_links(search_query=question)
    for link in top_5_links:
        try:
            original_question, top_comments, accepted_solutions = extract_info(link)
            prompt += f"Original question: {original_question} \n"
            prompt += f"Top 2 most liked comments: \n"
            for comment, kudos in top_comments:
                prompt += comment.text.strip()
            prompt += f"Accepted solution(s) \n"
            for solution in accepted_solutions:
                prompt += solution.strip()
        except:
            text, images, videos = extract_content_from_autodesk_help(link)
            if text:
                prompt += f"Text from article:\n"
                for t in text:
                    prompt += t
                    prompt += " "
            if images:
                prompt += f"Link to images in article:\n"
                for img in images:
                    prompt += img
                    prompt += " "
            if videos:
                prompt += f"Link to videos in article:\n"
                for vid in videos:
                    prompt += vid
                    prompt += " "
    prompt = prompt.replace("\n", " ")
    prompt = prompt.replace("\xa0", " ")
    prompt = prompt.replace("\t", "")
    print(prompt)
    return prompt

def ask_gemini(question):
    genai.configure(api_key=os.environ.get('Google_Gemini_API'))
    model = genai.GenerativeModel('gemini-1.5-pro-latest')
    response = model.generate_content(ask_question_on_autodesk_and_generate_prompt(question=question))
    return response

def main():
    st.title("Civil 3D helper tool")

    user_input = st.text_input("Enter your text:")
    submit_button = st.button("Submit")

    if submit_button:
        with st.spinner("Processing..."):
            response = ask_gemini(question=user_input)
        st.write(response)

if __name__ == "__main__":
    main()

