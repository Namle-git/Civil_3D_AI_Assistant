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
import subprocess
import ast
import shutil
import sys
from opentelemetry._logs import set_logger_provider
from opentelemetry.sdk._logs import (
    LoggerProvider,
    LoggingHandler,
)
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from azure.monitor.opentelemetry.exporter import AzureMonitorLogExporter
from ai_agent_functions import *

# Get the absolute path of the current file
current_dir = os.path.dirname(os.path.abspath(__file__))

# Navigate to the main_project directory
main_project_dir = os.path.abspath(os.path.join(current_dir, '..', '..', '..', '..'))

# Add the main_project directory to sys.path
sys.path.insert(0, main_project_dir)

from Streamlit_app import get_top_5_links, extract_content_from_autodesk_help, extract_forum_info

function_replaced = False

def commit_changes_to_git(commit_message):
    # Navigate to the main project directory
    os.chdir(main_project_dir)

    # Add changes
    subprocess.run(['git', 'add', 'Streamlit_app.py'])

    # Commit changes
    subprocess.run(['git', 'commit', '-m', commit_message])

    # Push changes
    subprocess.run(['git', 'push', 'origin', 'main'])

def restart_website():
    # Touch the web.config file to trigger a restart
    web_config_path = os.path.join(main_project_dir, 'web.config')
    with open(web_config_path, 'a'):
        os.utime(web_config_path, None)

def test_top_5_links_retrieval():
    global function_replaced
    reference_top_5_links = [
        'https://forums.autodesk.com/t5/Civil-3D-Forum/Cogo-Point-Text-Rotating-in-Viewport/td-p/9996980', 
        'https://help.autodesk.com/view/CIV3D/2024/ENU/?caas=caas/sfdcarticles/sfdcarticles/North-Arrow-Rotates-when-Linked-to-a-Viewport-in-Civil-3D.html', 
        'https://forums.autodesk.com/t5/Civil-3D-Forum/not-displaying-ECW-Raster-image-in-Viewport-Layout-when-I-rotate-the-map-with-the-Alignspace-command/td-p/11090968', 
        'https://help.autodesk.com/view/CIV3D/2024/ENU/?caas=caas/sfdcarticles/sfdcarticles/When-a-viewport-is-rotated-image-and-lines-do-not-align.html', 
        'https://help.autodesk.com/view/CIV3D/2024/ENU/?caas=caas/sfdcarticles/sfdcarticles/ECW-disappear-in-Layout-or-enable-background-transparency.html'
        ]
    search_query = "How to rotate in viewport"
    top_5_links = get_top_5_links(search_query, year=2024)
    try: 
        assert len(top_5_links) == 5
        for link in top_5_links:
            assert link in reference_top_5_links, f"Link '{link}' not found in reference links."
    except Exception as e:
        alert_developer(f"Error in test_top_5_links_retrieval: {e}. Performing secondary testing", 2)
        page_html_content = get_page_html(url="https://help.autodesk.com/view/CIV3D/2024/ENU/?query=how%20to%20rotate%20in%20viewport")
        secondary_test_status = start_ai_agent(os.environ["TOP_5_LINKS_VERIFICATION_ASSISTANT"], message1=page_html_content, message2=str(top_5_links))
        if secondary_test_status == "passed_test":
            pass
        elif secondary_test_status == "failed_test":
            alert_developer(f"Failed secondary test. Error with top 5 links retrieval function. Attempting to repair via agent", 3)
            top_5_links_retrieval_function = get_function_text_from_file("get_top_5_links")
            message1 = f"""This is an HTML page containing several URLs to helpful pages that might be relevant 
            to a user question: {page_html_content}. Please review the entire HTML and identify \
            the specific HTML elements (e.g., <div>, <p>, <span>, etc.) that contain the top 5 relevant URLs to pages that might be helpful to a user question.
            Please identify the elements without making any function calls. Please make sure to refrain from calling any functions"""

            message2 = f"""I have a Python function that extracts data the top 5 URLs from the Civil 3D help search page. It is designed to extract the top 5 relevant URLs \
            by identifying specific HTML elements. However, I want you to carefully and thoroughly examine the HTML element \
            identification used in the function to ensure that it correctly matches the relevant elements in the page's actual HTML structure.

            Please pay special attention to every line in the function where soup.find or soup.find_all is used. For each of these lines:

            1. Compare the HTML element (tag, class, etc.) specified in the function with the structure of the given html page.
            2. Ensure that the HTML element being targeted by the function is accurate and will successfully retrieve the desired content.
            3. If there are any mismatches between the function\’s HTML element targeting and the actual structure of the page, suggest specific corrections without generating any code.
            Here is the function:{top_5_links_retrieval_function}
            Make sure to focus on accuracy and recommend any necessary corrections to ensure the function's HTML element matching is aligned with the actual page  
            structure without calling any functions
            
            Please take one of the following actions:
            1. If no corrections or modifications to the user given function needs to be made, call the `passed_test` function.
            2. If there are any corrections or modifications that should be made to the code, respond with only the modified function without any explanations, comments, or additional text. Do not call the'passed_test' function
            """

            agent_output = start_ai_agent(os.environ["TOP_5_LINKS_RETRIEVAL_CODE_CORRECTION_ASSISTANT"], message1=message1, message2=message2)
            if agent_output == "passed_test":
                alert_developer("Agent did not find any error with the exisiting function", 2)
            else:
                agent_output = extract_function_text_from_assistant_output(agent_output)
                replacement_function_output = execute_replacement_function(agent_output, "how to rotate in viewport")
                logging.info(f"Replacement function output: {replacement_function_output}")
                replacement_function_test_status = start_ai_agent(os.environ["TOP_5_LINKS_VERIFICATION_ASSISTANT"], message1=str(page_html_content), message2=str(replacement_function_output))
                if replacement_function_test_status == "passed_test":
                    try:
                        replace_function_in_file(f"{main_project_dir}\Streamlit_app.py", "get_top_5_links", agent_output)
                        function_replaced = True
                        alert_developer("Replacement code passed. Implementing", 1)
                    except Exception as e:
                        alert_developer("Replacement code failed. Manual intervention required", 4)
                else:
                    alert_developer("Replacement code failed. Manual intervention required", 4)
        else:
            alert_developer("Critical Error", 4)

def test_extract_content_from_autodesk_help():
    global function_replaced
    reference_text = '\n\nIssue:When a viewport is rotated in\xa0AutoCAD, AutoCAD Map 3D or Civil 3D, the underlying SID or ECW image is no longer aligned to the drafted content.\xa0 Non-rotated viewports appear normal.Note.\xa0 In some cases the content only shifts when zooming in or out.\xa0\n \n\nSolution:To minimize the impact of the issue: \n  \nIn AutoCAD Map 3D or Civil 3D, use MAPCONNECT\xa0command to connect to the SID or ECW as an FDO-connection.\n\n\n\n\n\nTry using a different image format, such as TIF.\nUse non-rotated viewports.\n\n\n\nProducts: AutoCAD Products;\n \n'
    reference_images = ['https://help.autodesk.com/sfdcarticles/img/0EM3A0000002uCr',
                        'https://help.autodesk.com/sfdcarticles/img/0EM3A0000002uFl']
    reference_videos = []
    url = 'https://help.autodesk.com/view/CIV3D/2024/ENU/?caas=caas/sfdcarticles/sfdcarticles/When-a-viewport-is-rotated-image-and-lines-do-not-align.html'
    extracted_text, image_urls, video_urls = extract_content_from_autodesk_help(url=url)
    logging.info(extracted_text)
    try: 
        assert extracted_text == reference_text
        for image in image_urls:
            assert image in reference_images, f"Image {image} not found in reference image list."
        assert video_urls == reference_videos
    except Exception as e:
        alert_developer(f"Error in test_extract_content_from_autodesk_help: {e}. Performing secondary testing", 2)
        page_html_content = get_page_html(url='https://help.autodesk.com/view/CIV3D/2024/ENU/?caas=caas/sfdcarticles/sfdcarticles/When-a-viewport-is-rotated-image-and-lines-do-not-align.html')
        secondary_test_status = start_ai_agent(os.environ["EXTRACTED_OUTPUT_COMPARISON_ASSISTANT"], message1=str(reference_text), message2=str(extracted_text))
        if secondary_test_status == "passed_test":
            pass
        elif secondary_test_status == "failed_test":
            alert_developer(f"Failed secondary test. Error with extract_content_from_autodesk_help function. Attempting to repair via agent", 3)
            extract_content_from_autodesk_help_function = get_function_text_from_file("extract_content_from_autodesk_help")
            message1 = f"""This is an HTML page from a documentation page. {page_html_content}. Please review the entire HTML and identify \
            the specific HTML elements (e.g., <div>, <p>, <span>, etc.) that contain:
            1. The relevent documentation text.
            2. Any image urls.
            3. Any video urls.
            Please identify the elements without making any function calls. Please make sure to refrain from calling any functions"""

            message2 = f"""I have a Python function that extracts data from a Civil 3D documentation page. It is designed to extract the  the relevant text,\
            image urls, and video urls by identifying specific HTML elements. However, I want you to carefully and thoroughly examine the HTML element \
            identification used in the function to ensure that it correctly matches the relevant elements in the page's actual HTML structure.

            Please pay special attention to every line in the function where soup.find or soup.find_all is used. For each of these lines:

            1. Compare the HTML element (tag, class, etc.) specified in the function with the structure of a typical Civil 3D documentation page.
            2. Ensure that the HTML element being targeted by the function is accurate and will successfully retrieve the desired content.
            3. If there are any mismatches between the function\’s HTML element targeting and the actual structure of the page, suggest specific corrections to ensure the function works as intended.
            Here is the function:{extract_content_from_autodesk_help_function}
            Make sure to focus on accuracy and recommend any necessary corrections to ensure the function's HTML element matching is aligned with the actual page  
            structure without calling any functions or generate any code
            
            Please take one of the following actions:
            1. If no corrections or modifications to the user given function needs to be made, call the `passed_test` function.
            2. If there are  any corrections or modifications that should be made to the code, respond with only the modified function without any explanations, comments, or additional text. Do not call the'passed_test' function"""

            agent_output = start_ai_agent(os.environ["DOCUMENTATION_CODE_CORRECTION_ASSISTANT"], message1=message1, message2=message2)
            if agent_output == "passed_test":
                alert_developer("Agent did not find any error with the exisiting function", 2)
            else:
                agent_output = extract_function_text_from_assistant_output(agent_output)
                replacement_function_output = execute_replacement_function(agent_output, arg=url)
                if replacement_function_output:
                    replacement_function_text_output, replacement_function_image_urls, replacement_function_video_urls = replacement_function_output
                    replacement_function_test_status = start_ai_agent(os.environ["EXTRACTED_OUTPUT_COMPARISON_ASSISTANT"], message1=str(reference_text), message2=str(replacement_function_text_output))
                    if replacement_function_test_status == "passed_test":
                        try:
                            replace_function_in_file(f"{main_project_dir}\Streamlit_app.py", "extract_content_from_autodesk_help", agent_output)
                            function_replaced = True
                            alert_developer("Replacement code passed. Implementing", 1)
                        except Exception as e:
                            alert_developer("Replacement code failed. Manual intervention required", 4)
                else:
                    alert_developer("Replacement code failed. Manual intervention required", 4)
        else:
            alert_developer("Critical Error", 4)

def test_extract_forum_info():
    global function_replaced
    reference_original_question = 'Curve Table Hii everyone,Is it possible to create curve table like (in img I have attached).If it is possible could anyone please explain the procedure.Thank you\xa0\n\n\n\n\t\t\t\t\t\n\t\t\t\t\t\tSolved!\n\t\t\t\t\t\n\t\t\t\t\tGo to Solution.'
    reference_accepted_solutions = ["I don't know your level of knowledge regarding label design, however you can put just about anything in one label or multiple things from different entities.Here is a video to get your feet wet. This is on annotation labels.https://www.youtube.com/watch?v=2qZ3nC-gL1MI am not sure if there is a way to do it with alignment labels. You can label the alignment with an annotation (think singular) or a alignment label (the entire alignment).https://www.youtube.com/watch?v=AYtIZzloeucHere is a video about alignment labels:Good luck labeling!!",
    'I tried editing the label properties and found "vertical speed and station". I wouldn\'t have expected to have seen anything regarding super elevation although you could try some of those other labels within the Cant information. I vaguely remember doing super elevation on one of my projects awhile back, and I don\'t know if that would fall under something that could be referenced with the alignment or not. You might be able to make an expression in the settings tab>alignments>commands>new command, but I don\'t know what.']

    url = 'https://forums.autodesk.com/t5/civil-3d-forum/curve-table/m-p/12949679'
    original_question, accepted_solutions = extract_forum_info(url=url)
    try: 
        assert reference_original_question == original_question
        for accepted_solution in accepted_solutions:
            assert accepted_solution in reference_accepted_solutions, f"Accepted solution {accepted_solution} not found in reference accepted solutions list."
    except Exception as e:
        alert_developer(f"Error in test_extract_forum_info: {e}. Performing secondary testing", 2)
        page_html_content1, page_html_content2 = get_page_html(url=url)
        message1 = f"Original question: {reference_original_question}\nAccepted solutions: {reference_accepted_solutions}. Do not call any function"
        message2 = f"Original question: {original_question}\nAccepted solutions: {accepted_solutions}"
        secondary_test_status = start_ai_agent(os.environ["EXTRACTED_FORUM_COMPARISON_ASSISTANT"], message1=str(message1), message2=str(message2))
        if secondary_test_status == "passed_test":
            pass
        elif secondary_test_status == "failed_test":
            alert_developer(f"Failed secondary test. Error with extract_forum_info function. Attempting to repair via agent", 3)
            extract_content_from_autodesk_forum_function = get_function_text_from_file("extract_forum_info")
            message1 = f"""This is the first half HTML page from a forum: {page_html_content1}. I will give you the second half of the HTML page next.
            """
            message2 = f"""This is the second half HTML page from a forum: {page_html_content2}. Please review the entire HTML and identify \
                the specific HTML elements (e.g., <div>, <p>, <span>, etc.) that contain:
                1. The original question.
                2. Any accepted solution (if present).
                Please identify the elements without making any function calls. Please make sure to refrain from calling any functions"""

            message3 = f"""I have a Python function that extracts data from a Civil 3D forum page. It is designed to extract the original question, \
            and accepted solutions by identifying specific HTML elements. However, I want you to carefully and thoroughly examine the HTML element \
            identification used in the function to ensure that it correctly matches the relevant elements in the page's actual HTML structure.

            Please pay special attention to every line in the function where soup.find or soup.find_all is used. For each of these lines:

            1. Compare the HTML element (tag, class, etc.) specified in the function with the structure of a typical Civil 3D forum page.
            2. Ensure that the HTML element being targeted by the function is accurate and will successfully retrieve the desired content.
            3. If there are any mismatches between the function’s HTML element targeting and the actual structure of the page, suggest specific corrections to ensure the function works as intended.
            Here is the function:{extract_content_from_autodesk_forum_function}
            Make sure to focus on accuracy and recommend any necessary corrections to ensure the function's HTML element matching is aligned with the actual page  
            structure without calling any functions
            
            Please take one of the following actions:
            1. If no corrections or modifications to the user given function needs to be made, call the `passed_test` function.
            2. If there are any corrections or modifications that should be made to the code, respond with the modified function without any explanations, comments, or additional text. Do not call the'passed_test' function"""

            agent_output = start_ai_agent(os.environ["FORUM_CODE_CORRECTION_ASSISTANT"], message1=message1, message2=message2, message3=message3)
            if agent_output == "passed_test":
                alert_developer("Agent did not find any error with the exisiting function", 2)
            else:
                agent_output = extract_function_text_from_assistant_output(agent_output)
                replacement_function_output = execute_replacement_function(agent_output, arg=url)
                if replacement_function_output:
                    replacement_original_question, replacement_accepted_solutions = replacement_function_output
                    logging.info(f"Replacement original question: {replacement_original_question}")
                    logging.info(f"Replacement accepted solutions: {replacement_accepted_solutions}")
                    message1 = f"Original question: {str(reference_original_question)}\nAccepted solutions: {str(reference_accepted_solutions)}"
                    message2 = f"Original question: {str(replacement_original_question)}\nAccepted solutions: {str(replacement_accepted_solutions)}"
                    replacement_function_test_status = start_ai_agent(os.environ["EXTRACTED_FORUM_COMPARISON_ASSISTANT"], message1=str(message1), message2=str(message2))
                    if replacement_function_test_status == "passed_test":
                        try:
                            replace_function_in_file(f"{main_project_dir}\Streamlit_app.py", "extract_forum_info", agent_output)
                            function_replaced = True
                            alert_developer("Replacement code passed. Implementing", 1)
                        except Exception as e:
                            alert_developer("Replacement code failed. Manual intervention required", 4)
                else:
                    alert_developer("Execute_replacement_function returned None.", 4)
        else:
            alert_developer("Critical Error", 4)

if __name__=="__main__":
    logging.info("Testing forum info extraction \n ------------------------------")
    test_extract_forum_info()
    logging.info("Testing top 5 links retrieval \n ------------------------------")
    test_top_5_links_retrieval()
    logging.info("Testing content extraction from Autodesk help \n ------------------------------")
    test_extract_content_from_autodesk_help()
    if function_replaced:
        commit_changes_to_git("AI Agent: Replaced function")
        restart_website()
        logging.info("Application restart triggered.")
