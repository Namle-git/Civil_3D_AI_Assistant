import streamlit as st
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import quote
from bs4 import BeautifulSoup, NavigableString
import requests
from openai import OpenAI
import os
import logging

logging.basicConfig(level=logging.INFO)


def extract_info(url):
    """
        Extracts the original question, top comments, and accepted solutions from a given Civil 3D forum page URL.

        Args:
            url (str): The URL of the forum page to extract information from.

        Returns:
            tuple: A tuple containing:
                - original_question (str): The combined header and body of the original question.
                - top_comments (list of tuples): A list of the top two comments with their kudos counts.
                - accepted_solutions (list of str): A list of accepted solutions with their links (if any).

        Raises:
            requests.RequestException: If there is an issue with the network request.
    """
    try:
        # Send a GET request to the specified URL
        response = requests.get(url)
        response.raise_for_status()  # Raise an HTTPError for bad responses
    except requests.RequestException as e:
        raise requests.RequestException(f"Failed to retrieve the page: {e}")

    # Parse the content of the response with BeautifulSoup
    soup = BeautifulSoup(response.content, 'html.parser')

    # Extract the header (subject) of the original question
    header = soup.find('div', class_='lia-message-subject').text.strip()

    # Extract the body content of the original question
    question = soup.find('div', class_='lia-message-body-content').text.strip()

    # Combine the header and the body to form the full original question
    original_question = header + " " + question

    # Find all comments on page
    comments = soup.find_all('div', class_='lia-message-body-content')

    # Extract the kudos counts for each comment
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

            # Append the solution text to the list of accepted solutions
            accepted_solutions.append(solution_text)

    # Return the original question, top comments, and accepted solutions
    return original_question, top_comments, accepted_solutions


def get_top_5_links(search_query):
    """
       Simulates a search for a query on the Autodesk Civil 3D 2024 Help page and retrieves the top 5 pages links.

       Args:
           search_query (str): The search query string.

       Returns:
           list: A list of the top 5 links (str) from the search results.

       Raises:
           Exception: If there is an issue with the web scraping process.
       """
    # Encode the search query to be URL-safe
    encoded_query = quote(search_query, safe='')

    # Construct the search URL with the specific format (fixed path)
    simulated_search_url = f"https://help.autodesk.com/view/CIV3D/2024/ENU/?query={encoded_query}"

    try:
        # Set up Chrome options for headless mode
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        # Set up WebDriver
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        driver.get(simulated_search_url)

        # Wait for the content to load
        time.sleep(1)

        # Find the element containing the instructions (inspect the page to get the correct selector)
        links = driver.find_elements(By.TAG_NAME, "a")  # Replace with the actual ID or other selector
        top_5_links = [link.get_attribute("href") for link in links[2:7]]

        driver.quit()  # Close the browser
        return top_5_links

    except Exception as e:
        logging.info(f"An error occurred: {e}")
        return None


def extract_text_from_autodesk_help(url):
    """
        Extracts text content from a Civil 3D documentation page.

        Args:
            url (str): The URL of the Autodesk help page.

        Returns:
            str: The extracted text content from the page.

        Raises:
            Exception: If there is an issue with the web scraping process.
        """
    try:
        # Set up Chrome options for headless mode
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        # Set up WebDriver
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        driver.get(url)

        # Wait for the content to load
        time.sleep(1)

        # Find the element containing the instructions (inspect the page to get the correct selector)
        content = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "caas_body"))
        )
        extracted_text = content.text

        driver.quit()  # Close the browser
        return extracted_text

    except Exception as e:
        logging.info(f"An error occurred: {e}")
        return None


def extract_content_from_autodesk_help(url):
    """
        Extracts text, image URLs, and video URLs from a Civil 3D documentation page.

        Args:
            url (str): The URL of the Autodesk help page.

        Returns:
            tuple: A tuple containing:
                - extracted_text (list of str): List of text content from the page.
                - image_urls (list of str): List of image URLs from the page.
                - video_urls (list of str): List of video URLs from the page.

        Raises:
            Exception: If there is an issue with the web scraping process.
        """
    try:
        # Set up Chrome options for headless mode
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        # Set up WebDriver
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        driver.get(url)

        # Wait for the content to load
        time.sleep(1)

        image_urls = []
        video_urls = []

        # Extract Text
        content = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "caas_body"))
        )
        extracted_text = content.text

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

        driver.quit()  # Close the browser

        return extracted_text, image_urls, video_urls

    except Exception as e:
        logging.info(f"An error occurred: {e}")
        return None, None, None  # Return None for all types on error


def ask_question_on_autodesk_and_generate_prompt(question):
    """
       Generates a prompt using information from Autodesk Civil 3D documentation and forum based on a given question.

       Args:
           question (str): The question to search for.

       Returns:
           str: The generated prompt with information from documentation and forum.
       """
    # Start the prompt with a fixed text
    prompt = ("Here's some information from 5 different sources. The sources are either the Autodesk Civil 3D "
              "documentation or threads from the Civil 3D support forum. Information from the documentation starts "
              "with text from article and include links to any images or video in the article. The information from "
              "the forum starts with the original question and includes the top 2 most liked responses and the "
              "accepted solutions. The most relevant text are at the start of the prompt.")
    # Add the user question to the prompt
    prompt += f"Use the information given to answer this question: {question}"

    # Get the top 5 links and iterate through them to extract their information then structurally
    # adding the information into the prompt
    retry = True
    attempts = 0
    max_attempts = 2
    while retry and attempts < max_attempts:
        try:
            top_5_links = get_top_5_links(search_query=question)
            retry = False  # If the function succeeds, stop retrying
        except Exception as e:
            attempts += 1
            time.sleep(1)
            logging.info(f"Top 5 links attempt {attempts} failed: {e}")
            if attempts >= max_attempts:
                logging.info("Max attempts reached. Exiting.")
            else:
                logging.info("Retrying...")
    for link in top_5_links:
        # Try to extract the page as if it's a forum page
        try:
            original_question, top_comments, accepted_solutions = extract_info(link)
            prompt += f"\n"
            prompt += f"**Original question**: {original_question} \n"
            prompt += f"**Top most liked comments**: \n"
            for comment, kudos in top_comments:
                prompt += comment.text.strip()
            prompt += f"\n**Accepted solution(s)** \n"
            for solution in accepted_solutions:
                prompt += solution.strip()
        # If the page does not contain forum information, extract it as a documentation page
        except:
            text, images, videos = extract_content_from_autodesk_help(link)
            if text:
                prompt += f"\n**Text from article**:\n"
                prompt += text
            if images:
                prompt += f"\n**Link to images in article**:\n"
                for img in images:
                    prompt += img
                    prompt += " "
            if videos:
                prompt += f"\n**Link to videos in article**:\n"
                for vid in videos:
                    prompt += vid
                    prompt += " "
    prompt = prompt.replace("\xa0", " ")
    prompt = prompt.replace("\t", "")
    prompt = prompt.replace("Solved!\n\nGo to Solution.", "")
    prompt = prompt.replace("\n\n\n\n", "")
    logging.info(prompt)
    return prompt


def ask_gpt_4o(question):
    """
        Sends the prompt to the GPT-4 model and returns the response.

        Args:
            question (str): The prompt to inject into the GPT-4 model.

        Returns:
            dict: The response from the GPT-4 model.

        Raises:
            Exception: If there is an issue with the API request.
        """
    # Initiate the OpenAI client

    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    # Generate the prompt using the provided question and send the request to the GPT-4o model
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": ask_question_on_autodesk_and_generate_prompt(question=question),
            }
        ],
    )
    return response


def main():
    # Initiate a container
    with st.container():
        # Display the asistant's name
        st.title("Civil 3D AI Assistant")
        st.write("This is an independent application and is not in any way associated with Autodesk")

        # Get the question from the user
        user_input = st.text_input("Enter your text:")
        submit_button = st.button("Submit")

        # Generate the prompt and inject it into GPT 4o
        if submit_button or user_input:
            with st.spinner("Processing..."):
                response = ask_gpt_4o(question=user_input)
            # Display the generated response
            st.write("This response is AI generated . Please use it at your own risk")
            st.write(response.choices[0].message.content)
            

if __name__ == "__main__":
    main()
