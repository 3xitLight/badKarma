<p align="center">
	<img src="https://user-images.githubusercontent.com/635790/47499886-82a3cb80-d861-11e8-8186-6f090eb2471f.png">
	<p align="center">
		<a href="https://www.python.org/"><img src="https://img.shields.io/badge/python-3-green.svg"></a>
		<a href="https://github.com/r3vn/badKarma/blob/master/license.md"><img src="https://img.shields.io/badge/license-GPLv3-red.svg"></a>
		<a href="https://badkarma.xfiltrated.com/"><img src="https://img.shields.io/badge/web-site-none.svg"></a>
		<a href="https://twitter.com/r3vnn"><img src="https://img.shields.io/badge/twitter-@r3vnn-blue.svg"></a>
	</p>
</p>

**badKarma** is an open source GUI based network reconnaissance toolkit which aims to assist penetration testers during network infrastructure assessments.

## Screenshots ( not updated )
<p align="center">
	<img width="720" src="https://user-images.githubusercontent.com/635790/45002099-7161df80-afd3-11e8-8131-a4dfd8090562.gif">
</p>

## Setup  

install Archlinux dependecies:

```bash
# pacman -S --needed --noconfirm python-pip gobject-introspection mitmproxy ffmpeg gtk-vnc \
gtksourceview3 vte3 osm-gps-map webkit2gtk exploitdb --overwrite='*'
```

clone the repository:
```bash
$ git clone https://github.com/r3vn/badKarma.git
```
install python dependecies:
```bash
# cd badKarma
# pip install -r requirements.txt
```

## Run

```bash
$ chmod +x badkarma.py
$ ./badkarma.py
```

## Documentation

Documentation can be found in this ![wiki](https://github.com/r3vn/badKarma/wiki).

## Donate

If badKarma helped you during a penetration testing engagement, please consider making a donation via [PayPal](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=SK6XQ2BKHYGH6&lc=en_XC). Bitcoins are accepted as well, at 1Dvvb3TGHRQwfLoUT8rVTPmHqgVjAJRcsm.
