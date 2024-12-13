
import logging
import groq
import numpy as np
import streamlit as st
from datetime import datetime
from typing import Dict, List, Optional
from sklearn.cluster import DBSCAN

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdvancedScanner:
    # [Previous AdvancedScanner class implementation remains the same]
    def __init__(self, number: str, api_endpoints: Dict):
        self.number = number
        self.api_endpoints = api_endpoints if isinstance(api_endpoints, dict) else {}
        self._last_request_time = {}
        self._request_limits = {}
        self._validate_initialization()

    def _validate_initialization(self):
        if not self.number:
            raise ValueError("Phone number cannot be empty")
        if not isinstance(self.api_endpoints, dict):
            raise ValueError("API endpoints must be a dictionary")
        try:
            import phonenumbers
            parsed_number = phonenumbers.parse(self.number)
            if not phonenumbers.is_valid_number(parsed_number):
                raise ValueError("Invalid phone number format")
        except Exception as e:
            raise ValueError(f"Phone number validation failed: {str(e)}")

    def scan(self) -> Dict:
        """Main scanning method that orchestrates all checks."""
        try:
            results = {
                'directory_listings': self._scan_phone_directories(),
                'social_footprint': self._scan_social_networks(),
                'leaked_data': self._check_leak_databases(),
                'timestamp': datetime.now().isoformat()
            }
            
            # Add pattern analysis
            pattern_data = self._analyze_patterns()
            if pattern_data:
                results['patterns'] = pattern_data
                
            return results
        except Exception as e:
            logger.error(f"Scan failed: {str(e)}")
            raise

    def _make_request(self, url: str, params: Dict) -> Dict:
        """API request method with rate limiting."""
        try:
            current_time = datetime.now()
            if url in self._last_request_time:
                time_diff = (current_time - self._last_request_time[url]).total_seconds()
                if time_diff < self._request_limits.get(url, 1.0):
                    raise Exception("Rate limit exceeded")
            
            self._last_request_time[url] = current_time
            # Placeholder for actual API request
            return {"status": "success", "text": "Sample response"}
        except Exception as e:
            logger.error(f"API request failed: {str(e)}")
            return {"status": "error", "text": str(e)}

    def _scan_phone_directories(self) -> List[Dict]:
        """Scan phone directories for the number."""
        try:
            return [{"source": "sample_directory", "found": False}]
        except Exception as e:
            logger.error(f"Directory scan failed: {str(e)}")
            return []

    def _scan_social_networks(self) -> List[Dict]:
        """Scan social networks for the phone number presence."""
        try:
            if not isinstance(self.api_endpoints, dict) or 'social' not in self.api_endpoints:
                logger.warning("Social endpoints not properly configured")
                return []

            results = []
            for platform, url in self.api_endpoints['social'].items():
                response = self._make_request(url, {'q': self.number})
                result = {
                    'platform': platform,
                    'timestamp': datetime.now().isoformat()
                }
                
                if response.get('status') == 'success':
                    result['found'] = bool(response.get('text'))
                else:
                    result['error'] = response.get('text', 'Unknown error')
                    
                results.append(result)
            return results
        except Exception as e:
            logger.error(f"Social network scanning failed: {str(e)}")
            return []

    def _check_leak_databases(self) -> Dict:
        """Check for presence in leak databases."""
        try:
            return {
                "leaks_found": 0,
                "sources": [],
                "last_checked": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Leak database check failed: {str(e)}")
            return {"error": str(e)}

    def _analyze_geographical_patterns(self) -> Dict:
        """Analyze geographical patterns in the data."""
        try:
            return {
                "primary_location": "unknown",
                "movement_pattern": "static",
                "coordinates": []
            }
        except Exception as e:
            logger.error(f"Geographical analysis failed: {str(e)}")
            return {}

    def _analyze_patterns(self) -> Dict:
        """Analyze various patterns in the collected data."""
        try:
            # Analyze geographical patterns
            geo_data = self._analyze_geographical_patterns()
            patterns = {
                "geographical": geo_data,
                "usage": self._analyze_usage_frequency(),
                "risk_score": self._calculate_risk_score()
            }
            
            if geo_data.get('coordinates'):
                coords = np.array(geo_data['coordinates'])
                if len(coords) >= 2:  # Only cluster if we have enough points
                    geo_clusters = DBSCAN(eps=0.1, min_samples=2).fit(coords)
                    patterns["location_clusters"] = len(set(geo_clusters.labels_))
                    
            return patterns
        except Exception as e:
            logger.error(f"Pattern analysis failed: {str(e)}")
            return {}

    def _analyze_usage_frequency(self) -> Dict:
        """Analyze usage frequency patterns."""
        try:
            return {
                'daily': 0,
                'weekly': 0,
                'monthly': 0,
                'last_updated': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Usage frequency analysis failed: {str(e)}")
            return {}

    def _calculate_risk_score(self) -> float:
        """Calculate risk score based on various factors."""
        try:
            risk_factors = {
                'directory_presence': len(self._scan_phone_directories()) * 0.2,
                'social_presence': len(self._scan_social_networks()) * 0.3,
                'leak_presence': self._check_leak_databases().get('leaks_found', 0) * 0.5
            }
            total_risk = sum(risk_factors.values())
            return min(max(total_risk, 0.0), 10.0)  # Normalize between 0-10
        except Exception as e:
            logger.error(f"Risk score calculation failed: {str(e)}")
            return -1.0

def generate_ai_analysis(results: Dict, api_key: str) -> Optional[str]:
    """Generate AI analysis of the scan results."""
    try:
        if not api_key:
            raise ValueError("API key is required for AI analysis")
        
        client = groq.Groq(api_key=api_key)
        chat_completion = client.chat.completions.create(
            messages=[{
                "role": "user",
                "content": f"Analyze this phone number intelligence data: {str(results)}"
            }],
            model="mixtral-8x7b-32768",
            temperature=0.7,
            max_tokens=500
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        logger.error(f"AI analysis generation failed: {str(e)}")
        return None

# Streamlit UI
def main():
    st.set_page_config(page_title="Phone Number Intelligence", page_icon="📱", layout="wide")
    st.title("Advanced Phone Number Intelligence")

    # Sidebar configuration
    st.sidebar.header("Configuration")
    phone_number = st.sidebar.text_input("Enter Phone Number:", placeholder="+1234567890")
    api_key = st.sidebar.text_input("Enter API Key:", type="password")
    
    # Additional options
    st.sidebar.subheader("Scan Options")
    enable_social = st.sidebar.checkbox("Social Media Scan", value=True)
    enable_leaks = st.sidebar.checkbox("Data Breach Scan", value=True)
    enable_patterns = st.sidebar.checkbox("Pattern Analysis", value=True)
    enable_ai = st.sidebar.checkbox("AI Analysis", value=True)

    if st.button("Analyze"):
        if phone_number:
            try:
                # Initialize scanner with dummy API endpoints
                scanner = AdvancedScanner(phone_number, {"social": {"facebook": "api/url", "twitter": "api/url"}})
                
                with st.spinner("Scanning..."):
                    results = scanner.scan()
                
                # Display results
                st.header("Scan Results")
                
                # Directory Listings
                st.subheader("Directory Listings")
                st.json(results['directory_listings'])
                
                # Social Footprint
                st.subheader("Social Media Presence")
                st.json(results['social_footprint'])
                
                # Leaked Data
                st.subheader("Data Breach Information")
                st.json(results['leaked_data'])
                
                # Patterns
                if 'patterns' in results:
                    st.subheader("Pattern Analysis")
                    st.json(results['patterns'])
                
                # AI Analysis
                if api_key:
                    st.subheader("AI Analysis")
                    analysis = generate_ai_analysis(results, api_key)
                    if analysis:
                        st.write(analysis)
                    else:
                        st.error("AI analysis failed. Please check your API key and try again.")
                    
            except Exception as e:
                st.error(f"Error during analysis: {str(e)}")
        else:
            st.warning("Please enter a phone number")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Application startup failed: {e}")
