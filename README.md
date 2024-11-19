# Civil_3D_AI_Assistant

## Description
Civil_3D_AI_Assistant is a Streamlit app designed to assist users with questions related to Civil 3D. The app simulates a search of the Civil 3D help page using user input as the question, iterates through the top 5 links (documentation or forum pages), and executes Python functions to extract information from these links. This information is then used to generate an answer using GPT-4o-mini. The application is supported by an AI agent that maintains that web scrapping functions.

## Table of Contents
- [Installation](#installation)
  - [Main Application](#main-application)
  - [Setting Up AI Assistants API](#setting-up-ai-assistants-api)
- [Usage](#usage)
   - [Running the AI Agent](#running-the-ai-agent)
- [Contributing](#contributing)
- [Testing](#testing)
- [License](#license)
- [Acknowledgements](#acknowledgements)
- [Contact Information](#contact-information)
- [Badges](#badges)

## Installation

### Main Application
#### Prerequisites
- Python 3.11
- OpenAI API key
- Required Python packages (listed in `requirements.txt`)

#### Step-by-Step
1. Clone the repository:
    ```bash
    git clone https://github.com/yourusername/Civil_3D_AI_Assistant.git
    ```
2. Navigate to the project directory:
    ```bash
    cd path/to/Civil_3D_AI_Assistant
    ```
3. Install the required packages:
    ```bash
    pip install -r requirements.txt
    ```
4. Set up your OpenAI API key:

    - **On Linux and macOS:**
        ```bash
        export OPENAI_API_KEY='your-api-key-here'
        ```

    - **On Windows Command Prompt:**
        ```cmd
        set OPENAI_API_KEY=your-api-key-here
        ```

    - **On Windows PowerShell:**
        ```powershell
        $env:OPENAI_API_KEY="your-api-key-here"
        ```

### Setting Up AI Assistants API
The AI agents are configured using multiple assistants, each with unique system prompts and functions. Follow these steps to set up the assistants:

1. **Create a Python Environment for the AI Agent**:
   - Ensure you create a separate Python environment from the main application to avoid conflicts.

2. **Navigate to the Agent Folder**:
   ```bash
   cd path/to/Civil_3D_AI_Assistant/App_Data/jobs/triggered/scheduledtesting
   ```
   
3. **Install Required Packages**:

```bash
pip install -r requirements.txt
```

4. **Set Environment Variables for the Assistants' IDs**:
* **Create OpenAI Assistants**:
  * **TOP_5_LINKS_VERIFICATION_ASSISTANT**:
    - **System prompt**:
        You are a helpful assistant. The user will provide you with two prompts:
        
        First Prompt: The user will give you an HTML document containing several links to relevant forum and documentation pages. Your task is to manually review the HTML and identify the top 5 URLs that lead to the most relevant forum or documentation pages. You will extract these URLs without calling any functions.
        
        When reviewing the URLs, note that some URLs may appear in different formats depending on the source. For example, URLs containing the substring 'amazonaws' might be presented differently but still functionally lead to the same destination as their canonical versions. You should recognize these links as equivalent even if they don't match character-for-character.
        
        Second Prompt: The user will provide you with a Python list of the 5 URLs extracted from the HTML by a Python function. You will compare the URLs you manually identified with the ones in the list. When comparing the URLs, treat URLs as equivalent if they differ only in format or structure but point to the same destination. This includes but is not limited to cases where:
        
        URLs contain 'amazonaws' but otherwise refer to the same resource.
        The URL path differs slightly but still leads to the same forum or documentation page.
        Parameters in the query string differ but do not alter the core destination.
        If the Python function correctly identifies the top 5 links (taking into account these flexible matching rules), you will confirm that the function worked correctly. If not, you will explain the differences and call the appropriate function. If the list is empty, the function failed to retrieve the URLs.
        
        Remember: Refrain from calling any functions during the first step (HTML review).
      
    - **Assistant functions**:
    ```json
    {
      "name": "failed_test",
      "description": "Call this function if the 5 links given in the second prompt does not match the top 5 relevant links identified from the html given",
      "strict": false,
      "parameters": {
        "type": "object",
        "properties": {},
        "required": [],
        "additionalProperties": false
      }
    },
    {
      "name": "passed_test",
      "description": "Call this function if the 5 links given in the second prompt matches the top 5 relevant links identified from the html given",
      "strict": false,
      "parameters": {
        "type": "object",
        "properties": {},
        "required": [],
        "additionalProperties": false
      }
    }
    ```
    
    - **Model**: gpt-4o
  * **TOP_5_LINKS_RETRIEVAL_CODE_CORRECTION_ASSISTANT**:
    - **System prompt**:
        You are an expert and methodical Python code analyzer and code generator.
      
    - **Assistant functions**:
    ```json
     {
      "name": "passed_test",
      "description": "Call this function if no modification needs to be made with the top 5 links extraction function",
      "strict": false,
      "parameters": {
        "type": "object",
        "properties": {},
        "required": [],
        "additionalProperties": false
      }
    }
    ```
    
    - **Model**: gpt-4o
  * **EXTRACTED_OUTPUT_COMPARISON_ASSISTANT**:
    - **System prompt**:
        You are a helpful assistant. The user will give you two prompt. The first prompt is an extracted text from a documentation page. Please analyze the content of this text. Then the user will give you the second prompt which is the extracted text from the same document page at a later time. The two texts used the same text extraction function. Please determine whether the text extraction function still adequately extracts the relevant texts from the documentation page by comparing the content of the two prompts.  If the text extraction function still adequately extracts the text, call the passed_test function. Otherwise, call the failed_test function. Only call the corresponding function without adding any additional text.
      
    - **Assistant functions**:
      ```json
        {
          "name": "passed_test",
          "description": "Call this function if the content of text given in the second prompt matches the text in the first prompt",
          "strict": false,
          "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": false
          }
        },
        {
          "name": "failed_test",
          "description": "Call this function if content of the text given in the second prompt does not match the content of the text in the first prompt",
          "strict": false,
          "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": false
          }
        }
      ```
      
    - **Model**: gpt-4o
  * **DOCUMENTATION_CODE_CORRECTION_ASSISTANT**:
    - **System prompt**:
        You are an expert and methodical Python code analyzer and generator. Your responsibilities include reviewing code for errors, optimizing for best practices, and generating Python scripts based on user needs.
      
    - **Assistant functions**:
    ```json
    {
      "name": "passed_test",
      "description": "Call this function if no modification needs to be made to the information extraction function",
      "strict": false,
      "parameters": {
        "type": "object",
        "properties": {},
        "required": [],
        "additionalProperties": false
      }
    }
    ```
    
    - **Model**: gpt-4o
  * **EXTRACTED_FORUM_COMPARISON_ASSISTANT**:
    - **System prompt**:
        You are a helpful assistant. The user will give you two prompt. The first prompt is an extracted text containing the original question and some accepted solutions from a forum page. Please analyze the content of this text without calling any function. Then the user will give you the second prompt which is the extracted text from the same document page at a later time. The two texts used the same text extraction function. Please determine whether the text extraction function still adequately extracts the the original question and some accepted solutions from the forum page by comparing the content of the two prompts.  If the text extraction function still adequately extracts the text, call the passed_test function. Otherwise, call the failed_test function. Only call the corresponding function without adding any additional text.
      
    - **Assistant functions**:
    ```json
    {
      "name": "passed_test",
      "description": "Call this function if content of the text given in the second prompt matches the content of the text in the first prompt",
      "strict": false,
      "parameters": {
        "type": "object",
        "properties": {},
        "required": [],
        "additionalProperties": false
      }
    },
    {
      "name": "failed_test",
      "description": "Call this function if the content of the text in the second prompt does not match the content of the text in the first prompt",
      "strict": false,
      "parameters": {
        "type": "object",
        "properties": {},
        "required": [],
        "additionalProperties": false
      }
    }
    ```
    
    - **Model**: gpt-4o
  * **FORUM_CODE_CORRECTION_ASSISTANT**:
    - **System prompt**:
        You are an expert and methodical Python code analyzer and code generator.
      
    - **Assistant functions**:
    ```json
    {
      "name": "passed_test",
      "description": "Only call this function if no modification needs to be made to the information extraction function",
      "strict": false,
      "parameters": {
        "type": "object",
        "properties": {},
        "required": [],
        "additionalProperties": false
      }
    }
    ```
    
    - **Model**:
      gpt-4o
* You need to configure the following environment variables with the IDs of the corresponding assistants. You can find these ids under the assistant name in the assistant tab in OpenAI Platform Playground:

    * TOP_5_LINKS_VERIFICATION_ASSISTANT: assistant_id
    * TOP_5_LINKS_RETRIEVAL_CODE_CORRECTION_ASSISTANT: assistant_id
    * EXTRACTED_OUTPUT_COMPARISON_ASSISTANT: assistant_id
    * DOCUMENTATION_CODE_CORRECTION_ASSISTANT: assistant_id
    * EXTRACTED_FORUM_COMPARISON_ASSISTANT: assistant_id
    * FORUM_CODE_CORRECTION_ASSISTANT: assistant_id
* On Linux and macOS:

```bash
export TOP_5_LINKS_VERIFICATION_ASSISTANT='assistant_id'
export TOP_5_LINKS_RETRIEVAL_CODE_CORRECTION_ASSISTANT='assistant_id'
export EXTRACTED_OUTPUT_COMPARISON_ASSISTANT='assistant_id'
export DOCUMENTATION_CODE_CORRECTION_ASSISTANT='assistant_id'
export EXTRACTED_FORUM_COMPARISON_ASSISTANT='assistant_id'
export FORUM_CODE_CORRECTION_ASSISTANT='assistant_id'
```
* On Windows Command Prompt:

```cmd
set TOP_5_LINKS_VERIFICATION_ASSISTANT=assistant_id
set TOP_5_LINKS_RETRIEVAL_CODE_CORRECTION_ASSISTANT=assistant_id
set EXTRACTED_OUTPUT_COMPARISON_ASSISTANT=assistant_id
set DOCUMENTATION_CODE_CORRECTION_ASSISTANT=assistant_id
set EXTRACTED_FORUM_COMPARISON_ASSISTANT=assistant_id
set FORUM_CODE_CORRECTION_ASSISTANT=assistant_id
```
* On Windows PowerShell:

```powershell
$env:TOP_5_LINKS_VERIFICATION_ASSISTANT="assistant_id"
$env:TOP_5_LINKS_RETRIEVAL_CODE_CORRECTION_ASSISTANT="assistant_id"
$env:EXTRACTED_OUTPUT_COMPARISON_ASSISTANT="assistant_id"
$env:DOCUMENTATION_CODE_CORRECTION_ASSISTANT="assistant_id"
$env:EXTRACTED_FORUM_COMPARISON_ASSISTANT="assistant_id"
$env:FORUM_CODE_CORRECTION_ASSISTANT="assistant_id"
```
## Usage
### Basic Example
1. Open your terminal and navigate to the project directory.
2. Run the Streamlit app:
```bash
streamlit run Streamlit_app.py
```
3. Select your software version and enter your question related to Civil 3D in the input field.
4. The app will simulate a search, extract information from the top 5 links, and generate an answer using GPT-4o-mini.

### Running the AI Agent
1. Ensure you are in the App_Data/jobs/triggered/scheduledtesting directory.
2. Run the AI agent using the following command:
```bash
python ai_agents.py
```
3. The AI agent will execute, iterating through the core extraction functions in Streamlit_app.py. The agent will automatically repair any broken function. You can try to intentionally break the function by changing the html tag and see how the agnet work.

### Screenshots
![Screenshot](https://github.com/Namle-git/Civil_3D_AI_Assistant/assets/151961878/94705563-a6c8-4773-a3db-89d859e650a9)


## Contributing
### Code of Conduct
This project adheres to the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to [nemole1407@gmail.com].

### How to Contribute
1. Fork the repository
2. Create a new branch (`git checkout -b feature-branch`)
3. Commit your changes (`git commit -m 'Add some feature'`)
4. Push to the branch (`git push origin feature-branch`)
5. Open a pull request

## Testing
### Setting Up
- Ensure `unittest` is installed (it's included in the Python standard library).

### Running Tests
- **On any operating system**:
    1. Navigate to the project directory:
        ```bash
        cd path/to/Civil_3D_AI_Assistant
        ```
    2. Run the tests using the `unittest` module:
        ```bash
        python -m unittest test_Streamlit_app.py
        ```
        
## License
This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- **Libraries and Tools**:
  - **[BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/)** - For parsing HTML and XML documents used in the project.
  - **[Selenium](https://www.selenium.dev/)** - For automating web browser interaction to simulate searches and extract content.
  - **[webdriver-manager](https://pypi.org/project/webdriver-manager/)** - For managing WebDriver binaries required by Selenium.
  - **[Streamlit](https://streamlit.io/)** - For providing the framework to build the interactive web application.
  - **[Requests](https://docs.python-requests.org/en/latest/)** - For making HTTP requests to fetch web pages.
  - **[OpenAI](https://www.openai.com)** - For the GPT-4o model used to generate answers based on extracted information.
- **Resources and Inspiration**:
  - Special thanks to the open-source community and the following resources for their documentation and support:
    - [Stack Overflow](https://stackoverflow.com/) - For providing solutions to coding issues.
    - [GitHub](https://github.com/) - For hosting the project and version control.
    - [Python Documentation](https://docs.python.org/3/) - For comprehensive guides and references.
- **Special thanks to**:
  - All the developers and contributors of the libraries and tools used in this project for their continuous development and maintenance.

## Contact Information
- Maintainer: [Nam Le](mailto:nemole1407@gmail.com)

## Badges

- ![Build Status](https://github.com/Namle-git/Civil_3D_AI_Assistant/actions/workflows/main.yml/badge.svg)
- ![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

