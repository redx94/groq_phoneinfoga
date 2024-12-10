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

class NumberScanner:
    def __init__(self, number):
        self.number = self.normalize_number(number)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def normalize_number(self, number):
        # Remove all non-numeric characters except + for country code
        cleaned = re.sub(r'[^\d+]', '', number)
        if not cleaned.startswith('+'):
            # Assume US number if no country code
            cleaned = '+1' + cleaned if cleaned else ''
        return cleaned

    def scan_number(self):
        results = {}
        
        # Enhanced Basic Info
        try:
            parsed = phonenumbers.parse(self.number)
            results['valid'] = phonenumbers.is_valid_number(parsed)
            results['formatted'] = {
                'international': phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL),
                'national': phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.NATIONAL),
                'e164': phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
            }
            results['country'] = geocoder.description_for_number(parsed, "en")
            results['carrier'] = carrier.name_for_number(parsed, "en")
            results['timezones'] = timezone.time_zones_for_number(parsed)
            results['line_type'] = self.get_number_type(parsed)
            results['region'] = phonenumbers.region_code_for_number(parsed)
            results['possible_formats'] = self.generate_number_formats(parsed)
        except Exception as e:
            results['error'] = f"Basic info error: {str(e)}"

        # Expanded OSINT Scans
        results['osint'] = self.perform_osint_scan()
        results['deep_web'] = self.perform_deep_web_scan()
        results['breach_check'] = self.check_data_breaches()
        
        # Enhanced Web Footprint
        results['footprint'] = self.scan_footprint()
        
        # Comprehensive Social Media Scan
        results['social_media'] = self.scan_social_media()
        
        return results

    def generate_number_formats(self, parsed):
        number = self.number
        clean_number = ''.join(filter(str.isdigit, number))
        return {
            'raw': number,
            'clean': clean_number,
            'dashed': '-'.join([clean_number[i:i+3] for i in range(0, len(clean_number), 3)]),
            'bracketed': f"({clean_number[:3]}) {clean_number[3:6]}-{clean_number[6:]}",
            'dotted': f"+1.{clean_number[-10:-7]}.{clean_number[-7:-4]}.{clean_number[-4:]}" if not clean_number.startswith('+') else f"{clean_number[0:2]}.{clean_number[2:5]}.{clean_number[5:8]}.{clean_number[8:]}",
        }

    def perform_osint_scan(self):
        osint_results = {}
        
        search_engines = {
            'bing': 'https://www.bing.com/search',
            'duckduckgo': 'https://duckduckgo.com/html/',
            'yandex': 'https://yandex.com/search/',
            'qwant': 'https://www.qwant.com/',
            'baidu': 'https://www.baidu.com/s'
        }
        
        for engine, url in search_engines.items():
            number_formats = self.generate_number_formats(self.number)
            for format_type, number in number_formats.items():
                try:
                    params = {'q': f'"{number}"'}
                    response = requests.get(url, params=params, headers=self.headers, timeout=10)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        results = []
                        for result in soup.find_all(['h2', 'h3', 'div'], class_=['g', 'result']):
                            if result.find('a'):
                                results.append({
                                    'title': result.text.strip(),
                                    'url': result.find('a').get('href', ''),
                                    'format_used': format_type
                                })
                        osint_results[f'{engine}_{format_type}_results'] = results
                except Exception as e:
                    osint_results[f'{engine}_{format_type}_error'] = str(e)
                time.sleep(2)

        return osint_results

    def perform_deep_web_scan(self):
        # Implement deep web scanning logic
        # This is a placeholder for demonstration
        return {"status": "completed", "timestamp": datetime.now().isoformat()}

    def check_data_breaches(self):
        # Implement data breach checking logic
        # This is a placeholder for demonstration
        return {"status": "completed", "timestamp": datetime.now().isoformat()}

    def scan_footprint(self):
        footprint = {}
        number_formats = self.generate_number_formats(self.number)
        
        for format_type, number in number_formats.items():
            search_queries = [
                f'"{number}"',
                f'"{number}" contact',
                f'"{number}" profile',
                f'site:linkedin.com "{number}"',
                f'site:facebook.com "{number}"',
                f'site:twitter.com "{number}"',
                f'site:instagram.com "{number}"',
                f'site:whitepages.com "{number}"',
                f'site:yellowpages.com "{number}"',
                f'site:truepeoplesearch.com "{number}"'
            ]
            
            all_results = []
            for query in search_queries:
                try:
                    encoded_query = urllib.parse.quote(query)
                    url = f"https://www.google.com/search?q={encoded_query}"
                    response = requests.get(url, headers=self.headers, timeout=10)
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    for div in soup.find_all('div', class_=['g', 'tF2Cxc']):
                        link = div.find('a')
                        title = div.find('h3')
                        snippet = div.find('div', class_=['VwiC3b', 'yXK7lf'])
                        
                        if link and title:
                            result = {
                                'title': title.text,
                                'url': link.get('href', ''),
                                'snippet': snippet.text if snippet else '',
                                'format_used': format_type,
                                'query_used': query
                            }
                            all_results.append(result)
                    
                    time.sleep(2)
                except Exception as e:
                    footprint[f'search_error_{query}_{format_type}'] = str(e)
            
            footprint[f'search_results_{format_type}'] = all_results
        
        return footprint

    def scan_social_media(self):
        social_results = {}
        platforms = {
            'linkedin': 'https://www.linkedin.com/search/results/all/',
            'facebook': 'https://www.facebook.com/search/top/',
            'twitter': 'https://twitter.com/search',
            'instagram': 'https://www.instagram.com/explore/tags/',
            'tiktok': 'https://www.tiktok.com/search',
            'reddit': 'https://www.reddit.com/search/'
        }
        
        number_formats = self.generate_number_formats(self.number)
        
        for platform, base_url in platforms.items():
            platform_results = []
            for format_type, number in number_formats.items():
                try:
                    params = {'q': number}
                    url = f"{base_url}?q={urllib.parse.quote(number)}"
                    response = requests.get(url, headers=self.headers, timeout=10)
                    platform_results.append({
                        'format_used': format_type,
                        'status_code': response.status_code,
                        'url_checked': url
                    })
                except Exception as e:
                    platform_results.append({
                        'format_used': format_type,
                        'error': str(e)
                    })
                time.sleep(1)
            
            social_results[platform] = platform_results
        
        return social_results

def generate_ai_analysis(results, api_key):
    client = groq.Groq(api_key=api_key)
    
    initial_prompt = f"""Analyze this phone number information and create a detailed report:
    {json.dumps(results, indent=2)}
    
    Create a comprehensive analysis including:
    1. Basic Information Summary
    2. Digital Presence Analysis with confidence scores
    3. Risk Assessment and potential security implications
    4. Social Media Footprint analysis
    5. Data Verification & Cross-Reference with confidence levels
    6. Additional Findings & Patterns
    7. Temporal Analysis (Data Freshness)
    8. Recommendations and Security Concerns
    
    Perform fact-checking and validation of the provided data.
    Identify any inconsistencies or outdated information.
    Look for additional connections or patterns not captured in the initial scan.
    Assess the reliability of each data source.
    Provide confidence scores for each finding.
    Identify potential false positives or misleading information.
    Suggest additional verification steps if needed.
    
    Format as a detailed professional report with markdown headings and bullet points.
    """
    
    try:
        completion = client.chat.completions.create(
            messages=[{"role": "user", "content": initial_prompt}],
            model="mixtral-8x7b-32768",
            temperature=0.3,
            max_tokens=4000
        )
        initial_analysis = completion.choices[0].message.content
        
        verification_prompt = f"""Given the initial analysis:
        {initial_analysis}
        
        Please verify the findings and expand the analysis:
        1. Cross-reference all data points for accuracy
        2. Identify potential gaps or inconsistencies
        3. Suggest additional data sources to check
        4. Validate temporal aspects of the data
        5. Assess confidence levels for each finding
        6. Identify potential false positives
        7. Suggest verification steps for uncertain data
        8. Compare findings against known patterns
        9. Evaluate source reliability
        10. Recommend additional investigation areas
        """
        
        verification = client.chat.completions.create(
            messages=[
                {"role": "user", "content": initial_prompt},
                {"role": "assistant", "content": initial_analysis},
                {"role": "user", "content": verification_prompt}
            ],
            model="mixtral-8x7b-32768",
            temperature=0.2,
            max_tokens=4000
        )
        
        final_report = f"""# Comprehensive Phone Number Analysis Report

{initial_analysis}

## Verification and Additional Findings
{verification.choices[0].message.content}
"""
        return final_report
        
    except Exception as e:
        return f"AI Analysis Error: {str(e)}"

def main():
    st.set_page_config(page_title="Advanced Phone Number Scanner", layout="wide")
    
    st.title("🔍 Advanced Phone Number Scanner")
    st.markdown("---")
    
    with st.sidebar:
        st.header("⚙️ Configuration")
        groq_api_key = st.text_input("Groq API Key", type="password")
        
    col1, col2 = st.columns([2,1])
    
    with col1:
        phone_number = st.text_input("📱 Enter Phone Number (Any format)", placeholder="Enter phone number")
        st.caption("Supports various formats: +1-555-555-5555, (555) 555-5555, 5555555555, etc.")
        
    with col2:
        scan_button = st.button("🚀 Start Scan", type="primary")
        
    if scan_button and phone_number:
        try:
            with st.spinner("🔄 Scanning number..."):
                scanner = NumberScanner(phone_number)
                results = scanner.scan_number()
                
                st.subheader("📊 Scan Results")
                
                tabs = st.tabs(["📌 Overview", "🌐 Digital Footprint", "🔍 OSINT", "🤖 AI Analysis"])
                
                with tabs[0]:
                    st.json(results)
                    
                with tabs[1]:
                    if 'footprint' in results:
                        st.write(results['footprint'])
                        
                with tabs[2]:
                    if 'osint' in results:
                        st.write(results['osint'])
                        
                with tabs[3]:
                    if groq_api_key:
                        analysis = generate_ai_analysis(results, groq_api_key)
                        st.markdown(analysis)
                        
                        st.download_button(
                            "📥 Download Report",
                            analysis,
                            file_name=f"phone_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                        )
                    else:
                        st.warning("⚠️ Please add a Groq API key to enable AI analysis")
                        
        except Exception as e:
            st.error(f"❌ Error during scan: {str(e)}")

if __name__ == "__main__":
    main()