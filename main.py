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
                'https://api.numlookupapi.com/v1/validate/',
                'https://api.apilayer.com/number_verification/',
            ],
            'reputation': [
                'https://api.fraudguard.io/v2/phone/',
                'https://api.spamhaus.org/v2/phone/'
            ]
        }

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
            'metadata': phonenumbers.PhoneMetadata.load_for_region(region_code),
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
        verification_results = []
        for endpoint in self.api_endpoints['lookup']:
            try:
                result = self._make_request(f"{endpoint}{self.number}")
                verification_results.append(result)
            except Exception as e:
                logger.error(f"Verification failed for endpoint {endpoint}: {str(e)}")

        return {
            'verified': any(result.get('valid', False) for result in verification_results),
            'verification_sources': len(verification_results),
            'confidence_score': self._calculate_verification_confidence(verification_results)
        }

    def _deep_web_scan(self) -> Dict:
        # Implement deep web scanning logic
        return {"status": "simulated", "timestamp": datetime.now().isoformat()}

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
        return {
            'usage_patterns': self._analyze_usage_patterns(),
            'communication_patterns': self._analyze_communication_patterns(),
            'temporal_patterns': self._analyze_temporal_patterns(),
            'geographical_patterns': self._analyze_geographical_patterns()
        }

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
    main()