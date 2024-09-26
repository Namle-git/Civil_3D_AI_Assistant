import streamlit as st
import sys
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
import ast
import shutil
from opentelemetry._logs import set_logger_provider
from opentelemetry.sdk._logs import (
    LoggerProvider,
    LoggingHandler,
)
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from azure.monitor.opentelemetry.exporter import AzureMonitorLogExporter
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

# Get the absolute path of the current file
current_dir = os.path.dirname(os.path.abspath(__file__))

# Navigate to the main_project directory
main_project_dir = os.path.abspath(os.path.join(current_dir, '..', '..', '..', '..'))

# Add the main_project directory to sys.path
sys.path.insert(0, main_project_dir)

from Streamlit_app import get_top_5_links, extract_content_from_autodesk_help, extract_forum_info

azure_monitor_log_exporter = AzureMonitorLogExporter(
        connection_string=os.environ["APP_INSIGHTS_CONNECTION_STRING"]
    )
# Initiate the OpenAI client
key_vault_name = os.environ["KEYVAULT_NAME"]
keyVaultRui = f"https://{key_vault_name}.vault.azure.net/"
credential = DefaultAzureCredential()
client = SecretClient(vault_url=keyVaultRui, credential=credential)
secret = client.get_secret("openai-key")
openai_key = secret.value
openai_client = OpenAI(api_key=openai_key)

def get_page_html(url):
    """
       Simulates a search for a query on the Autodesk Civil 3D 2024 Help page and retrieves the html.

       Args:
           search_query (str): The search query string.

       Returns:
           list: A list of the top 5 links (str) from the search results.

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

        html_content = driver.page_source

        driver.quit()

        if len(str(html_content)) > 250000:
            truncated_html_content1 = html_content[:250000]
            truncated_html_content2 = html_content[250000:500000]
            return truncated_html_content1, truncated_html_content2
        else:
            return html_content
    except Exception as e:
        raise alert_developer(f"Error in get_page_html: {e}.", 4)
    
# Track whether the processor has already been added
log_processor_added = False

def alert_developer(message, severity_level, exporter=azure_monitor_log_exporter):
    global log_processor_added

    # Map severity levels 1-4 to Python logging levels
    level_mapping = {
        1: logging.INFO,
        2: logging.WARNING,
        3: logging.ERROR,
        4: logging.CRITICAL
    }
    log_level = level_mapping.get(severity_level, logging.WARNING)
    
    # Get logger provider and set it (assuming this needs to happen each time)
    logger_provider = LoggerProvider()
    set_logger_provider(logger_provider)

    # Add the log record processor only once (using a global flag to track this)
    if not log_processor_added:
        logger_provider.add_log_record_processor(BatchLogRecordProcessor(exporter))
        log_processor_added = True

    # Attach LoggingHandler to namespaced logger if not already attached
    logger = logging.getLogger(__name__)
    
    if not any(isinstance(h, LoggingHandler) for h in logger.handlers):
        handler = LoggingHandler()
        logger.addHandler(handler)
    
    logger.setLevel(logging.NOTSET)
    
    # Log the message at the appropriate level
    logger.log(log_level, message)


def add_message_to_thread(assistant_id, thread_id, message_content, max_retries=12, max_timeout=500):
    message = openai_client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=message_content
        )
    run = openai_client.beta.threads.runs.create(
                    thread_id=thread_id,
                    assistant_id=assistant_id,
                )
    # Retrieve the run ID and poll for status
    run_id = run.id
    
    # Polling for completion with timeout
    start_time = time.time()
    timeout = 60  # Maximum 60 seconds timeout for the process
    
    # Exponential backoff settings
    retries = 0
    delay = 1  # Initial delay in seconds
    
    while True:
        run = openai_client.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run_id
        )
        
        if run.status not in ["in_progress", "queued"]:
            if run.status == "completed":
                conversation = openai_client.beta.threads.messages.list(
                    thread_id=thread_id
                )
                try:
                    assistant_message = list(reversed(conversation.data))[-1]
                    assistant_message_text = assistant_message.content[0].text.value
                    logging.info(f"Assistant response: {assistant_message_text}")
                except Exception as e:
                    logging.info(f"Error retrieving assistant message: {e}")
            return run
        
        # Exit if timeout is reached
        if time.time() - start_time > timeout:
            raise TimeoutError("The assistant run took too long to complete.")
        
        # Exponential backoff (increasing sleep time to reduce API pressure)
        # Implement exponential backoff
        if retries < max_retries:
            time.sleep(delay)
            delay *= 2  # Double the delay each retry
            retries += 1
        else:
            raise Exception("Maximum retries reached. The assistant did not complete in time.")

def start_ai_agent(assistant_id, message1, message2, message3=None, message4=None):
    thread = openai_client.beta.threads.create()
    run1 = add_message_to_thread(assistant_id=assistant_id, thread_id=thread.id, message_content=message1)
    logging.info(run1.status)
    final_run = add_message_to_thread(assistant_id=assistant_id, thread_id=thread.id, message_content=message2)
    logging.info(final_run.status)
    if message3:
        final_run = add_message_to_thread(assistant_id=assistant_id, thread_id=thread.id, message_content=message3)
        logging.info(final_run.status)
    if message4:
        final_run = add_message_to_thread(assistant_id=assistant_id, thread_id=thread.id, message_content=message4)
        logging.info(final_run.status)
    if final_run.status == 'completed':
        conversation = openai_client.beta.threads.messages.list(
            thread_id=thread.id
        )
        message = list(reversed(conversation.data))[-1]
        content = message.content[0].text.value
        if "functions.passed_test" in content:
            return "passed_test"
        elif "functions.failed_test" in content:
            return "failed_test"
        else:
            return content
        
    elif final_run.status == 'requires_action':
        required_actions = final_run.required_action.submit_tool_outputs.model_dump()
        tools_output = []
        for action in required_actions["tool_calls"]:
            func_name = action["function"]["name"]
        return func_name

def get_function_text_from_file(func_name, filename=f"{main_project_dir}\Streamlit_app.py"):
    """
    Reads the Python source code from a file and returns the text of the function
    with the specified name.

    Parameters:
    - filename (str): The path to the Python file.
    - func_name (str): The name of the function to retrieve.

    Returns:
    - str: The text of the function definition, or None if not found.
    """
    try:
        with open(filename, 'r') as f:
            code = f.read()
    except FileNotFoundError:
        logging.info(f"Error: The file '{filename}' was not found.")
        return None
    except IOError as e:
        logging.info(f"Error reading file '{filename}': {e}")
        return None
    try:
        # Parse the source code into an AST
        tree = ast.parse(code, filename=filename)
    except SyntaxError as e:
        logging.info(f"Error parsing file '{filename}': {e}")
        return None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == func_name:
            # Use ast.get_source_segment to get the source code of the node
            return ast.get_source_segment(code, node)
    return None

def extract_function_name(function_text):
    try:
        parsed_ast = ast.parse(function_text)
        for node in ast.walk(parsed_ast):
            if isinstance(node, ast.FunctionDef):
                return node.name
    except SyntaxError as e:
        alert_developer(f"Syntax error in replacement_function_code: {e}.", 4)
    return None

def extract_function_text_from_assistant_output(code_str):
    """
    Extracts the function definition from the given code string, starting from 'def',
    and removes the last line of the function.
    
    Args:
        code_str (str): The code as a string from which to extract the function.

    Returns:
        str: The extracted function code starting from 'def', omitting any preceding text
             and the last line.
    """
    # Split the input string into lines
    lines = code_str.strip().splitlines()

    # Find the first line that starts with 'def'
    function_lines = []
    function_started = False

    for line in lines:
        # Check if the line starts with 'def', indicating the function definition
        if line.strip().startswith('def') or function_started:
            function_started = True
            function_lines.append(line)

    # Remove the last line from the list of function lines
    if function_lines:
        function_lines = function_lines[:-1]  # Remove the last line

    # Join the lines to form the full function text
    function_text = '\n'.join(function_lines)

    return function_text


def execute_replacement_function(replacement_function_code, arg):
    try:
        # Open (or create) the file in write mode
        with open('webjobs/scheduled_testing_webjob/temp.py', 'w') as file:
            file.write(replacement_function_code)
        global_namespace = globals()
        local_namespace = {}
        
        exec(replacement_function_code, global_namespace, local_namespace)
        
        function_name = extract_function_name(replacement_function_code)
        
        if function_name:
            replacement_func = local_namespace.get(function_name)
            if callable(replacement_func):
                result = replacement_func(arg)
                return result
            else:
                alert_developer(f"Function '{function_name}' not found or is not callable in replacement_function.", 4)
        else:
            alert_developer("No function definition found in replacement_function_code.", 4)
    except Exception as e:
        alert_developer(f"Error in execute_replacement_function: {e}.", 4)
    return None

def replace_function_in_file(file_path, target_function_name, new_function_code, backup_folder='webjobs/scheduled_testing_webjob/backups'):
    # Step 1: Read the original Python file
    with open(file_path, 'r') as file:
        original_code = file.read()

    # Step 2: Parse the code into an AST
    try:
        tree = ast.parse(original_code)
    except SyntaxError as e:
        logging.info(f"Syntax error when parsing {file_path}: {e}")
        return

    # Step 3: Define a Node Visitor to locate the target function and get its location
    class FunctionLocator(ast.NodeVisitor):
        def __init__(self):
            self.target_function_node = None
            self.start_lineno = None
            self.end_lineno = None

        def visit_FunctionDef(self, node):
            if node.name == target_function_name:
                self.target_function_node = node
                self.start_lineno = node.lineno
                self.end_lineno = node.end_lineno
            self.generic_visit(node)

    # Locate the target function
    locator = FunctionLocator()
    locator.visit(tree)

    if not locator.target_function_node:
        logging.info(f"Function '{target_function_name}' not found in '{file_path}'.")
        return

    # Step 4: Backup the original file
    backup_dir = os.path.join(os.path.dirname(file_path), backup_folder)
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
        logging.info(f"Created backup directory at '{backup_dir}'.")

    # Create a timestamped backup file
    base_name = os.path.basename(file_path)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    backup_file_name = f"{os.path.splitext(base_name)[0]}_{timestamp}{os.path.splitext(base_name)[1]}"
    backup_file_path = os.path.join(backup_dir, backup_file_name)
    shutil.copy2(file_path, backup_file_path)
    logging.info(f"Backup of '{file_path}' created at '{backup_file_path}'.")

    # Step 5: Split the original code into lines and replace the target function
    original_lines = original_code.splitlines()

    # Preserve everything before and after the target function
    before_function = original_lines[:locator.start_lineno - 1]
    after_function = original_lines[locator.end_lineno:]

    # Insert the new function code, preserving formatting
    modified_code = '\n'.join(before_function) + '\n' + new_function_code.strip() + '\n' + '\n'.join(after_function)

    # Step 6: Write the modified code back to the original file
    with open(file_path, 'w') as file:
        file.write(modified_code)
    
    logging.info(f"Function '{target_function_name}' has been replaced in '{file_path}'.")



