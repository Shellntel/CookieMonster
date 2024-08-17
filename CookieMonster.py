import json
import argparse
from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
import tldextract
import whois
import pandas as pd
from urllib.parse import urlparse
from collections import defaultdict
from prettytable import PrettyTable

def load_tracking_patterns(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

def get_cookies_with_selenium(url, take_screenshot=False, verbose=False):
    try:
        # Start Xvfb to simulate a display environment
        display = Display(visible=0, size=(1024, 768))
        display.start()

        # Set Chrome options for headless mode
        options = Options()
        options.headless = True
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--remote-debugging-port=9222')
        options.add_argument('--disable-software-rasterizer')

        # Ensure third-party cookies are allowed
        options.add_argument('--disable-features=SameSiteByDefaultCookies')
        options.add_argument('--disable-features=CookiesWithoutSameSiteMustBeSecure')
        options.add_argument('--allow-insecure-localhost')
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-features=BlockThirdPartyCookies')

        print(f"Opening Chrome to visit {url}")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

        # Set timeouts to avoid getting stuck
        driver.set_page_load_timeout(30)  # 30 seconds timeout for page load
        driver.set_script_timeout(30)  # 30 seconds timeout for scripts

        # Clear any existing cookies to ensure no persistence between sessions
        driver.delete_all_cookies()
        print("Cleared all cookies from the session.")

        try:
            # Visit the URL
            driver.get(url)
        except TimeoutException:
            print(f"Page load timeout for URL: {url}")
            driver.quit()
            display.stop()
            return None, None

        # Log the final URL after redirection
        final_url = driver.current_url
        print(f"Final URL after redirection: {final_url}")

        # Take a screenshot if the flag is set
        if take_screenshot:
            screenshot_path = "screenshot.png"
            driver.save_screenshot(screenshot_path)
            print(f"Screenshot saved to {screenshot_path}")

        # Log browser console errors if in verbose mode
        if verbose:
            logs = driver.get_log("browser")
            if logs:
                print("Browser console logs:")
                for entry in logs:
                    print(entry)
            else:
                print("No browser console errors detected.")

        # Retrieve cookies
        cookies = driver.get_cookies()

        driver.quit()
        display.stop()

        return final_url, cookies

    except WebDriverException as e:
        # Handle DNS resolution errors like 'ERR_NAME_NOT_RESOLVED'
        if "ERR_NAME_NOT_RESOLVED" in str(e):
            print(f"DNS resolution error: {url} could not be resolved.")
        else:
            print(f"An error occurred while trying to access {url}: {str(e)}")
        return None, None

def categorize_cookies(cookies, domain, tracking_patterns):
    first_party_cookies = []
    third_party_cookies = []
    third_party_tracking_cookies = []
    summary_counts = defaultdict(int)

    extracted_domain = tldextract.extract(domain).registered_domain

    if cookies is None:
        return first_party_cookies, third_party_cookies, third_party_tracking_cookies, summary_counts

    for cookie in cookies:
        cookie_domain = tldextract.extract(cookie['domain']).registered_domain

        # Check if the cookie is a known tracking cookie set via JS
        tracking_service = None
        friendly_name = None
        for service, details in tracking_patterns.items():
            patterns = details.get("patterns", [])
            for pattern in patterns:
                if len(pattern) == 3 and pattern[0] in cookie['name']:
                    tracking_service = service
                    friendly_name = pattern[1]
                    summary_counts[f"{friendly_name} ({service})"] += 1
                    break
            if tracking_service:
                break

        if tracking_service:
            third_party_tracking_cookies.append({
                "name": cookie['name'],
                "value": cookie['value'],
                "domain": cookie['domain'],
                "service": friendly_name
            })
        elif cookie_domain == extracted_domain:
            first_party_cookies.append(cookie)
        else:
            third_party_cookies.append(cookie)

    return first_party_cookies, third_party_cookies, third_party_tracking_cookies, summary_counts

def get_vendor_info(cookie_domain):
    try:
        w = whois.whois(cookie_domain)
        vendor = w.org if w.org else 'Unknown'
        return vendor
    except Exception as e:
        return 'Unknown'

def process_url(url, tracking_patterns, take_screenshot=False, verbose=False):
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    final_url, cookies = get_cookies_with_selenium(url, take_screenshot=take_screenshot, verbose=verbose)
    if final_url is None:
        return url, None, None, None, None, None

    parsed_url = urlparse(final_url)

    domain = parsed_url.hostname
    if parsed_url.port:
        domain += f":{parsed_url.port}"

    first_party_cookies, third_party_cookies, third_party_tracking_cookies, summary_counts = categorize_cookies(cookies, domain, tracking_patterns)

    if verbose:
        print(f"Debugging Information: Final URL: {final_url}, Domain: {domain}")
        print(f"Cookies Retrieved: {cookies}")

    return url, final_url, first_party_cookies, third_party_cookies, third_party_tracking_cookies, summary_counts

def print_summary_table(summary_counts):
    table = PrettyTable()
    table.field_names = ["Count", "Name (Service)"]

    # Sort summary counts from highest to lowest
    sorted_summary_counts = sorted(summary_counts.items(), key=lambda item: item[1], reverse=True)

    for name, count in sorted_summary_counts:
        table.add_row([count, name])

    print("\nSummary of Tracking Patterns:")
    print(table)

def print_categorized_cookies(url, final_url, first_party_cookies, third_party_cookies, third_party_tracking_cookies):
    if final_url is None:
        return

    print(f"\nGenerating report for {url}")
    print(f"Final URL after redirection: {final_url}")
    print("="*40)

    print("First-party Cookies:")
    if first_party_cookies:
        for cookie in first_party_cookies:
            print(f"- {cookie['name']}: {cookie['value']}")
    else:
        print("No First-party Cookies found.")

    print("\nThird-party Cookies:")
    if third_party_cookies:
        for cookie in third_party_cookies:
            vendor = get_vendor_info(cookie['domain'])
            print(f"- {cookie['name']}: {cookie['value']} (Domain: {cookie['domain']}, Vendor: {vendor})")
    else:
        print("No Third-party Cookies found.")

    print("\nThird-party Tracking Cookies Loaded Through JS as First-party Cookies:")
    if third_party_tracking_cookies:
        for cookie in third_party_tracking_cookies:
            print(f"- {cookie['name']}: {cookie['value']} (Domain: {cookie['domain']}, Service: {cookie['service']})")
    else:
        print("No Third-party Tracking Cookies found.")

def print_and_save_report(results, summary=False):
    report = []
    overall_summary_counts = defaultdict(int)

    for url, final_url, first_party_cookies, third_party_cookies, third_party_tracking_cookies, summary_counts in results:
        if final_url is None:
            continue

        print_categorized_cookies(url, final_url, first_party_cookies, third_party_cookies, third_party_tracking_cookies)

        for cookie in first_party_cookies:
            report.append([url, final_url, "First-party", cookie['name'], cookie['value'], cookie['domain'], "N/A", "N/A"])

        for cookie in third_party_cookies:
            vendor = get_vendor_info(cookie['domain'])
            report.append([url, final_url, "Third-party", cookie['name'], cookie['value'], cookie['domain'], vendor, "N/A"])

        for cookie in third_party_tracking_cookies:
            report.append([url, final_url, "3rd Party Tracking", cookie['name'], cookie['value'], cookie['domain'], cookie['service'], "Tracking"])

        # Aggregate summary counts across all URLs
        for key, count in summary_counts.items():
            overall_summary_counts[key] += count

    df = pd.DataFrame(report, columns=["Original URL", "Final URL", "Type", "Cookie Name", "Cookie Value", "Domain", "Vendor/Service", "Purpose"])
    csv_filename = "cookie_report.csv"
    df.to_csv(csv_filename, index=False)
    print(f"\nReport saved to {csv_filename}")

    if summary:
        print_summary_table(overall_summary_counts)

def main():
    parser = argparse.ArgumentParser(description="CookieMonster: A tool for discovering and categorizing cookies set by websites.")
    parser.add_argument("url_or_file", help="The URL to scrape or a file containing a list of URLs.")
    parser.add_argument("-s", "--screenshot", action="store_true", help="Take a screenshot of the website.")
    parser.add_argument("-r", "--report", action="store_true", help="Generate a summary report of tracking patterns.")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose mode for debugging.")
    parser.add_argument("-f", "--file", action="store_true", help="Indicates that the input is a file containing a list of URLs.")
    
    args = parser.parse_args()

    tracking_patterns = load_tracking_patterns('tracking_cookie_patterns.json')
    results = []

    if args.file:
        with open(args.url_or_file, 'r') as file:
            urls = file.read().splitlines()
            for url in urls:
                result = process_url(url, tracking_patterns, take_screenshot=args.screenshot, verbose=args.verbose)
                results.append(result)
    else:
        url = args.url_or_file
        result = process_url(url, tracking_patterns, take_screenshot=args.screenshot, verbose=args.verbose)
        results.append(result)

    # Generate and save the report for all URLs
    print_and_save_report(results, summary=args.report)

if __name__ == "__main__":
    main()

