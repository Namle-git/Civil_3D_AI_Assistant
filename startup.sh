# Update the package list
apt-get update

# Install necessary dependencies for Chrome and ChromeDriver
apt-get install -y wget unzip curl libglib2.0-0 libnss3 libgconf-2-4 libxi6 libxcursor1 libxss1 libxcomposite1 libasound2 libxtst6 fonts-liberation libappindicator3-1 xdg-utils

# Install Chrome
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
apt-get -y install ./google-chrome-stable_current_amd64.deb

# Install ChromeDriver
CHROME_DRIVER_VERSION=`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE`
wget -N https://chromedriver.storage.googleapis.com/$CHROME_DRIVER_VERSION/chromedriver_linux64.zip
unzip chromedriver_linux64.zip -d /usr/local/bin/

streamlit run Streamlit_app.py --server.port 8000 --server.address 0.0.0.0
