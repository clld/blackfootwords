"""
    Verifies navigation and loading of pages in the user interface using Selenium. 
"""
import time

def test_ui(selenium):
    """
    Test the user interface by navigating to several URLs and ensuring the pages load.
    
    Args:
        selenium: A Selenium test fixture that provides a browser instance and a URL generator.
    """
    selenium.browser.get(selenium.url('/'))
    time.sleep(1)

    selenium.browser.get(selenium.url('/languages'))
    time.sleep(3) 

    selenium.browser.get(selenium.url('/sources'))
    time.sleep(3) 
