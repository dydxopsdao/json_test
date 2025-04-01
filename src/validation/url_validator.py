from typing import List, Tuple, Dict, Any
import concurrent
import requests
from urllib.parse import urlparse
import logging
from datetime import datetime
import re
from bs4 import BeautifulSoup
from validation.validation_utils import ValidationUtils
from concurrent.futures import ThreadPoolExecutor, as_completed
from constants import MAINNET_PATTERNS
import sys
from pathlib import Path
from rich.console import Console
import time  # Import the time module for sleep


class URLValidator:
    def __init__(self, utils: ValidationUtils):
        self.utils = utils
        # Import configuration from constants
        from constants import API_ENDPOINTS, ERROR_PATTERNS, APP_STORE_CONFIG

        self.API_ENDPOINTS = API_ENDPOINTS
        self.ERROR_PATTERNS = ERROR_PATTERNS
        self.APP_STORE_CONFIG = APP_STORE_CONFIG

        # Timeout for URL requests (in seconds)
        self.TIMEOUT = 30  # Keep original timeout for each attempt
        self.MAX_RETRIES = 3  # Number of attempts
        self.RETRY_DELAY = 2  # Seconds to wait between retries

        # Initialize logging
        self.logger = logging.getLogger("URLValidator")
        self.logger.setLevel(logging.INFO)

    def _is_api_endpoint(self, url: str) -> bool:
        """
        Check if the URL is an API endpoint that should be skipped.
        """
        try:
            parsed_url = urlparse(url)
            domain_parts = parsed_url.netloc.split(".")
            for i in range(len(domain_parts) - 1):
                domain_to_check = ".".join(domain_parts[i:])
                if any(api in domain_to_check.lower() for api in self.API_ENDPOINTS):
                    return True
            return False
        except Exception:
            return False

    def _validate_app_store_url(self, url: str, path: str) -> List[Dict[str, Any]]:
        """
        Validates app store URLs by checking for valid app IDs.
        """
        # Check if it's an Apple App Store URL
        for pattern in self.APP_STORE_CONFIG["ios"]["url_patterns"]:
            match = re.search(pattern, url)
            if match:
                app_id = match.group(1)
                if app_id in self.APP_STORE_CONFIG["ios"]["valid_ids"]:
                    return []  # Valid App Store ID
                return [
                    {
                        "path": path,
                        "url": url,
                        "type": "invalid_app_store_id",
                        "details": f'Invalid Apple App Store ID: {app_id}. Expected one of: {", ".join(self.APP_STORE_CONFIG["ios"]["valid_ids"])}',
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                ]

        # Check if it's a Google Play Store URL
        for pattern in self.APP_STORE_CONFIG["android"]["url_patterns"]:
            match = re.search(pattern, url)
            if match:
                package_name = match.group(1)
                if package_name in self.APP_STORE_CONFIG["android"]["valid_ids"]:
                    return []  # Valid Package Name
                return [
                    {
                        "path": path,
                        "url": url,
                        "type": "invalid_play_store_id",
                        "details": f'Invalid Google Play Store package name: {package_name}. Expected one of: {", ".join(self.APP_STORE_CONFIG["android"]["valid_ids"])}',
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                ]

        return []

    def is_mainnet_path(self, path: str) -> bool:
        """
        Checks if a given JSON path corresponds to a mainnet environment.
        
        Args:
            path (str): The JSON path to check.
        
        Returns:
            bool: True if the path is for mainnet, False otherwise.
        """
        # Check if the path contains any mainnet patterns
        for pattern in MAINNET_PATTERNS:
            if pattern in path:
                return True
        return False

    def should_validate_url(self, path: str, url: str) -> bool:
        """
        Determines whether a URL at a given path should be validated.
        
        Args:
            path (str): The JSON path where the URL was found.
            url (str): The URL to potentially validate.
        
        Returns:
            bool: True if the URL should be validated, False otherwise.
        """
        # Skip validation for non-mainnet paths
        if not self.is_mainnet_path(path):
            self.logger.info(f"Skipping validation for non-mainnet path: {path}")
            return False

        # Skip validation for invalid URL formats
        if not url.startswith(("http://", "https://")):
            self.logger.info(f"Skipping validation for invalid URL format: {url}")
            return False

        return True

    def _check_single_url(self, url: str, path: str = "") -> List[Dict[str, Any]]:
        """
        Validate a single URL and return any issues found, with retry logic for timeouts.
        """
        issues = []

        if not url.startswith(("http://", "https://")):
            return []

        if self._is_api_endpoint(url) or self.utils.is_exception(url):
            self.logger.info(f"Skipping API/Exception endpoint: {url}")
            return []

        # Check if this is an App Store URL
        app_store_issues = self._validate_app_store_url(url, path)
        if app_store_issues or "apps.apple.com" in url or "play.google.com" in url:
            return app_store_issues  # Skip further checks for App Store URLs

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
        }
        session = requests.Session()
        last_exception = None

        for attempt in range(self.MAX_RETRIES):
            try:
                response = session.get(
                    url, timeout=self.TIMEOUT, headers=headers, allow_redirects=True
                )

                if response.status_code == 200:
                    # Success! No issues to report for this check.
                    return []
                else:
                    # Got a non-200 status code, report immediately, no retry needed.
                    return [
                        {
                            "path": path,
                            "url": url,
                            "type": "status_code",
                            "details": f"Received status code {response.status_code}",
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                    ]

            except requests.Timeout:
                last_exception = requests.Timeout(f"Request timed out after {self.TIMEOUT} seconds on attempt {attempt + 1}")
                self.logger.warning(f"Attempt {attempt + 1}/{self.MAX_RETRIES} timed out for URL: {url}. Retrying in {self.RETRY_DELAY}s...")
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.RETRY_DELAY)
                continue  # Go to the next attempt

            except requests.RequestException as e:
                # For other request errors (DNS, connection refused, etc.), fail immediately.
                return [
                    {
                        "path": path,
                        "url": url,
                        "type": "request_error",
                        "details": str(e),
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                ]
            except Exception as e:
                # For unexpected errors, fail immediately.
                return [
                    {
                        "path": path,
                        "url": url,
                        "type": "unexpected_error",
                        "details": str(e),
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                ]

        # If loop finished, all retries timed out
        if isinstance(last_exception, requests.Timeout):
             return [
                {
                    "path": path,
                    "url": url,
                    "type": "timeout",
                    # Report the timeout from the last attempt
                    "details": f"Request timed out after {self.TIMEOUT} seconds after {self.MAX_RETRIES} attempts",
                    "timestamp": datetime.utcnow().isoformat(),
                }
            ]

        # Should not be reached if logic is correct, but return empty list as fallback
        return []

    def extract_urls(
        self, config: Dict[str, Any], current_path: str = ""
    ) -> List[Tuple[str, str]]:
        """
        Recursively extract all URLs from the configuration.
        """
        urls = []

        if isinstance(config, dict):
            for key, value in config.items():
                new_path = f"{current_path}.{key}" if current_path else key
                if isinstance(value, str) and value.startswith(("http://", "https://")):
                    if value.strip() not in ["null", ""]:  # Skip empty or null URLs
                        urls.append((new_path, value))
                elif isinstance(value, (dict, list)):
                    urls.extend(self.extract_urls(value, new_path))
        elif isinstance(config, list):
            for idx, item in enumerate(config):
                new_path = f"{current_path}[{idx}]"
                if isinstance(item, str) and item.startswith(("http://", "https://")):
                    if item.strip() not in ["null", ""]:  # Skip empty or null URLs
                        urls.append((new_path, item))
                elif isinstance(item, (dict, list)):
                    urls.extend(self.extract_urls(item, new_path))

        return urls

    def validate_urls(
        self, config: Dict[str, Any], max_workers: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Validate all URLs in the configuration using parallel processing.
        """
        all_urls = self.extract_urls(config)
        self.logger.info(f"Found {len(all_urls)} URLs to validate")
        all_issues = []

        urls_by_domain = {}
        for path, url in all_urls:
            try:
                if not self.should_validate_url(path, url):
                    self.logger.debug(
                        f"Skipping validation for non-mainnet URL: {url} at path: {path}"
                    )
                    continue

                app_store_issues = self._validate_app_store_url(url, path)
                if app_store_issues:
                    self.logger.info(
                        f"Found app store issues for {url}: {app_store_issues}"
                    )
                    all_issues.extend(app_store_issues)
                    continue

                if self.utils.is_exception(url):
                    self.logger.debug(f"Skipping exception URL: {url}")
                    continue

                if self._is_api_endpoint(url):
                    self.logger.debug(f"Skipping API endpoint: {url}")
                    continue

                domain = urlparse(url).netloc
                if domain not in urls_by_domain:
                    urls_by_domain[domain] = []
                urls_by_domain[domain].append((path, url))

            except Exception as e:
                self.logger.error(f"Error processing URL {url}: {str(e)}")
                continue

        for domain, domain_urls in urls_by_domain.items():
            with ThreadPoolExecutor(
                max_workers=min(max_workers, len(domain_urls))
            ) as executor:
                future_to_url = {
                    executor.submit(self._check_single_url, url, path): (path, url)
                    for path, url in domain_urls
                }

                for future in as_completed(future_to_url):
                    path, url = future_to_url[future]
                    try:
                        issues = future.result()
                        all_issues.extend(issues)
                    except Exception as e:
                        self.logger.error(f"Error checking URL {url}: {str(e)}")

        return all_issues
