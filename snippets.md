Chrome extentions
```python
from selenium import webdriver 
from selenium.webdriver.chrome.options import Options 

options = webdriver.ChromeOptions()
options.add_extension('./exampleOfExtensionDownloadedToFolder.crx')
driver = webdriver.Chrome(options=options) 
driver.get('http://www.google.com')
```