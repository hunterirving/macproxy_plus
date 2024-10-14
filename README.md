## MacProxy Plus

This fork of <a href="https://github.com/rdmark/macproxy">MacProxy</a> adds support for 'extensions', which intercept requests for specific domains and serve simple HTML interfaces, making it possible to browse the modern web from vintage hardware.

### Demonstration Video (on YouTube)

<a href="https://youtu.be/f1v1gWLHcOk" target="_blank">
  <img src="./readme_images/youtube_thumbnail.jpg" alt="Teaching an Old Mac New Tricks" width="400">
</a>

### Extensions

Each extension has its own folder within the `extensions` directory. Extensions can be individually enabled or disabled via a `config.py` file in the root of the `extensions` directory.

To enable extensions:

1. In the ```extensions``` directory, rename ```config.py.example``` to ```config.py``` :

	```shell
	mv extensions/config.py.example extensions/config.py
	```

2. In ```config.py```, enable/disable extensions by uncommenting/commenting lines in the ```ENABLED_EXTENSIONS``` list:

	```python
	ENABLED_EXTENSIONS = [
		#disabled_extension,
		"enabled_extension"
		]
	```

### Running MacProxy Plus

Run the ```start_macproxy.sh``` script. If an enabled extension relies on any external packages, ```start_macproxy.sh``` will automatically install them from the extension's included ```requirements.txt``` file.

```shell
./start_macproxy.sh
```

### Example Extension: ChatGPT

A ChatGPT extension is provided as an example. This extension serves a simple web interface that lets users interact with OpenAI's GPT models.

To enable the ChatGPT extension, open ```extensions/config.py```, uncomment the ```chatgpt``` line in the ```ENABLED_EXTENSIONS``` list, and replace ```YOUR_OPENAI_API_KEY_HERE``` with your actual OpenAI API key.

```python
open_ai_api_key = "YOUR_OPENAI_API_KEY_HERE"

ENABLED_EXTENSIONS = [
	"chatgpt"
]
```

Once enabled, Macproxy will reroute requests to ```http://chatgpt.com``` to this inteface.

<img src="readme_images/macintosh_plus.jpg">

### Other Extensions

#### Claude (Anthropic)
For the discerning LLM connoisseur.

#### Weather
Get the forecast for any zip code in the US.

#### Wikipedia
Read any of over 6 million encyclopedia articles - complete with clickable links and search function.

#### Reddit
Browse any subreddit or the Reddit homepage, with support for nested comments and downloadable images... in dithered black and white.

#### WayBack Machine
Enter any date between January 1st, 1996 and today, then browse the web as it existed at that point in time. Includes full download support for images and other files backed up by the Internet Archive.

#### Web Simulator
Type a URL that doesn't exist into the address bar, and Anthropic's Claude 3.5 Sonnet will interpret the domain and any query parameters to generate an imagined version of that page on the fly. Each HTTP request is serialized and sent to the AI, along with the full HTML of the last 3 pages you visited, allowing you to explore a vast, interconnected, alternate reality Internet where the only limit is your imagination.

#### (not) YouTube
A legally distinct parody of YouTube, which uses the fantastic homebrew application <a href="https://www.macflim.com/macflim2/">MacFlim</a> (created by Fred Stark) to encode video files as a series of dithered black and white frames.

#### Hackaday
Serves a pared-down, text-only version of hackaday.com, complete with articles, comments, and search functionality.

#### npr.org
Serves articles from the text-only version of the site (```text.npr.org```) and transforms relative urls into absolute urls for compatibility with MacWeb 2.0.

#### wiby.me
Browse Wiby's collection of personal, handmade webpages (fixes an issue where clicking "surprise me..." would not redirect users to their final destination).

<hr>

#### (pre-fork version of the readme follows below)

<hr>

## Macproxy 

A simple HTTP proxy script for putting early computers on the Web. Despite its name, there is nothing Mac specific about this proxy. It was originally designed with compatibility with the MacWeb web browser in mind, but has been tested on a variety of vintage web browsers since.

The proxy.py script runs a Flask server that takes all requests and proxies them, using html_utils.py to strip tags that are incompatible with, or pulls in contents that aren't parsable by old browsers such as Netscape 4 or MacWeb.

The proxy server listens to port 5001 by default, but the port number can be changed using a command line parameter.

## Requirements
Python3 for running the script, venv if you want to use the virtual environment, or pip if you want to install libraries manually.

```
sudo apt install python3 python3-venv python3-pip
```

## Usage
The start_macproxy.sh shell script will create and manage a venv Python environment, and if successful launch the proxy script.

```
./start_macproxy.sh
```

Launch with a specific port number (defaults to port 5000):

```
./start_macproxy.sh --port=5001
```

You may also start the Python script by itself, using system Python.

```
pip3 install -r requirements.txt
python3 proxy.py
```

Launch with a specific port number:

```
python3 proxy.py --port 5001
```

## Advanced Options
Use the advanced options to change how Macproxy presents itself to the web, and how it processes the data it gets back.

By default, Macproxy will forward the actual User-Agent string of the originating browser in its request headers. This option overrides this with an arbitrary string, allowing you to spoof as any browser. For instance, Opera Mini 8.0 for J2ME:

```
python3 proxy.py --user-agent "Opera/9.80 (J2ME/MIDP; Opera Mini/8.0.35158/36.2534; U; en) Presto/2.12.423 Version/12.16"
```

Selects the BeatifulSoup html formatter that Macproxy will use, e.g. the minimal formatter:
```
python3 proxy.py --html-formatter minimal
```

Turns off the conversion of select typographic symbols to ASCII characters:
```
python3 proxy.py --disable-char-conversion
```

Refer to Macproxy's helptext for more details:
```
python3 proxy.py -h
```

## systemd service
This repo comes with a systemd service configuration template. At the time of writing, systemd is the de-facto standard solution for managing daemons on contemporary Linux distributions.
Edit the macproxy.service file and point the ExecStart= parameter to the location of the start_macproxy.sh file, e.g. on a Raspberry Pi:

```
ExecStart=/home/pi/macproxy/start_macproxy.sh
```

Then copy the service file to /etc/systemd/system and enable the service:

```
sudo cp macproxy.service /etc/systemd/system/
sudo systemctl enable macproxy
sudo systemctl daemon-reload
sudo systemctl start macproxy
```
