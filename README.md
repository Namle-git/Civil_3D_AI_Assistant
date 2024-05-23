# Civil_3D_AI_Assistant

## Description
Civil_3D_AI_Assistant is a Streamlit app designed to assist users with questions related to Civil 3D. The app simulates a search of the Civil 3D help page using user input as the question, iterates through the top 5 links (documentation or forum pages), and executes Python functions to extract information from these links. This information is then used to generate an answer using GPT-40.

## Table of Contents
- [Installation](#installation)
- [Usage](#usage)
- [Contributing](#contributing)
- [Testing](#testing)
- [License](#license)
- [Acknowledgements](#acknowledgements)
- [Contact Information](#contact-information)

## Installation
### Prerequisites
- Python 3.11
- OpenAI API key
- Required Python packages (listed in `requirements.txt`)

### Step-by-Step
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

5. Run the Streamlit app:
    ```bash
    streamlit run Streamlit_app.py
    ```
    
## Usage
### Basic Example
1. Open your terminal and navigate to the project directory.
2. Run the Streamlit app:
    ```bash
    streamlit run Streamlit_app.py
    ```
3. Enter your question related to Civil 3D in the input field.
4. The app will simulate a search, extract information from the top 5 links, and generate an answer using GPT-4.

### Screenshots
![Screenshot](https://github.com/Namle-git/Civil_3D_AI_Assistant/assets/151961878/94705563-a6c8-4773-a3db-89d859e650a9)


## Contributing
### Code of Conduct
This project adheres to the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to [your-email@example.com].

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

