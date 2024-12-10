
import streamlit as st
import phonenumbers
from phonenumbers import geocoder, carrier, timezone
import requests
from bs4 import BeautifulSoup
import json
import groq
from datetime import datetime
import re
import urllib.parse
import warnings
import sys

class NumberScanner:
    def __init__(self, number):
        self.number = number
        self.apis = {
            'numverify': 'http://apilayer.net/api/validate',
            'googlesearch': 'https://www.google.com/search?q=',
            'truecaller': 'https://www.truecaller.com/search/',
            'ovh': 'https://api.ovh.com/1.0/telephony/number/detailedZones',
            'hlr-lookups': 'https://www.hlr-lookups.com/en/api/number/',
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
            results['line_type'] = self.get_number_type(parsed)
        except Exception as e:
            results['error'] = str(e)
            
        # Web Footprint
        results['footprint'] = self.scan_footprint()
        
        # Reputation Scan
        results['reputation'] = self.scan_reputation()
        
        return results
    
    def get_number_type(self, parsed_number):
        number_type = phonenumbers.number_type(parsed_number)
        type_map = {
            phonenumbers.PhoneNumberType.MOBILE: "Mobile",
            phonenumbers.PhoneNumberType.FIXED_LINE: "Fixed Line",
            phonenumbers.PhoneNumberType.FIXED_LINE_OR_MOBILE: "Fixed Line or Mobile",
            phonenumbers.PhoneNumberType.VOIP: "VOIP",
            phonenumbers.PhoneNumberType.TOLL_FREE: "Toll Free",
        }
        return type_map.get(number_type, "Unknown")
        
    def scan_footprint(self):
        footprint = {}
        
        # Google Search
        search_query = f"{self.number} OR \"{self.number}\" OR '+{self.number}'"
        encoded_query = urllib.parse.quote(search_query)
        url = f"{self.apis['googlesearch']}{encoded_query}"
        
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            results = []
            for div in soup.find_all('div', class_='g'):
                link = div.find('a')
                if link:
                    title = div.find('h3')
                    snippet = div.find('div', class_='VwiC3b')
                    if title and snippet:
                        results.append({
                            'title': title.text,
                            'url': link['href'],
                            'snippet': snippet.text
                        })
            
            footprint['google_results'] = results[:5]
        except Exception as e:
            footprint['google_error'] = str(e)
            
        return footprint
        
    def scan_reputation(self):
        reputation = {}
        
        # Custom reputation checks
        spam_apis = [
            f"https://api.scamalytics.com/phone/{self.number}",
            f"https://api.spamcalls.net/lookup/{self.number}",
        ]
        
        for api in spam_apis:
            try:
                response = requests.get(api)
                if response.status_code == 200:
                    reputation[api.split('/')[2]] = response.json()
            except:
                continue
                
        return reputation

def generate_ai_analysis(results, api_key):
    client = groq.Groq(api_key=api_key)
    prompt = f"""Analyze this phone number information and create a detailed report:
    {json.dumps(results, indent=2)}
    
    Include:
    1. Number validity and basic information
    2. Digital footprint analysis
    3. Reputation assessment
    4. Risk evaluation
    5. Recommendations
    
    Format in markdown with sections and bullet points.
    """
    
    completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="mixtral-8x7b-32768",
        temperature=0.3,
    )
    
    return completion.choices[0].message.content

def main():
    st.set_page_config(page_title="Advanced PhoneInfoga", layout="wide")
    
    st.title("PhoneInfoga Advanced Scanner")
    st.markdown("---")
    
    with st.sidebar:
        st.header("Configuration")
        groq_api_key = st.text_input("Groq API Key", type="password")
        
    col1, col2 = st.columns([2,1])
    
    with col1:
        phone_number = st.text_input("Enter Phone Number (E.164 format)", placeholder="+1234567890")
        
    with col2:
        scan_button = st.button("Start Scan", type="primary")
        
    if scan_button and phone_number:
        try:
            with st.spinner("Scanning number..."):
                scanner = NumberScanner(phone_number)
                results = scanner.scan_number()
                
                # Display results
                st.subheader("Scan Results")
                
                tabs = st.tabs(["Overview", "Digital Footprint", "Reputation", "AI Analysis"])
                
                with tabs[0]:
                    st.json(results)
                    
                with tabs[1]:
                    if 'footprint' in results:
                        st.write(results['footprint'])
                        
                with tabs[2]:
                    if 'reputation' in results:
                        st.write(results['reputation'])
                        
                with tabs[3]:
                    if groq_api_key:
                        analysis = generate_ai_analysis(results, groq_api_key)
                        st.markdown(analysis)
                        
                        # Export options
                        st.download_button(
                            "Download Report (MD)",
                            analysis,
                            file_name=f"phone_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                        )
                    else:
                        st.warning("Please add a Groq API key to enable AI analysis")
                        
        except Exception as e:
            st.error(f"Error during scan: {str(e)}")
    
if __name__ == "__main__":
    main()
