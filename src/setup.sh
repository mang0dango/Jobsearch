#!/bin/bash
# Check if any required packages are missing and install them as needed.

install_python_packages () {
    if ! pipenv --venv >/dev/null 2>&1; then

    	echo "Installing Python dependencies..."

	pipenv sync

    fi
}

install_playwright_chromium () {
    if [ ! -d "$HOME/.cache/ms-playwright" ]; then

        echo "Installing Playwright Chromium..."
        
	pipenv run playwright install chromium

    fi
}

install_chrome_for_selenium () {
    if ! command -v google-chrome >/dev/null 2>&1; then
    
	echo "Google Chrome not found. Installing..."

	wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb

	sudo apt install -y ./google-chrome-stable_current_amd64.deb

	rm google-chrome-stable_current_amd64.deb

    fi
}

install_matching_chrome_driver() {
    if ! command -v chromedriver >/dev/null 2>&1; then

        echo "ChromeDriver not found. Installing matching version..."

        CHROME_VERSION=$(google-chrome --version | grep -oP '\d+' | head -1)

        DRIVER_VERSION=$(curl -s "https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_$CHROME_VERSION")

        wget -O chromedriver.zip \
        "https://storage.googleapis.com/chrome-for-testing-public/$DRIVER_VERSION/linux64/chromedriver-linux64.zip"

        unzip chromedriver.zip

        sudo mv chromedriver-linux64/chromedriver /usr/local/bin/

        sudo chmod +x /usr/local/bin/chromedriver

        rm -rf chromedriver.zip chromedriver-linux64
    
    fi
}

install_python_packages

install_playwright_chromium

install_chrome_for_selenium

install_matching_chrome_driver

echo "All needed prerequisites are met."

