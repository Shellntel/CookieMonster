
![alt text](https://github.com/njoyzrd/CookieMonster/blob/main/CookieMonster.png?raw=true)

# CookieMonster

CookieMonster is a tool designed to discover and categorize cookies set by websites. It utilizes a headless Chrome browser to visit a given URL (or URLs from a file), extract cookies, categorize them into first-party, third-party, and third-party tracking cookies, and then optionally generates a summary report.

## Installation

Ensure that you have Python 3 installed. You'll also need to install the necessary Python packages listed in the `requirements.txt` file. You can install them using pip:

```bash
pip install -r requirements.txt
```

### Headless Chrome Setup

To run Chrome in headless mode, you need to have Google Chrome and `chromedriver` installed on your system. Here's how you can set them up on Ubuntu:

1. **Install Google Chrome**:
    ```bash
    wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
    sudo apt install ./google-chrome-stable_current_amd64.deb
    ```

2. **Install `chromedriver`**:
    `webdriver-manager` will automatically download the correct version of `chromedriver` when you run the script, so no additional installation steps are needed.

3. **Install Xvfb** (to simulate a display environment):
    ```bash
    sudo apt-get install -y xvfb
    ```

## Usage

```bash
python3 CookieMonster.py [URL or file] [options]
```

### Arguments

- `URL or file`: The URL of the website to analyze or a file containing a list of URLs to analyze.

### Options

- `-s, --screenshot`: Take a screenshot of the website.
- `-r, --report`: Generate a summary report of tracking patterns.
- `-v, --verbose`: Enable verbose mode for debugging (shows browser console logs and internal variables).
- `-f, --file`: Indicates that the input is a file containing a list of URLs.

### Examples

1. **Analyze a single URL and take a screenshot**:
   ```bash
   python3 CookieMonster.py https://www.example.com -s
   ```

2. **Analyze a list of URLs from a file and generate a summary report**:
   ```bash
   python3 CookieMonster.py urls.txt -f -r
   ```

3. **Analyze a single URL with verbose mode enabled**:
   ```bash
   python3 CookieMonster.py https://www.example.com -v
   ```

4. **Analyze a file of URLs with both verbose mode and a summary report**:
   ```bash
   python3 CookieMonster.py urls.txt -f -v -r
   ```

## Tracking Cookie Patterns

The script uses a `tracking_cookie_patterns.json` file to identify and categorize tracking cookies. This file contains patterns of known tracking cookies along with their friendly names and descriptions. You can customize this file to add or update patterns as needed.

### Example `tracking_cookie_patterns.json` Structure:

```json
{
    "Google Analytics": {
        "description": "Google Analytics is a web analytics service offered by Google that tracks and reports website traffic.",
        "patterns": [
            ["_ga", "Google Analytics", "Used to distinguish users."],
            ["_gid", "Google Analytics", "Used to distinguish users."]
        ]
    },
    ...
}
```

## Output

The script will print categorized cookies to the console, and if the `-r` option is used, it will generate a summary report sorted by the most common tracking patterns. The output is also saved to a CSV file named `cookie_report.csv`.

If the `-s` option is used, a screenshot of the visited website is saved as `screenshot.png`.

## License

This project is licensed under the MIT License.
