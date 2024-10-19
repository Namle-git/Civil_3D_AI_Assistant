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
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential
from azure.ai.contentsafety import ContentSafetyClient
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import HttpResponseError
from azure.ai.contentsafety.models import AnalyzeTextOptions, TextCategory
import os
import logging

logging.basicConfig(level=logging.INFO)


def extract_forum_info(url):
    """
        Extracts the original question, and accepted solutions from a given Civil 3D forum page URL.

        Args:
            url (str): The URL of the forum page to extract information from.

        Returns:
            tuple: A tuple containing:
                - original_question (str): The combined header and body of the original question.
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

    try:
        # Parse the content of the response with BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')
        
        header = soup.find('h2', class_='PageTitle lia-component-common-widget-page-title').text.strip()

        # Extract the body content of the original question
        question = soup.find('div', itemprop='text').text.strip()

        # Combine the header and the body to form the full original question
        original_question = header + " " + question

        # Find all comments on page
        comments = soup.find_all('div', class_='lia-message-body-content')

        # Extract the kudos counts for each comment
        kudos_counts = [int(count.text) for count in
                        soup.find_all('span', class_='MessageKudosCount lia-component-kudos-widget-message-kudos-count')]

        # Combine comments and kudos counts into a list of tuples
        comment_kudos = list(zip(comments, kudos_counts))[1:]
        
        # Extract accepted solutions
        accepted_solutions = []
        for comment in soup.find_all('div', class_='lia-message-body-content')[2:]:
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
                solution_text = ''.join(text_parts)

                # Append the solution text to the list of accepted solutions
                accepted_solutions.append(solution_text.strip().replace("\xa0",""))

        if not original_question:
            original_question = "Failed to retrieve the original question."

        # Check if the accepted solutions list is empty and provide a fallback message if necessary
        if not accepted_solutions:
            accepted_solutions = ["No accepted solutions found."]
        # Return the original question, top comments, and accepted solutions
        return original_question, accepted_solutions
    except Exception as e:
        logging.info(f"An error occurred: {e}")
        original_question = "Failed to retrieve the original question."
        accepted_solutions = ["No accepted solutions found."]
        return original_question, accepted_solutions


def get_top_5_links(search_query, year=2024):
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
    simulated_search_url = f"https://help.autodesk.com/view/CIV3D/{year}/ENU/?query={encoded_query}"

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
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".results-item .results-item-title a"))
        )

        # Find the element containing the instructions (inspect the page to get the correct selector)
        links = driver.find_elements(By.CSS_SELECTOR, '.results-item .results-item-title a')
        top_5_links = [link.get_attribute("href") for link in links[:5]]

        driver.quit()  # Close the browser
        
        if top_5_links:
            return top_5_links
        else:
            raise Exception("Top_5_links retrieval error. List is empty")

    except Exception as e:
        top_5_links = ["Failed to retrieve the top 5 links."]
        logging.info(f"An error occurred: {e}")
        return top_5_links


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
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "caas_body"))
        )

        # Extract page source after it is fully loaded
        page_source = driver.page_source
        driver.quit()  # Close the browser

        # Parse page source with BeautifulSoup
        soup = BeautifulSoup(page_source, 'html.parser')

        # Extract Text
        content = soup.find('div', class_='caas_body')
        extracted_text = content.get_text()

        # Extract Image URLs
        image_urls = []
        image_elements = content.find_all('img')
        for img in image_elements:
            image_url = img['src']
            if image_url:
                image_urls.append(image_url)

        # Extract Video URLs
        video_urls = []
        video_elements = content.find_all('video')
        for video in video_elements:
            sources = video.find_all('source')
            for source in sources:
                video_url = source['src']
                if video_url:
                    video_urls.append(video_url)

        return extracted_text, image_urls, video_urls

    except Exception as e:
        extracted_text = "Failed to extract text from the page."
        image_urls = ["Failed to extract image URLs from the page."]
        video_urls = ["Failed to extract video URLs from the page."]
        logging.info(f"An error occurred: {e}")
        return extracted_text, image_urls, video_urls

def ask_question_on_autodesk_and_generate_prompt(question, year=2024):
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
              "the forum contain with the original question any accepted solutions")
    # Add the user question to the prompt
    prompt += f"Use the information given to answer this question: {question}"

    # Get the top 5 links and iterate through them to extract their information then structurally
    # adding the information into the prompt
    retry = True
    attempts = 0
    max_attempts = 2
    while retry and attempts < max_attempts:
        try:
            top_5_links = get_top_5_links(search_query=question, year=year)
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
            original_question, top_comments, accepted_solutions = extract_forum_info(link)
            prompt += f"\n"
            prompt += f"**Original question**: {original_question} \n"
            prompt += f"**Top most liked comments**: \n"
            for comment in top_comments:
                prompt += comment.strip()
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
    return prompt, top_5_links

def ask_gpt_4o(question, year="2024"):
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
    key_vault_name = os.environ["KEYVAULT_NAME"]
    keyVaultRui = f"https://{key_vault_name}.vault.azure.net/"
    credential = DefaultAzureCredential()
    client = SecretClient(vault_url=keyVaultRui, credential=credential)
    secret = client.get_secret("openai-key")
    openai_key = secret.value
    client = OpenAI(api_key=openai_key)

    prompt, top_5_links = ask_question_on_autodesk_and_generate_prompt(question=question, year=year)
    # Generate the prompt using the provided question and send the request to the GPT-4o model
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )
    return response, top_5_links

def analyze_user_input(input_text):
    # analyze text
    key_vault_name = os.environ["KEYVAULT_NAME"]
    keyVaultRui = f"https://{key_vault_name}.vault.azure.net/"
    credential = DefaultAzureCredential()
    client = SecretClient(vault_url=keyVaultRui, credential=credential)
    content_safety_key = client.get_secret("content-safety-key")
    endpoint = os.environ["CONTENT_SAFETY_ENDPOINT"]
    input_safe = True
    # Create an Azure AI Content Safety client
    client = ContentSafetyClient(endpoint, AzureKeyCredential(content_safety_key.value))

    # Contruct request
    request = AnalyzeTextOptions(text=input_text)

    # Analyze text
    try:
        response = client.analyze_text(request)
    except HttpResponseError as e:
        logging.info("Analyze text failed.")
        if e.error:
            logging.info(f"Error code: {e.error.code}")
            logging.info(f"Error message: {e.error.message}")
            st.warning("Error with content filtering. Please try again later.")
        else:
            logging.info(e)
            st.warning("Error with content filtering. Please try again later.")
    
    if response:
        hate_result = next(item for item in response.categories_analysis if item.category == TextCategory.HATE)
        self_harm_result = next(item for item in response.categories_analysis if item.category == TextCategory.SELF_HARM)
        sexual_result = next(item for item in response.categories_analysis if item.category == TextCategory.SEXUAL)
        violence_result = next(item for item in response.categories_analysis if item.category == TextCategory.VIOLENCE)

        if hate_result and hate_result.severity > 1:
            st.warning("This text contains hate speech.")
            input_safe = False
        if self_harm_result and self_harm_result.severity > 1:
            st.warning("This text contains self-harm content.")
            input_safe = False
        if sexual_result and sexual_result.severity > 1:
            st.warning("This text contains sexual content.")
            input_safe = False
        if violence_result and violence_result.severity > 1:
            st.warning("This text contains violent content.")
            input_safe = False 
    return input_safe


def main():
    # Initiate a container
    with st.container():
        # Display the asistant's name
        st.title("Civil 3D AI Assistant")
        st.write("This is an independent application and is not in any way associated with Autodesk")
        year_version = st.selectbox(
        "Your Civil 3D version",
        ("2025", "2024", "2023", "2022"),
        )

        # Get the question from the user
        user_input = st.text_input("Please don't enter any sensitive information:")
        submit_button = st.button("Submit")

        # Generate the prompt and inject it into GPT 4o
        if submit_button or user_input:
            if analyze_user_input(user_input):
                with st.spinner("Processing..."):
                    response, top_5_links = ask_gpt_4o(question=user_input, year=int(year_version))
                # Display the generated response
                st.write("These instructions are AI generated. Please proceed at your own risk")
                st.subheader("Summarized troubleshooting steps", divider=True)
                st.write(response.choices[0].message.content)
                st.subheader("URLs to reference resources", divider = True)
                st.write("This application uses OpenAI API to generate responses. OpenAI API does not train models on inputs and outputs")
                for link in top_5_links:
                    st.write(link)
                
if __name__ == "__main__":
    main()
