import unittest
from unittest.mock import patch, Mock, MagicMock
import Streamlit_app
import re

# Assuming 'test_forum_page.txt' contains the HTML content of a forum page for testing
with open("test_forum_page.txt", 'r', encoding='utf-8') as file:
    test_forum_page = file.read()

class TestStreamlitApp(unittest.TestCase):

    @patch('Streamlit_app.requests.get')
    def test_extract_forum_info(self, mock_get):
        self.maxDiff = None  # Show the full diff in case of assertion failure

        # Mocking the response content with HTML example of the forum page
        mock_response = Mock()
        mock_response.content = test_forum_page
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        url = "http://example.com"
        original_question, accepted_solutions = Streamlit_app.extract_forum_info(url)

        # Expected outputs based on 'test_forum_page.txt' content
        expected_original_question = (
            "Dynamic Block Stretch and Rotate Actions Not Cooperating "
            "I'm trying to create a block with simple stretch and rotation actions. I have this working almost 100%, "
            "but I'd really like to have the rotation grip stay fixed to the tip of the arrow after the base polyline is stretched. "
            "I've tried including the rotation action in the action set for the stretch, but then I end up with unexpected results when rotating the block after it's stretched. "
            "Does anyone have ideas on how I could adjust this to get the desired result?"
        )

        expected_accepted_solutions = [
            (
                "You can do this with a more simplistic approach. Replace the linear parameter and rotation parameter "
                "with a Polar Parameter and a Polar Stretch action. It can do both stretching and rotation in one action. "
                "Include the point/move for the attribute in the polar stretch action. The point/move action will chain with the stretch and rotation of the polar stretch. "
                "Mark McCall CAD Manager Hammer Land Engineering LinkedIn "
                "Link: http://example.com/solution_video.mp4"
            )
        ]

        # Function to normalize whitespace
        def normalize_whitespace(text):
            return re.sub(r'\s+', ' ', text).strip()

        # Normalize and compare the original question
        self.assertEqual(
            normalize_whitespace(original_question),
            normalize_whitespace(expected_original_question)
        )

        # Normalize and compare the accepted solutions
        self.assertEqual(
            [normalize_whitespace(s) for s in accepted_solutions],
            [normalize_whitespace(s) for s in expected_accepted_solutions]
        )

    @patch('Streamlit_app.webdriver.Chrome')
    @patch('Streamlit_app.ChromeDriverManager')
    @patch('Streamlit_app.Options')
    @patch('Streamlit_app.Service')
    def test_get_top_5_links(self, mock_service, mock_options, mock_chromedriver_manager, mock_chrome):
        # Mocking the Chrome WebDriver and options
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        mock_options.return_value = MagicMock()
        mock_service.return_value = MagicMock()
        mock_chromedriver_manager.install.return_value = 'mocked_driver_path'

        # Mocked links
        mocked_links = [MagicMock() for _ in range(7)]
        for i, link in enumerate(mocked_links):
            link.get_attribute.return_value = f"http://example.com/link{i}"

        # Mock find_elements to return mocked links
        mock_driver.find_elements.return_value = mocked_links

        search_query = "example query"
        year = 2024
        top_5_links = Streamlit_app.get_top_5_links(search_query, year)

        expected_links = [f"http://example.com/link{i}" for i in range(5)]
        self.assertEqual(top_5_links, expected_links)

    @patch('Streamlit_app.webdriver.Chrome')
    @patch('Streamlit_app.ChromeDriverManager')
    @patch('Streamlit_app.Options')
    @patch('Streamlit_app.Service')
    def test_extract_content_from_autodesk_help(self, mock_service, mock_options, mock_chromedriver_manager, mock_chrome):
        # Mocking the Chrome WebDriver and options
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        mock_options.return_value = MagicMock()
        mock_service.return_value = MagicMock()
        mock_chromedriver_manager.install.return_value = 'mocked_driver_path'

        # Sample page source
        mock_driver.page_source = '''
            <div class="caas_body">
                <p>Sample text 1</p>
                <p>Sample text 2</p>
                <img src="http://example.com/image1.jpg" />
                <img src="http://example.com/image2.jpg" />
                <video>
                    <source src="http://example.com/video1.mp4" type="video/mp4">
                </video>
            </div>
        '''

        # Call the function
        url = "http://example.com"
        extracted_text, image_urls, video_urls = Streamlit_app.extract_content_from_autodesk_help(url)

        # Assertions to validate the result
        self.assertIn("Sample text 1", extracted_text)
        self.assertIn("Sample text 2", extracted_text)
        self.assertEqual(image_urls, ["http://example.com/image1.jpg", "http://example.com/image2.jpg"])
        self.assertEqual(video_urls, ["http://example.com/video1.mp4"])

        # Ensure WebDriver was called correctly
        mock_chrome.assert_called_once()
        mock_driver.get.assert_called_once_with(url)
        mock_driver.quit.assert_called_once()

    @patch('Streamlit_app.ask_gpt_4o')
    @patch('Streamlit_app.st')
    def test_main(self, mock_st, mock_ask_gpt_4o):
        # Mock the OpenAI response and top_5_links
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Mocked AI response"))]
        mock_ask_gpt_4o.return_value = (mock_response, ["http://example.com/link1", "http://example.com/link2"])

        # Mock Streamlit inputs
        mock_st.container.return_value.__enter__.return_value = mock_st
        mock_st.text_input.return_value = 'Test question'
        mock_st.button.return_value = True
        mock_st.selectbox.return_value = "2024"

        with patch('Streamlit_app.st.spinner'):
            Streamlit_app.main()

        # Assertions to check that the write function was called with expected outputs
        mock_st.write.assert_any_call("These instructions are AI generated. Please proceed at your own risk")
        mock_st.subheader.assert_any_call("Summarized troubleshooting steps", divider=True)
        mock_st.write.assert_any_call("Mocked AI response")
        mock_st.subheader.assert_any_call("URLs to reference resources", divider=True)
        mock_st.write.assert_any_call("This application uses OpenAI API to generate responses. OpenAI API does not train models on inputs and outputs")
        mock_st.write.assert_any_call("http://example.com/link1")
        mock_st.write.assert_any_call("http://example.com/link2")

if __name__ == "__main__":
    unittest.main()
