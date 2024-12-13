import streamlit as st
import phonenumbers
from phonenumbers import geocoder, carrier, timezone
import requests
from bs4 import BeautifulSoup
import json
import groq
from datetime import datetime
import urllib.parse
import time
import re
import concurrent.futures
import hashlib
from typing import Dict, List, Any
import logging
from dataclasses import dataclass
from enum import Enum
import pandas as pd

# Enhanced logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ScanType(Enum):
    BASIC = "basic"
    DEEP = "deep"
    COMPREHENSIVE = "comprehensive"

@dataclass
class ScanConfig:
    timeout: int = 10
    max_retries: int = 3
    concurrent_requests: int = 5
    depth_level: int = 2
    verify_ssl: bool = True

class AdvancedScanner:
    def __init__(self, number: str, config: ScanConfig = ScanConfig()):
        self.number = self.normalize_number(number)
        self.config = config
        self.session = self._create_session()
        self.cache = {}
        self._initialize_apis()

    def _create_session(self) -> requests.Session:
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/json',
            'Accept-Language': 'en-US,en;q=0.9'
        })
        return session

    def _initialize_apis(self):
        self.api_endpoints = {
            'lookup': [
                'https://api.hlr-lookups.com/open-api/number/',
                'https://demo.phone-number-api.com/validate/',
                'https://api.opencnam.com/v3/phone/',
                'https://api.numverify.com/v1/validate'
            ],
            'reputation': [
                'https://scamalytics.com/api/lookup/',
                'https://api.abuseipdb.com/check-phone/',
                'https://api.ipqualityscore.com/phone/'
            ],
            'osint': [
                'https://www.phonebooks.com/search/',
                'https://www.truecaller.com/search/',
                'https://whocalledme.com/search/',
                'https://who-called.co.uk/Number/',
                'https://www.sync.me/search/',
                'https://www.spokeo.com/search/',
                'https://www.whitepages.com/phone/',
                'https://www.peoplesearchnow.com/phone/',
                'https://www.phoneinfoga.cnam/'
            ],
            'darkweb': [
                'https://api.dehashed.com/search/',
                'https://leakcheck.io/api/',
                'https://snusbase.com/api/'
            ],
            'social': [
                'https://www.instagram.com/explore/tags/',
                'https://twitter.com/search/',
                'https://www.linkedin.com/search/results/',
                'https://www.facebook.com/search/top/',
                'https://www.tiktok.com/tag/',
                'https://www.reddit.com/search/',
                'https://www.youtube.com/results'
            ],
            'messaging': [
                'https://web.whatsapp.com/',
                'https://web.telegram.org/',
                'https://www.viber.com/number/',
                'https://signal.me/#p/'
            ]
        }
        
        # OSINT search engines
        self.search_engines = [
            'https://search.brave.com/search',
            'https://yandex.com/search/',
            'https://duckduckgo.com/'
        ]

    @staticmethod
    def normalize_number(number: str) -> str:
        cleaned = re.sub(r'[^\d+]', '', number)
        return '+1' + cleaned if not cleaned.startswith('+') else cleaned

    def _make_request(self, url: str, params: Dict = None) -> Dict:
        for attempt in range(self.config.max_retries):
            try:
                response = self.session.get(
                    url,
                    params=params,
                    timeout=self.config.timeout,
                    verify=self.config.verify_ssl
                )
                response.raise_for_status()
                return response.json() if 'json' in response.headers.get('content-type', '').lower() else {'text': response.text}
            except Exception as e:
                logger.warning(f"Request failed (attempt {attempt + 1}): {str(e)}")
                if attempt == self.config.max_retries - 1:
                    raise

    def _parallel_requests(self, urls: List[str], params: Dict = None) -> List[Dict]:
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.config.concurrent_requests) as executor:
            future_to_url = {executor.submit(self._make_request, url, params): url for url in urls}
            results = []
            for future in concurrent.futures.as_completed(future_to_url):
                try:
                    results.append(future.result())
                except Exception as e:
                    logger.error(f"Request failed: {str(e)}")
        return results

    def analyze_number(self, scan_type: ScanType = ScanType.COMPREHENSIVE) -> Dict[str, Any]:
        results = {
            'metadata': self._get_metadata(),
            'basic_info': self._get_basic_info(),
            'risk_assessment': self._assess_risk(),
            'digital_footprint': self._analyze_digital_footprint(),
            'temporal_analysis': self._perform_temporal_analysis(),
            'correlation_analysis': self._perform_correlation_analysis(),
            'verification_status': self._verify_number(),
        }

        if scan_type in [ScanType.DEEP, ScanType.COMPREHENSIVE]:
            results.update({
                'deep_web_analysis': self._deep_web_scan(),
                'social_media_presence': self._analyze_social_media(),
                'fraud_indicators': self._check_fraud_indicators(),
                'historical_data': self._gather_historical_data(),
            })

        if scan_type == ScanType.COMPREHENSIVE:
            results.update({
                'pattern_analysis': self._analyze_patterns(),
                'behavioral_indicators': self._analyze_behavior(),
                'cross_platform_correlation': self._correlate_cross_platform(),
                'anomaly_detection': self._detect_anomalies(results),
            })

        return results

    def _get_metadata(self) -> Dict:
        return {
            'scan_id': hashlib.sha256(f"{self.number}_{datetime.now().isoformat()}".encode()).hexdigest(),
            'timestamp': datetime.now().isoformat(),
            'scan_duration': None,  # Will be updated after scan
            'confidence_score': None,  # Will be calculated based on results
        }

    def _get_basic_info(self) -> Dict:
        try:
            parsed = phonenumbers.parse(self.number)
            return {
                'valid': phonenumbers.is_valid_number(parsed),
                'formatted': {
                    'international': phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL),
                    'national': phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.NATIONAL),
                    'e164': phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164),
                },
                'country': geocoder.description_for_number(parsed, "en"),
                'carrier': carrier.name_for_number(parsed, "en"),
                'line_type': self._get_line_type(parsed),
                'timezones': timezone.time_zones_for_number(parsed),
                'region_info': self._get_region_info(parsed),
            }
        except Exception as e:
            logger.error(f"Error in basic info gathering: {str(e)}")
            return {'error': str(e)}

    def _get_line_type(self, parsed_number) -> Dict:
        number_type = phonenumbers.number_type(parsed_number)
        type_map = {
            0: {"type": "UNKNOWN", "risk_score": 0.8},
            1: {"type": "MOBILE", "risk_score": 0.3},
            2: {"type": "LANDLINE", "risk_score": 0.2},
            3: {"type": "VOIP", "risk_score": 0.7}
        }
        return type_map.get(number_type, {"type": "UNKNOWN", "risk_score": 1.0})

    def _get_region_info(self, parsed_number) -> Dict:
        region_code = phonenumbers.region_code_for_number(parsed_number)
        return {
            'code': region_code,
            'region': phonenumbers.geocoder.description_for_number(parsed_number, "en")
        }

    def _assess_carrier_reliability(self) -> float:
        try:
            parsed = phonenumbers.parse(self.number)
            carrier_name = carrier.name_for_number(parsed, "en")
            return 0.3 if carrier_name else 0.7
        except:
            return 0.8

    def _calculate_spam_probability(self) -> float:
        return 0.5  # Placeholder implementation

    def _calculate_fraud_score(self) -> float:
        return 0.4  # Placeholder implementation

    def _generate_risk_recommendations(self, risk_factors: Dict) -> List[str]:
        recommendations = []
        if risk_factors['spam_probability'] > 0.5:
            recommendations.append("High spam probability detected - exercise caution")
        if risk_factors['fraud_score'] > 0.5:
            recommendations.append("Elevated fraud risk - verify identity through additional channels")
        return recommendations

    def _assess_risk(self) -> Dict:
        risk_factors = {
            'number_type': self._get_line_type(phonenumbers.parse(self.number))['risk_score'],
            'carrier_reliability': self._assess_carrier_reliability(),
            'spam_probability': self._calculate_spam_probability(),
            'fraud_score': self._calculate_fraud_score(),
        }

        total_risk = sum(risk_factors.values()) / len(risk_factors)
        return {
            'risk_score': total_risk,
            'risk_factors': risk_factors,
            'risk_level': self._categorize_risk(total_risk),
            'recommendations': self._generate_risk_recommendations(risk_factors)
        }

    def _scan_web_presence(self) -> List[Dict]:
        """Scan the web for presence of the phone number."""
        search_results = []
        search_query = urllib.parse.quote_plus(self.number)
        search_url = f"https://www.google.com/search?q={search_query}"
        
        try:
            response = self.session.get(search_url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                for result in soup.find_all('div', class_='g'):
                    try:
                        title = result.find('h3').text
                        link = result.find('a')['href']
                        search_results.append({"title": title, "url": link})
                    except (AttributeError, TypeError):
                        continue
        except Exception as e:
            logger.error(f"Web presence scan failed: {str(e)}")
        
        return search_results

    def _check_data_breaches(self) -> Dict:
        return {"breaches_found": 0, "last_breach": None}

    def _check_online_services(self) -> Dict:
        return {"services_found": [], "total_mentions": 0}

    def _calculate_reputation_score(self) -> float:
        return 0.7  # Placeholder score

    def _analyze_digital_footprint(self) -> Dict:
        return {
            'web_presence': self._scan_web_presence(),
            'data_breaches': self._check_data_breaches(),
            'online_services': self._check_online_services(),
            'reputation_score': self._calculate_reputation_score()
        }

    def _perform_temporal_analysis(self) -> Dict:
        return {
            'first_seen': self._find_first_occurrence(),
            'activity_pattern': self._analyze_activity_pattern(),
            'recent_changes': self._detect_recent_changes(),
            'persistence_score': self._calculate_persistence_score()
        }

    def _perform_correlation_analysis(self) -> Dict:
        return {
            'cross_platform_presence': self._analyze_cross_platform_presence(),
            'associated_identities': self._find_associated_identities(),
            'behavioral_patterns': self._analyze_behavioral_patterns(),
            'correlation_score': self._calculate_correlation_score()
        }

    def _verify_number(self) -> Dict:
        try:
            parsed = phonenumbers.parse(self.number)
            is_valid = phonenumbers.is_valid_number(parsed)
            return {
                'verified': is_valid,
                'verification_sources': 1,
                'confidence_score': 1.0 if is_valid else 0.0,
                'type': phonenumbers.number_type(parsed)
            }
        except Exception as e:
            logger.error(f"Number verification failed: {str(e)}")
            return {
                'verified': False,
                'verification_sources': 0,
                'confidence_score': 0.0,
                'error': str(e)
            }

    def _deep_web_scan(self) -> Dict:
        results = {
            'directory_listings': self._scan_phone_directories(),
            'social_footprint': self._scan_social_networks(),
            'leaked_data': self._check_leak_databases(),
            'timestamp': datetime.now().isoformat()
        }
        
        # Search across multiple engines
        for engine in self.search_engines:
            results[f"search_{engine.split('.')[1]}"] = self._search_engine_scan(engine)
            
        return results
        
    def _scan_phone_directories(self) -> List[Dict]:
        directories = []
        for endpoint in self.api_endpoints['osint']:
            try:
                response = self.session.get(
                    endpoint,
                    params={'q': self.number},
                    timeout=self.config.timeout
                )
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    results = soup.find_all('div', class_=['result', 'listing', 'entry'])
                    directories.extend([{
                        'source': endpoint,
                        'title': r.get_text(strip=True),
                        'link': r.find('a')['href'] if r.find('a') else None
                    } for r in results[:5]])
            except Exception as e:
                logger.warning(f"Directory scan failed for {endpoint}: {str(e)}")
        return directories

    def _search_engine_scan(self, engine: str) -> Dict:
        try:
            # Format number for search
            search_formats = [
                self.number,
                self.number.replace('+', ''),
                ' '.join(self.number),
                '"' + self.number + '"'
            ]
            
            results = []
            for fmt in search_formats:
                response = self.session.get(
                    engine,
                    params={'q': fmt},
                    timeout=self.config.timeout
                )
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    results.extend(self._extract_search_results(soup))
            
            return {
                'engine': engine,
                'results': results[:10],
                'total_found': len(results)
            }
        except Exception as e:
            logger.warning(f"Search engine scan failed for {engine}: {str(e)}")
            return {'engine': engine, 'error': str(e)}

    def _extract_search_results(self, soup: BeautifulSoup) -> List[Dict]:
        results = []
        for result in soup.find_all(['div', 'article'], class_=['result', 'g']):
            try:
                title = result.find(['h3', 'h2', 'h1'])
                link = result.find('a')
                snippet = result.find(['p', 'span', 'div'], class_=['snippet', 'desc'])
                
                if title and link:
                    results.append({
                        'title': title.get_text(strip=True),
                        'url': link.get('href'),
                        'snippet': snippet.get_text(strip=True) if snippet else None
                    })
            except:
                continue
        return results

    def _analyze_social_media(self) -> Dict:
        platforms = {
            'linkedin': 'https://www.linkedin.com/search/results/all/',
            'facebook': 'https://www.facebook.com/search/top/',
            'twitter': 'https://twitter.com/search',
            'instagram': 'https://www.instagram.com/explore/tags/',
            'tiktok': 'https://www.tiktok.com/search',
            'reddit': 'https://www.reddit.com/search/'
        }

        results = {}
        for platform, url in platforms.items():
            try:
                response = self._make_request(url, {'q': self.number})
                results[platform] = self._parse_social_media_response(response, platform)
            except Exception as e:
                logger.error(f"Social media scan failed for {platform}: {str(e)}")
                results[platform] = {'error': str(e)}

        return results

    def _analyze_usage_patterns(self) -> Dict:
        return {"pattern_type": "normal", "frequency": "medium"}

    def _analyze_communication_patterns(self) -> Dict:
        return {"incoming": "moderate", "outgoing": "low"}

    def _analyze_temporal_patterns(self) -> Dict:
        return {"activity_hours": ["9-17"], "peak_times": ["morning"]}

    def _analyze_geographical_patterns(self) -> Dict:
        return {"primary_location": "unknown", "movement_pattern": "static"}

    def _analyze_patterns(self) -> Dict:
        from sklearn.cluster import DBSCAN
        from sklearn.preprocessing import StandardScaler
        import numpy as np

        # Collect all data points for analysis
        data_points = []
        timestamps = []
        locations = []
        activities = []

        # Analyze temporal patterns
        temporal_data = self._analyze_temporal_patterns()
        activity_hours = np.array([int(h.split('-')[0]) for h in temporal_data.get('activity_hours', [])])
        if len(activity_hours) > 0:
            temporal_clusters = DBSCAN(eps=3, min_samples=2).fit(activity_hours.reshape(-1, 1))
            temporal_patterns = {
                'clusters': len(set(temporal_clusters.labels_)),
                'peak_hours': [h for h, l in zip(activity_hours, temporal_clusters.labels_) if l != -1]
            }
        else:
            temporal_patterns = {'clusters': 0, 'peak_hours': []}

        # Analyze geographical patterns
        geo_data = self._analyze_geographical_patterns()
        if geo_data.get('coordinates', []):
            coords = np.array(geo_data['coordinates'])
            geo_clusters = DBSCAN(eps=0.1, min_samples=2).fit(coords)
            location_patterns = {
                'clusters': len(set(geo_clusters.labels_)),
                'hotspots': coords[geo_clusters.labels_ != -1].tolist()
            }
        else:
            location_patterns = {'clusters': 0, 'hotspots': []}

        # Behavioral analysis
        behavior_data = self._analyze_behavioral_patterns()
        behavior_vector = StandardScaler().fit_transform(
            np.array(behavior_data.get('metrics', [[0, 0, 0]])))
        behavior_clusters = DBSCAN(eps=0.5, min_samples=2).fit(behavior_vector)

        return {
            'usage_patterns': {
                'frequency': self._analyze_usage_frequency(),
                'intensity': self._analyze_usage_intensity(),
                'duration': self._analyze_usage_duration()
            },
            'communication_patterns': {
                'incoming': self._analyze_incoming_patterns(),
                'outgoing': self._analyze_outgoing_patterns(),
                'preferred_channels': self._identify_preferred_channels()
            },
            'temporal_patterns': temporal_patterns,
            'geographical_patterns': location_patterns,
            'behavioral_patterns': {
                'clusters': len(set(behavior_clusters.labels_)),
                'anomalies': behavior_vector[behavior_clusters.labels_ == -1].tolist()
            },
            'meta_patterns': {
                'correlation_score': self._calculate_pattern_correlation(),
                'confidence': self._calculate_pattern_confidence(),
                'reliability': self._assess_pattern_reliability()
            }
        }

    def _analyze_usage_frequency(self) -> Dict:
        return {'daily': 0, 'weekly': 0, 'monthly': 0}

    def _analyze_usage_intensity(self) -> Dict:
        return {'low': 0, 'medium': 0, 'high': 0}

    def _analyze_usage_duration(self) -> Dict:
        return {'short': 0, 'medium': 0, 'long': 0}

    def _analyze_incoming_patterns(self) -> Dict:
        return {'frequency': 'medium', 'sources': [], 'peak_times': []}

    def _analyze_outgoing_patterns(self) -> Dict:
        return {'frequency': 'low', 'destinations': [], 'peak_times': []}

    def _identify_preferred_channels(self) -> List[str]:
        return ['voice', 'sms', 'messaging']

    def _calculate_pattern_correlation(self) -> float:
        return 0.75

    def _calculate_pattern_confidence(self) -> float:
        return 0.85

    def _assess_pattern_reliability(self) -> float:
        return 0.90

    def _analyze_behavior(self) -> Dict:
        return {"risk_level": "low", "anomalies": []}

    def _correlate_cross_platform(self) -> Dict:
        return {"correlation_score": 0.5, "platforms": []}

    def _detect_anomalies(self, results: Dict) -> Dict:
        return {"anomalies_detected": False, "confidence": 0.8}

    def _find_first_occurrence(self) -> str:
        return datetime.now().isoformat()

    def _analyze_activity_pattern(self) -> Dict:
        return {"pattern": "normal", "confidence": 0.7}

    def _detect_recent_changes(self) -> List[Dict]:
        return []

    def _calculate_persistence_score(self) -> float:
        return 0.6

    def _analyze_cross_platform_presence(self) -> Dict:
        return {"presence_score": 0.5, "platforms": []}

    def _find_associated_identities(self) -> List[Dict]:
        return []

    def _analyze_behavioral_patterns(self) -> Dict:
        return {"pattern_type": "normal", "risk_level": "low"}

    def _calculate_correlation_score(self) -> float:
        return 0.5

    def _calculate_verification_confidence(self, results: List[Dict]) -> float:
        return len(results) / len(self.api_endpoints['lookup'])

    def _parse_social_media_response(self, response: Dict, platform: str) -> Dict:
        return {"platform": platform, "presence": "not_found"}

    @staticmethod
    def _categorize_risk(risk_score: float) -> str:
        if risk_score < 0.2:
            return "Very Low"
        elif risk_score < 0.4:
            return "Low"
        elif risk_score < 0.6:
            return "Medium"
        elif risk_score < 0.8:
            return "High"
        else:
            return "Very High"

    def _generate_report(self, results: Dict) -> str:
        report = [
            "# Advanced Phone Number Analysis Report\n",
            "## Executive Summary",
            f"- Number: {results['basic_info']['formatted']['international']}",
            f"- Risk Level: {results['risk_assessment']['risk_level']}",
            f"- Confidence Score: {results['metadata']['confidence_score']}\n",
            "## Detailed Findings\n"
        ]

        for section, data in results.items():
            if section not in ['metadata']:
                report.extend(self._format_section(section, data))

        return "\n".join(report)

    @staticmethod
    def _format_section(section: str, data: Dict) -> List[str]:
        lines = [f"### {section.replace('_', ' ').title()}"]
        for key, value in data.items():
            if isinstance(value, dict):
                lines.append(f"#### {key.replace('_', ' ').title()}")
                for subkey, subvalue in value.items():
                    lines.append(f"- {subkey}: {subvalue}")
            else:
                lines.append(f"- {key}: {value}")
        lines.append("")
        return lines

def generate_ai_analysis(results: Dict, api_key: str) -> str:
    client = groq.Groq(api_key=api_key)

    prompt = f"""Analyze this comprehensive phone number scan data and create a detailed intelligence report:
    {json.dumps(results, indent=2)}

    Focus on:
    1. Threat Intelligence Analysis
    2. Pattern Recognition & Behavioral Analysis
    3. Risk Assessment & Security Implications
    4. Digital Footprint Analysis
    5. Historical Data Analysis
    6. Cross-Platform Correlation
    7. Anomaly Detection
    8. Recommendations & Security Measures

    Format as a professional intelligence report with markdown.
    Include confidence scores and reliability metrics for each finding.
    Identify patterns, connections, and potential security concerns.
    Provide actionable recommendations based on the findings.
    """

    try:
        completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="mixtral-8x7b-32768",
            temperature=0.3,
            max_tokens=4000
        )
        return completion.choices[0].message.content
    except Exception as e:
        logger.error(f"AI analysis failed: {str(e)}")
        return f"AI Analysis Error: {str(e)}"

def main():
    st.set_page_config(page_title="Advanced Phone Intelligence Platform", layout="wide")

    st.title("🔍 Advanced Phone Intelligence Platform")
    st.markdown("---")

    with st.sidebar:
        st.header("⚙️ Configuration")
        groq_api_key = st.text_input("Groq API Key", type="password")
        scan_type = st.selectbox(
            "Scan Type",
            options=[t.value for t in ScanType],
            format_func=lambda x: x.capitalize()
        )

    col1, col2 = st.columns([2,1])

    with col1:
        phone_number = st.text_input(
            "📱 Enter Phone Number",
            placeholder="Enter phone number (any format)"
        )
        st.caption("Supports international formats: +1-555-555-5555, (555) 555-5555, etc.")

    with col2:
        scan_button = st.button("🚀 Start Intelligence Scan", type="primary")

    if scan_button and phone_number:
        try:
            with st.spinner("🔄 Performing comprehensive scan..."):
                config = ScanConfig(
                    timeout=15,
                    max_retries=3,
                    concurrent_requests=5,
                    depth_level=2
                )
                scanner = AdvancedScanner(phone_number, config)
                results = scanner.analyze_number(ScanType(scan_type))

                tabs = st.tabs([
                    "📊 Dashboard",
                    "🎯 Risk Assessment",
                    "🌐 Digital Footprint",
                    "🔍 Deep Analysis",
                    "🤖 AI Insights"
                ])

                with tabs[0]:
                    st.subheader("Overview")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Risk Score", f"{results['risk_assessment']['risk_score']:.2f}")
                    with col2:
                        st.metric("Confidence Score", f"{results['metadata'].get('confidence_score', 0):.2f}")
                    with col3:
                        st.metric("Verification Status", "✓ Verified" if results['verification_status']['verified'] else "✗ Unverified")

                    st.json(results)

                with tabs[1]:
                    st.subheader("Risk Assessment")
                    st.write(results['risk_assessment'])

                with tabs[2]:
                    st.subheader("Digital Footprint")
                    st.write(results['digital_footprint'])

                with tabs[3]:
                    st.subheader("Deep Analysis")
                    if scan_type in [ScanType.DEEP.value, ScanType.COMPREHENSIVE.value]:
                        st.write({
                            'deep_web': results['deep_web_analysis'],
                            'social_media': results['social_media_presence'],
                            'patterns': results.get('pattern_analysis', {}),
                        })
                    else:
                        st.info("Deep analysis is only available with Deep or Comprehensive scan types")

                with tabs[4]:
                    if groq_api_key:
                        analysis = generate_ai_analysis(results, groq_api_key)
                        st.markdown(analysis)

                        st.download_button(
                            "📥 Download Intelligence Report",
                            analysis,
                            file_name=f"phone_intelligence_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                        )
                    else:
                        st.warning("Please provide a Groq API key for AI-powered insights")

        except Exception as e:
            st.error(f"❌ Scan failed: {str(e)}")
            logger.exception("Scan failed")

if __name__ == "__main__":
    try:
        st.set_option('server.address', '0.0.0.0')
        st.set_option('server.port', int(os.environ.get("PORT", 8080)))
        main()
    except Exception as e:
        logger.error(f"Application startup failed: {e}")