import unittest
from unittest.mock import patch, Mock, MagicMock
import Streamlit_app

with open("test_forum_page.txt", 'r', encoding='utf-8') as file:
    test_forum_page = file.read()


class TestStreamlitApp(unittest.TestCase):

    @patch('Streamlit_app.requests.get')
    def test_extract_info(self, mock_get):
        # Mocking the response content with HTML example of the forum page
        mock_response = Mock()
        mock_response.content = test_forum_page
        mock_get.return_value = mock_response

        url = "http://example.com"
        original_question, top_comments, accepted_solutions = Streamlit_app.extract_info(url)
        self.assertEqual(original_question,
                         "Dynamic Block Strech and Rotate Actions Not Cooperating I'm trying to create a block with simple stretch and rotation actions. I have this working almost 100%, but I'd really like to have the rotation grip stay fixed to the tip of the arrow after the base polyline is stretched. I've tried including the rotation action in the action set for the stretch, but then I end up with unexpected results when rotating the block after it's stretched.  Does anyone have ideas on how I could adjust this to get the desired result?\n\n\n\n\t\t\t\t\t\n\t\t\t\t\t\tSolved!\n\t\t\t\t\t\n\t\t\t\t\tGo to Solution.")
        self.assertEqual(len(top_comments), 2)
        self.assertEqual(top_comments[0][0].text.strip(),
                         'You can do this with a more simplistic approach.  Replace the linear parameter and rotation parameter with a Polar Parameter and a Polar Stretch action.  It can to both stretching and rotation in one action.  Include the point/move for the attribute in the polar stretch action.  The point/move action will chain with the stretch and rotation of the polar stretch.\n \n\n \n\nMark Mccall CAD ManglerHammer Land EngineeringLinkedin')
        self.assertEqual(top_comments[1][0].text.strip(),
                         "I'd considered that, but we're wanting to be able to specify the rotation angle and the signal head offset distance. Polar parameters will cause it to display as XY coordinate values, right?")
        self.assertEqual(len(accepted_solutions), 1)
        self.assertEqual(accepted_solutions[0],
                         '\n\n\nYou can do this with a more simplistic approach.  Replace the linear parameter and rotation parameter with a Polar Parameter and a Polar Stretch action.  It can to both stretching and rotation in one action.  Include the point/move for the attribute in the polar stretch action.  The point/move action will chain with the stretch and rotation of the polar stretch.\n\n\n\n\n\n\n\nMark Mccall CAD ManglerHammer Land EngineeringLinkedin\n')

    @patch('Streamlit_app.webdriver.Chrome')
    def test_get_top_5_links(self, mock_chrome):
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver

        mock_driver.find_elements.return_value = [Mock(get_attribute=lambda x: f"http://example.com/link{i}") for i in
                                                  range(7)]

        search_query = "example query"
        top_5_links = Streamlit_app.get_top_5_links(search_query)

        self.assertEqual(len(top_5_links), 5)
        self.assertTrue(all(link.startswith("http://example.com/link") for link in top_5_links))

    @patch('Streamlit_app.webdriver.Chrome')
    def test_extract_text_from_autodesk_help(self, mock_chrome):
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver

        mock_element = Mock()
        mock_element.text = "Example Text"
        mock_driver.find_element.return_value = mock_element

        url = "http://example.com"
        text = Streamlit_app.extract_text_from_autodesk_help(url)

        self.assertEqual(text, "Example Text")

    @patch('Streamlit_app.webdriver.Chrome')
    @patch('Streamlit_app.ChromeDriverManager')
    @patch('Streamlit_app.Options')
    @patch('Streamlit_app.Service')
    def test_extract_content_from_autodesk_help(self, mock_service, mock_options, mock_chromedriver_manager,
                                                mock_chrome):
        # Mocking the Chrome WebDriver and options
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        mock_options_instance = MagicMock()
        mock_options.return_value = mock_options_instance
        mock_service_instance = MagicMock()
        mock_service.return_value = mock_service_instance
        mock_chromedriver_manager.install.return_value = 'mocked_driver_path'

        # Sample data to be returned by the mocked WebDriver
        mock_text_elements = [MagicMock(), MagicMock()]
        # Mock the content of the page
        mock_text_element = MagicMock()
        mock_text_element.text = "Sample text 1\nSample text 2"
        

        mock_image_elements = [MagicMock(), MagicMock(), MagicMock()]
        mock_image_elements[1].get_attribute.return_value = "http://example.com/image1.jpg"
        mock_image_elements[2].get_attribute.return_value = "http://example.com/image2.jpg"

        mock_video_elements = [MagicMock()]
        mock_video_elements[0].get_attribute.return_value = "http://example.com/video1.mp4"

        # Set the return value for find_element (to mock text extraction)
        mock_driver.find_element.return_value = mock_text_element
        mock_driver.find_elements.side_effect = [
            mock_image_elements,  # First call returns image elements
            mock_video_elements  # Second call returns video elements
        ]

        # Mock the URL
        url = "http://example.com"

        # Call the function
        extracted_text, image_urls, video_urls = Streamlit_app.extract_content_from_autodesk_help(url)

        # Assertions to validate the result
        self.assertIn("Sample text 1", extracted_text)
        self.assertIn("Sample text 2", extracted_text)
        self.assertEqual(image_urls, ["http://example.com/image1.jpg", "http://example.com/image2.jpg"])
        self.assertEqual(video_urls, ["http://example.com/video1.mp4"])

        # Ensure WebDriver was called correctly
        mock_chrome.assert_called_once_with(service=mock_service_instance, options=mock_options_instance)
        mock_driver.get.assert_called_once_with(url)
        mock_driver.quit.assert_called_once()

    @patch('Streamlit_app.ask_gpt_4o')
    def test_main(self, mock_ask_gpt_4o):
        mock_ask_gpt_4o.return_value = Mock(choices=[Mock(message=Mock(content="Mocked response"))])

        with patch('streamlit.text_input', return_value='Test question'):
            with patch('streamlit.button', return_value=True):
                with patch('streamlit.write') as mock_write:
                    Streamlit_app.main()
                    mock_write.assert_called_with("Mocked response")


if __name__ == "__main__":
    unittest.main()
