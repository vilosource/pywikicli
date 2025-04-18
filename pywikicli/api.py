"""
MediaWiki API client implementations for PyWikiCLI.
"""

import logging
import requests
import json
import urllib.parse
from typing import Dict, List, Optional, Any

from pywikicli.interfaces import (
    AuthenticationService,
    PageService,
    LinkService,
    WikiApiInterface,
    UrlGenerator
)

logger = logging.getLogger(__name__)


class MediaWikiAuth(AuthenticationService):
    """
    Authentication service for MediaWiki.
    Handles login and session management.
    """
    
    def __init__(self, api_url: str, username: str = None, password: str = None):
        """
        Initialize the authentication service.
        
        Args:
            api_url: URL of the MediaWiki API endpoint
            username: Username for authentication
            password: Password for authentication
        """
        self.api_url = api_url
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "PyWikiCLI/0.1"})
        self._logged_in = False
    
    def login(self) -> bool:
        """
        Log in to the wiki using provided credentials.
        
        Returns:
            bool: True if login successful, False otherwise
        """
        if not self.username or not self.password:
            logger.warning("No credentials provided, login skipped")
            return False
            
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
                self._logged_in = False
                return False
            
            logger.debug(f"Successfully logged in as {self.username}")
            self._logged_in = True
            return True
            
        except Exception as e:
            logger.error(f"Error during login: {e}")
            self._logged_in = False
            return False
    
    def is_authenticated(self) -> bool:
        """
        Check if currently authenticated.
        
        Returns:
            bool: True if authenticated, False otherwise
        """
        return self._logged_in


class MediaWikiPageService(PageService):
    """
    Service for MediaWiki page operations.
    Handles retrieving and editing pages.
    """
    
    def __init__(self, api_url: str, auth_service: AuthenticationService):
        """
        Initialize the page service.
        
        Args:
            api_url: URL of the MediaWiki API endpoint
            auth_service: Authentication service for API access
        """
        self.api_url = api_url
        self.auth_service = auth_service
        # Use the session from auth_service for consistency
        if isinstance(auth_service, MediaWikiAuth):
            self.session = auth_service.session
        else:
            # Create a new session if auth_service is not MediaWikiAuth
            self.session = requests.Session()
            self.session.headers.update({"User-Agent": "PyWikiCLI/0.1"})
    
    def get_page(self, title: str) -> Optional[str]:
        """
        Retrieve the content of a wiki page.
        
        Args:
            title: Title of the page to retrieve
            
        Returns:
            Optional[str]: Page content as wikitext or None if page doesn't exist
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
    
    def edit_page(self, title: str, content: str, summary: str = "", **options) -> bool:
        """
        Edit or create a wiki page with new content.
        
        Args:
            title: Title of the page to edit
            content: New content for the page
            summary: Edit summary
            **options: Additional options like minor=True, bot=True
            
        Returns:
            bool: True if edit successful, False otherwise
        """
        # Ensure we're logged in
        if not self.auth_service.is_authenticated():
            if not self.auth_service.login():
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
                'text': content,
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
                return False
                
            logger.debug(f"Successfully edited page '{title}'")
            return True
            
        except Exception as e:
            logger.error(f"Error editing page '{title}': {e}")
            raise


class MediaWikiLinkService(LinkService):
    """
    Service for MediaWiki link operations.
    Handles retrieving links from pages.
    """
    
    def __init__(self, api_url: str, session=None):
        """
        Initialize the link service.
        
        Args:
            api_url: URL of the MediaWiki API endpoint
            session: Optional requests session to use
        """
        self.api_url = api_url
        self.session = session or requests.Session()
        if not session:
            self.session.headers.update({"User-Agent": "PyWikiCLI/0.1"})
    
    def get_links(self, title: str) -> List[str]:
        """
        Get all links from a wiki page.
        
        Args:
            title: Title of the page to get links from
            
        Returns:
            List[str]: List of page titles linked from the page
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


class MediaWikiUrlGenerator(UrlGenerator):
    """
    Service for generating URLs to MediaWiki resources.
    """
    
    def __init__(self, api_url: str):
        """
        Initialize the URL generator.
        
        Args:
            api_url: URL of the MediaWiki API endpoint
        """
        self.api_url = api_url
    
    def get_page_url(self, page_title: str) -> str:
        """
        Generate URL to a wiki page.
        
        Args:
            page_title: Title of the wiki page
            
        Returns:
            str: URL to the wiki page
        """
        # Most MediaWiki sites follow these patterns:
        # API: https://wiki.example.com/api.php
        # Page: https://wiki.example.com/wiki/Page_Name or https://wiki.example.com/index.php?title=Page_Name
        
        # Try to determine the base URL
        base_url = self.api_url.split('/api.php')[0]
        
        # Encode the page name for URLs
        encoded_page = urllib.parse.quote(page_title.replace(' ', '_'))
        
        # First try the /wiki/ pattern which is common
        return f"{base_url}/wiki/{encoded_page}"


class MediaWikiClient(WikiApiInterface):
    """
    Composite client for interacting with MediaWiki APIs.
    Implements the Facade pattern to provide a unified interface to all services.
    """
    
    def __init__(self, api_url: str, username: str = None, password: str = None):
        """
        Initialize the MediaWiki client.
        
        Args:
            api_url: URL of the MediaWiki API endpoint
            username: Username for authentication
            password: Password for authentication
        """
        self.api_url = api_url
        self.auth_service = MediaWikiAuth(api_url, username, password)
        self.page_service = MediaWikiPageService(api_url, self.auth_service)
        self.link_service = MediaWikiLinkService(api_url, self.auth_service.session)
        self.url_generator = MediaWikiUrlGenerator(api_url)
        
        # Try to login if credentials are provided
        if username and password:
            self.login()
    
    def login(self) -> bool:
        """
        Log in to the wiki using provided credentials.
        
        Returns:
            bool: True if login successful, False otherwise
        """
        return self.auth_service.login()
    
    def is_authenticated(self) -> bool:
        """
        Check if currently authenticated.
        
        Returns:
            bool: True if authenticated, False otherwise
        """
        return self.auth_service.is_authenticated()
    
    def get_page(self, title: str) -> Optional[str]:
        """
        Retrieve content of a wiki page.
        
        Args:
            title: Title of the wiki page
            
        Returns:
            Optional[str]: Page content or None if page doesn't exist
        """
        return self.page_service.get_page(title)
    
    def edit_page(self, title: str, content: str, summary: str = "", **options) -> bool:
        """
        Edit or create a wiki page.
        
        Args:
            title: Title of the wiki page
            content: New content for the page
            summary: Edit summary/comment
            **options: Additional edit options
            
        Returns:
            bool: True if successful, False otherwise
        """
        return self.page_service.edit_page(title, content, summary, **options)
    
    def get_links(self, title: str) -> List[str]:
        """
        Get all links from a wiki page.
        
        Args:
            title: Title of the wiki page
            
        Returns:
            List[str]: List of page titles linked from the page
        """
        return self.link_service.get_links(title)
    
    def get_page_url(self, page_title: str) -> str:
        """
        Generate URL to a wiki page.
        
        Args:
            page_title: Title of the wiki page
            
        Returns:
            str: URL to the wiki page
        """
        return self.url_generator.get_page_url(page_title)


# For backward compatibility
WikiClient = MediaWikiClient