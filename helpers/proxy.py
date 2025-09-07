from selenium import webdriver
from selenium.webdriver.chrome.options import Options


opts = Options()
opts.add_extension("proxy_auth_plugin.zip")
opts.add_argument(f"--proxy-server=http://mx.smartproxy.com:20000")


driver = webdriver.Chrome(options=opts)
driver.get("https://httpbin.org/ip")
print(driver.page_source)
driver.quit()
