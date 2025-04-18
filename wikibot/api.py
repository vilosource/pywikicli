"""
MediaWiki API client for Wikibot CLI.
Handles API interactions using the requests library.
"""

import logging
import requests
import json

logger = logging.getLogger(__name__)


class WikiClient:
    """
    Client for interacting with MediaWiki APIs.
    Handles authentication, page retrieval, editing, and link traversal.
    """
    
    def __init__(self, api_url: str, username: str = None, password: str = None):
        """
        Initialize the WikiClient with API endpoint and optional credentials.
        
        Args:
            api_url (str): URL of the MediaWiki API endpoint
            username (str, optional): Username for authentication
            password (str, optional): Password for authentication
        """
        self.api_url = api_url
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Wikibot/0.1"})
        self.logged_in = False
        
        # Always try to login if credentials are provided, even for read operations
        if username and password:
            self.login()
    
    def login(self):
        """
        Log in to the wiki using provided credentials.
        
        Raises:
            Exception: If login fails
        """
        # Step 1: Get login token
        params = {
            'action': 'query',
            'meta': 'tokens',
            'type': 'login',
            'format': 'json'
        }
        
        try:
            response = self.session.get(self.api_url, params=params)
            response.raise_for_status()
            data = response.json()
            token = data['query']['tokens']['logintoken']
            
            # Step 2: Send login request with token
            login_params = {
                'action': 'login',
                'lgname': self.username,
                'lgpassword': self.password,
                'lgtoken': token,
                'format': 'json'
            }
            
            login_response = self.session.post(self.api_url, data=login_params)
            login_response.raise_for_status()
            login_data = login_response.json()
            
            if login_data['login']['result'] != 'Success':
                logger.error(f"Login failed: {login_data['login']['reason']}")
                raise Exception(f"Login failed: {login_data['login']['reason']}")
            
            logger.debug(f"Successfully logged in as {self.username}")
            self.logged_in = True
            
        except Exception as e:
            logger.error(f"Error during login: {e}")
            raise
    
    def get_page(self, title: str) -> str:
        """
        Retrieve the content of a wiki page.
        
        Args:
            title (str): Title of the page to retrieve
            
        Returns:
            str: Page content as wikitext or None if page doesn't exist
        """
        params = {
            'action': 'query',
            'prop': 'revisions',
            'titles': title,
            'rvprop': 'content',
            'rvslots': 'main',
            'format': 'json'
        }
        
        try:
            response = self.session.get(self.api_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Log the full response for debugging
            logger.debug(f"API Response: {json.dumps(data, indent=2)}")
            
            # Check if response contains expected structure
            if 'query' not in data:
                logger.error(f"Unexpected API response structure: {data}")
                return None
                
            # Extract page content from response
            pages = data['query']['pages']
            page_id = next(iter(pages))
            
            # Check if page exists
            if 'missing' in pages[page_id]:
                logger.warning(f"Page '{title}' does not exist")
                return None
                
            content = pages[page_id]['revisions'][0]['slots']['main']['*']
            return content
            
        except Exception as e:
            logger.error(f"Error retrieving page '{title}': {e}")
            raise
    
    def edit_page(self, title: str, new_content: str, summary: str = "", **options):
        """
        Edit or create a wiki page with new content.
        
        Args:
            title (str): Title of the page to edit
            new_content (str): New content for the page
            summary (str, optional): Edit summary
            **options: Additional options like minor=True, bot=True
            
        Raises:
            Exception: If edit fails or user is not logged in
        """
        # Ensure we're logged in
        if not self.logged_in:
            if self.username and self.password:
                self.login()
            else:
                raise Exception("Authentication required to edit pages")
        
        # Step 1: Get CSRF token
        params = {
            'action': 'query',
            'meta': 'tokens',
            'format': 'json'
        }
        
        try:
            response = self.session.get(self.api_url, params=params)
            response.raise_for_status()
            data = response.json()
            csrf_token = data['query']['tokens']['csrftoken']
            
            # Step 2: Submit the edit
            edit_params = {
                'action': 'edit',
                'title': title,
                'text': new_content,
                'summary': summary,
                'token': csrf_token,
                'format': 'json'
            }
            
            # Add optional parameters
            if options.get('minor'):
                edit_params['minor'] = '1'
            if options.get('bot'):
                edit_params['bot'] = '1'
            
            edit_response = self.session.post(self.api_url, data=edit_params)
            edit_response.raise_for_status()
            edit_data = edit_response.json()
            
            if 'error' in edit_data:
                logger.error(f"Edit failed: {edit_data['error']['info']}")
                raise Exception(f"Edit failed: {edit_data['error']['info']}")
                
            logger.debug(f"Successfully edited page '{title}'")
            
        except Exception as e:
            logger.error(f"Error editing page '{title}': {e}")
            raise
    
    def get_links(self, title: str) -> list:
        """
        Get all links from a wiki page.
        
        Args:
            title (str): Title of the page to get links from
            
        Returns:
            list: List of page titles linked from the page
        """
        params = {
            'action': 'query',
            'prop': 'links',
            'titles': title,
            'pllimit': 500,  # Fetch up to 500 links
            'format': 'json'
        }
        
        all_links = []
        try:
            # Handle continuation if there are many links
            continue_param = None
            
            while True:
                if continue_param:
                    params.update(continue_param)
                    
                response = self.session.get(self.api_url, params=params)
                response.raise_for_status()
                data = response.json()
                
                # Extract links from response
                pages = data['query']['pages']
                page_id = next(iter(pages))
                
                # Check if page exists and has links
                if 'missing' not in pages[page_id] and 'links' in pages[page_id]:
                    links = pages[page_id]['links']
                    all_links.extend([link['title'] for link in links])
                
                # Check if we need to continue for more links
                if 'continue' not in data:
                    break
                    
                continue_param = {'plcontinue': data['continue']['plcontinue']}
            
            return all_links
            
        except Exception as e:
            logger.error(f"Error retrieving links from '{title}': {e}")
            raise