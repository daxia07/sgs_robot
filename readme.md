# Script to play SGSOL
### This script login in via H5 web page and then play in practice mode

### Deploy on Ubuntu VM
1. Install ChromeDriver

    ```bash
    sudo apt install sudo apt-get install chromium-chromedriver
    # check with whereis chromedriver
    ```

2. Update the path for linux platform
3. Activate the venv by
    ```bash
    # if hasn't been installed, install the venv
    pipenv install
    pipenv shell
    ```
4. Run the main script
    ```bash
    python main.py
    ```