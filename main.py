import streamlit as st
import phonenumbers
from phonenumbers import geocoder, carrier, timezone
import requests
from bs4 import BeautifulSoup
import json
import groq
import tempfile
from datetime import datetime

class AdvancedPhoneInfoga:
    def __init__(self, phone_number, region=None):
        self.phone_number = phone_number
        self.parsed_number = phonenumbers.parse(phone_number, region)
        self.results = {}
        self.rate_limit = {'count': 0, 'max_requests': 100}

    def check_rate_limit(self):
        self.rate_limit['count'] += 1
        return self.rate_limit['count'] <= self.rate_limit['max_requests']

    def get_line_type(self):
        number_type = phonenumbers.number_type(self.parsed_number)
        type_map = {
            0: "UNKNOWN",
            1: "MOBILE",
            2: "LANDLINE",
            3: "VOIP"
        }
        self.results['LineType'] = type_map.get(number_type, "UNKNOWN")

    def validate_number(self):
        return phonenumbers.is_valid_number(self.parsed_number)

    def get_basic_info(self):
        self.results['Country'] = geocoder.description_for_number(self.parsed_number, "en")
        self.results['Carrier'] = carrier.name_for_number(self.parsed_number, "en")
        self.results['Timezone'] = timezone.time_zones_for_number(self.parsed_number)

    def lookup_via_api(self):
        api_urls = [
            f"https://api.numlookupapi.com/v1/validate/{self.phone_number}",
            f"https://api.apilayer.com/number_verification/{self.phone_number}",
        ]
        headers = {
            "User-Agent": "AdvancedPhoneInfoga/1.0",
        }

        for url in api_urls:
            try:
                response = requests.get(url, headers=headers)
                if response.status_code == 200:
                    self.results['APILookup'] = json.loads(response.text)
                else:
                    self.results['APIError'] = f"Error {response.status_code}: Unable to fetch data."
            except Exception as e:
                self.results['APIError'] = str(e)

    def web_scrape_info(self):
        search_url = f"https://www.google.com/search?q={self.phone_number}+phone+directory"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(search_url, headers=headers)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            snippets = [snip.text for snip in soup.find_all('span')]
            self.results['WebScraping'] = snippets[:5]

    def dark_web_scan(self):
        self.results['DarkWebScan'] = "Simulated dark web scan completed. No actual data retrieved."

    def run(self):
        if not self.validate_number():
            return {"Error": "Invalid phone number format"}

        if not self.check_rate_limit():
            return {"Error": "Rate limit exceeded"}

        self.get_basic_info()
        self.get_line_type()
        self.lookup_via_api()
        self.web_scrape_info()
        self.dark_web_scan()

        risk_score = 0
        if self.results.get('LineType') == "VOIP":
            risk_score += 50
        if not self.results.get('Carrier'):
            risk_score += 30

        self.results['RiskScore'] = risk_score
        return self.results

def generate_ai_analysis(results, api_key):
    """Generate AI analysis using Groq"""
    client = groq.Groq(api_key=api_key)
    prompt = f"""Analyze the following phone number information and create a detailed markdown report:
    {json.dumps(results, indent=2)}

    Focus on:
    1. Basic Information
    2. Risk Assessment
    3. Key Findings
    4. Recommendations

    Format the response in markdown with proper headers, lists, and tables where appropriate.
    """

    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="mixtral-8x7b-32768",
        temperature=0.3,
    )

    return chat_completion.choices[0].message.content

def main():
    st.set_page_config(page_title="Advanced PhoneInfoga", layout="wide")
    st.title("Advanced PhoneInfoga Tool")

    # Sidebar for API key
    with st.sidebar:
        st.header("Configuration")
        groq_api_key = st.text_input("Enter Groq API Key", type="password")

    # Main content
    phone_number = st.text_input("Enter phone number (with country code, e.g., +1xxxxxxxxxx):")
    region = st.selectbox("Select default region:", ["US", "GB", "IN", "CA", "AU"])

    if st.button("Analyze Number"):
        if phone_number:
            with st.spinner("Analyzing phone number..."):
                tool = AdvancedPhoneInfoga(phone_number, region=region)
                results = tool.run()

                # Display raw results in expandable section
                with st.expander("Raw Results"):
                    st.json(results)

                # Generate and display AI analysis
                if groq_api_key:
                    analysis = generate_ai_analysis(results, groq_api_key)
                    st.markdown(analysis)

                    # Download buttons
                    st.download_button(
                        "Download Report (MD)",
                        analysis,
                        file_name=f"phone_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                    )

                    st.download_button(
                        "Download Report (TXT)",
                        analysis,
                        file_name=f"phone_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                    )
                else:
                    st.warning("Please enter a Groq API key in the sidebar to enable AI analysis")
        else:
            st.error("Please enter a phone number")

if __name__ == "__main__":
    main()