
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

class NumberScanner:
    def __init__(self, number):
        self.number = number
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def scan_number(self):
        results = {}
        
        # Basic Info
        try:
            parsed = phonenumbers.parse(self.number)
            results['valid'] = phonenumbers.is_valid_number(parsed)
            results['formatted'] = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
            results['country'] = geocoder.description_for_number(parsed, "en")
            results['carrier'] = carrier.name_for_number(parsed, "en")
            results['timezones'] = timezone.time_zones_for_number(parsed)
            results['line_type'] = self.get_number_type(parsed)
            results['region'] = phonenumbers.region_code_for_number(parsed)
        except Exception as e:
            results['error'] = f"Basic info error: {str(e)}"

        # OSINT Scans
        results['osint'] = self.perform_osint_scan()
        
        # Web Footprint
        results['footprint'] = self.scan_footprint()
        
        # Social Media Scan
        results['social_media'] = self.scan_social_media()
        
        return results

    def get_number_type(self, parsed_number):
        number_type = phonenumbers.number_type(parsed_number)
        type_map = {
            phonenumbers.PhoneNumberType.MOBILE: "Mobile",
            phonenumbers.PhoneNumberType.FIXED_LINE: "Fixed Line",
            phonenumbers.PhoneNumberType.FIXED_LINE_OR_MOBILE: "Fixed Line or Mobile",
            phonenumbers.PhoneNumberType.VOIP: "VOIP",
            phonenumbers.PhoneNumberType.TOLL_FREE: "Toll Free",
            phonenumbers.PhoneNumberType.PREMIUM_RATE: "Premium Rate",
            phonenumbers.PhoneNumberType.SHARED_COST: "Shared Cost",
            phonenumbers.PhoneNumberType.PERSONAL_NUMBER: "Personal Number",
            phonenumbers.PhoneNumberType.PAGER: "Pager",
            phonenumbers.PhoneNumberType.UAN: "UAN",
            phonenumbers.PhoneNumberType.UNKNOWN: "Unknown"
        }
        return type_map.get(number_type, "Unknown")

    def perform_osint_scan(self):
        osint_results = {}
        
        # Additional search engines
        search_engines = {
            'bing': 'https://www.bing.com/search',
            'duckduckgo': 'https://duckduckgo.com/html/',
            'yandex': 'https://yandex.com/search/'
        }
        
        for engine, url in search_engines.items():
            try:
                params = {'q': self.number}
                response = requests.get(url, params=params, headers=self.headers)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    results = []
                    for result in soup.find_all(['h2', 'h3']):
                        if result.find('a'):
                            results.append({
                                'title': result.text.strip(),
                                'url': result.find('a').get('href', '')
                            })
                    osint_results[f'{engine}_results'] = results
            except Exception as e:
                osint_results[f'{engine}_error'] = str(e)
            time.sleep(2)

        # Business directories
        directories = [
            'yellowpages.com', 'bbb.org', 'yelp.com',
            'chamberofcommerce.com', 'manta.com'
        ]
        
        for directory in directories:
            try:
                url = f"https://www.{directory}/search"
                response = requests.get(url, params={'q': self.number}, headers=self.headers)
                if response.status_code == 200:
                    osint_results[f'{directory}_found'] = True
            except Exception as e:
                osint_results[f'{directory}_error'] = str(e)
            time.sleep(1)

        return osint_results

    def scan_footprint(self):
        footprint = {}
        
        # Google Search
        clean_number = ''.join(filter(str.isdigit, self.number))
        search_queries = [
            f"\"{clean_number}\"",
            f"\"+{clean_number}\"",
            f"site:linkedin.com \"{clean_number}\"",
            f"site:facebook.com \"{clean_number}\"",
            f"site:whitepages.com \"{clean_number}\""
        ]
        
        all_results = []
        for query in search_queries:
            try:
                encoded_query = urllib.parse.quote(query)
                url = f"https://www.google.com/search?q={encoded_query}"
                response = requests.get(url, headers=self.headers)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                for div in soup.find_all('div', class_=['g', 'tF2Cxc']):
                    link = div.find('a')
                    title = div.find('h3')
                    snippet = div.find('div', class_=['VwiC3b', 'yXK7lf'])
                    
                    if link and title:
                        result = {
                            'title': title.text,
                            'url': link.get('href', ''),
                            'snippet': snippet.text if snippet else ''
                        }
                        all_results.append(result)
                
                time.sleep(2)  # Respect rate limits
            except Exception as e:
                footprint[f'search_error_{query}'] = str(e)
        
        footprint['search_results'] = all_results
        return footprint

    def scan_social_media(self):
        social_results = {}
        platforms = ['linkedin', 'facebook', 'twitter', 'instagram']
        
        for platform in platforms:
            try:
                url = f"https://www.{platform}.com/search?q={self.number}"
                response = requests.get(url, headers=self.headers)
                social_results[platform] = {
                    'status_code': response.status_code,
                    'url_checked': url
                }
            except Exception as e:
                social_results[f'{platform}_error'] = str(e)
            time.sleep(1)
        
        return social_results

def generate_ai_analysis(results, api_key):
    client = groq.Groq(api_key=api_key)
    
    initial_prompt = f"""Analyze this phone number information and create a detailed report:
    {json.dumps(results, indent=2)}
    
    Create a comprehensive analysis including:
    1. Basic Information Summary
    2. Digital Presence Analysis
    3. Risk Assessment
    4. Social Media Footprint
    5. Data Verification & Cross-Reference
    6. Additional Findings & Patterns
    7. Temporal Analysis (Data Freshness)
    8. Recommendations and Security Concerns
    
    Perform fact-checking and validation of the provided data.
    Identify any inconsistencies or outdated information.
    Look for additional connections or patterns not captured in the initial scan.
    Assess the reliability of each data source.
    
    Format as a detailed professional report with markdown headings and bullet points.
    """
    
    try:
        # Initial analysis
        completion = client.chat.completions.create(
            messages=[{"role": "user", "content": initial_prompt}],
            model="mixtral-8x7b-32768",
            temperature=0.3,
            max_tokens=2000
        )
        initial_analysis = completion.choices[0].message.content
        
        # Secondary verification prompt
        verification_prompt = f"""Given the initial analysis:
        {initial_analysis}
        
        Please verify the findings and expand the analysis:
        1. Cross-reference the data points
        2. Identify any potential gaps or inconsistencies
        3. Suggest additional data sources to check
        4. Validate temporal aspects of the data
        5. Assess confidence levels for each finding
        """
        
        verification = client.chat.completions.create(
            messages=[
                {"role": "user", "content": initial_prompt},
                {"role": "assistant", "content": initial_analysis},
                {"role": "user", "content": verification_prompt}
            ],
            model="mixtral-8x7b-32768",
            temperature=0.2,
            max_tokens=2000
        )
        
        final_report = f"""# Comprehensive Phone Number Analysis Report

{initial_analysis}

## Verification and Additional Findings
{verification.choices[0].message.content}
"""
        return final_report
        
    except Exception as e:
        return f"AI Analysis Error: {str(e)}"
    
    try:
        completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="mixtral-8x7b-32768",
            temperature=0.3,
            max_tokens=2000
        )
        return completion.choices[0].message.content
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
        phone_number = st.text_input("📱 Enter Phone Number (E.164 format)", placeholder="+1234567890")
        
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
