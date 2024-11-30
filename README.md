# linkaBot
Twitter, Mastodon, Bluesky and Telegram bot for https://AireLib.re

more info in https://github.com/melizeche/AireLibre

## Requirements

* Python 3.8+
* Chromium Webdriver

## Prerequisites
You can download the Chromium Webdriver from https://chromedriver.chromium.org/downloads or install via package manager.

### Ubuntu
```bash
sudo apt install chromium-chromedriver
```

### Arch/Manjaro
```bash
sudo pacman -S chromium
```

### MacOS
```bash
brew install chromedriver
```

## Install

```
git clone git@github.com:melizeche/linkaBot.git
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
python bot.py
```

### Crontab format and example

MIN 	HOUR 	DAYofMONTH 	MONTH 	DAYofWEEK 	PYTHONPATH SCRIPT

 For check and tweet  at 8am, 12pm and 6pm everyday

```0      8,12,18    * * * /apps/linkaBot/env/bin/python /apps/linkaBot/bot.py```

## Contributing

1. Fork it!
2. Create your feature branch: `git checkout -b my-new-feature`
3. Commit your changes: `git commit -am 'Add some feature'`
4. Push to the branch: `git push origin my-new-feature`
5. Submit a pull request :D

## Author

* Marcelo Elizeche Landó https://github.com/melizeche

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.