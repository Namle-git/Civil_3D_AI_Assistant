import unittest
from unittest.mock import patch, Mock, MagicMock
import Streamlit_app

with open("test_forum_page.html", 'r', encoding='utf-8') as file:
    test_forum_page = file.read()

class TestStreamlitApp(unittest.TestCase):

    @patch('Streamlit_app.requests.get')
    def test_extract_forum_info(self, mock_get):
        # Mocking the response content with HTML example of the forum page
        mock_response = Mock()
        mock_response.content = test_forum_page
        mock_get.return_value = mock_response

        url = "http://example.com"
        original_question, accepted_solutions = Streamlit_app.extract_forum_info(url)
        self.assertEqual(original_question,
                         'Curve Table Hii everyone,Is it possible to create curve table like (in img I have attached).If it is possible could anyone please explain the procedure.Thank you\xa0\n\n\n\n\t\t\t\t\t\n\t\t\t\t\t\tSolved!\n\t\t\t\t\t\n\t\t\t\t\tGo to Solution.')
        self.assertEqual(len(accepted_solutions), 2)
        self.assertEqual(accepted_solutions[0],
                         "I don't know your level of knowledge regarding label design, however you can put just about anything in one label or multiple things from different entities.Here is a video to get your feet wet. This is on annotation labels.https://www.youtube.com/watch?v=2qZ3nC-gL1MI am not sure if there is a way to do it with alignment labels. You can label the alignment with an annotation (think singular) or a alignment label (the entire alignment).https://www.youtube.com/watch?v=AYtIZzloeucHere is a video about alignment labels:Good luck labeling!!")
        self.assertEqual(accepted_solutions[1],
                         'I tried editing the label properties and found "vertical speed and station". I wouldn\'t have expected to have seen anything regarding super elevation although you could try some of those other labels within the Cant information. I vaguely remember doing super elevation on one of my projects awhile back, and I don\'t know if that would fall under something that could be referenced with the alignment or not. You might be able to make an expression in the settings tab>alignments>commands>new command, but I don\'t know what.')

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
    def test_extract_content_from_autodesk_help(self, mock_service, mock_options, mock_chromedriver_manager, mock_chrome):
        # Mock the driver
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver

        # Mock page source for BeautifulSoup
        mock_html = """
        <div class='caas_body'>
            <p>Sample text 1</p>
            <p>Sample text 2</p>
            <img src='http://example.com/image1.jpg'/>
            <img src='http://example.com/image2.jpg'/>
            <video>
                <source src='http://example.com/video1.mp4'/>
            </video>
        </div>
        """
        # Set up the mock page source
        mock_driver.page_source = mock_html

        # Mocking the URL
        url = "http://example.com"

        # Call the function
        extracted_text, image_urls, video_urls = Streamlit_app.extract_content_from_autodesk_help(url)


        # Assertions to validate the result
        self.assertIn("Sample text 1", extracted_text)
        self.assertIn("Sample text 2", extracted_text)
        self.assertEqual(image_urls, ["http://example.com/image1.jpg", "http://example.com/image2.jpg"])
        self.assertEqual(video_urls, ["http://example.com/video1.mp4"])

        # Ensure WebDriver was called correctly
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
