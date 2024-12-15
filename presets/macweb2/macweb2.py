SIMPLIFY_HTML = True

TAGS_TO_UNWRAP = [
	"noscript",
]

TAGS_TO_STRIP = [
	"script",
	"link",
	"style",
	"source",
]

ATTRIBUTES_TO_STRIP = [
	"style",
	"onclick",
	"class",
	"bgcolor",
	"text",
	"link",
	"vlink"
]

CAN_RENDER_INLINE_IMAGES = False
RESIZE_IMAGES = True
MAX_IMAGE_WIDTH = 512
MAX_IMAGE_HEIGHT = 342
CONVERT_IMAGES = True
CONVERT_IMAGES_TO_FILETYPE = "gif"
DITHERING_ALGORITHM = "FLOYDSTEINBERG"

WEB_SIMULATOR_PROMPT_ADDENDUM = """<formatting>
IMPORTANT: The user's web browser only supports (most of) HTML 3.2 (you do not need to acknowledge this to the user, only understand it and use this knowledge to construct the HTML you respond with).
Their browser has NO CSS support and NO JavaScript support. Never include <script>, <style> or inline scripting or styling in your responses. The output html will always be rendered as black on a white background, and there's no need to try to change this.
Tags supported by the user's browser include:html, head, body, title, a, h1, h2, h3, p, ul, ol, li, div, table, tr, th, td, caption,
dl, dt, dd, kbd, samp, var, b, i, u, address, blockquote,
form, select, option, textarea,
input - inputs with type="text" and type="password" are fully supported. Inputs with type="radio", type="checkbox", type="file", and type="image" are NOT supported and should never be used. Never prepopulate forms with information. Never reveal passwords in webpages or urls.
hr - always format like <hr>, and never like <hr />, as this is not supported by the user's browser
<br> - always format like <br>, and never like <br />, as this is not supported by the user's browser
<xmp> - if presenting html code to the user, wrap it in this tag to keep it from being rendered as html
<img> - all images will render as a "broken image" in the user's browser, so use them sparingly. The dimensions of the user's browser are 512 × 342px; any included images should take this into consideration. The alt attribute is not supported, so don't include it. Instead, if a description of the img is relevant, use nearby text to describe it.
<pre> - can be used to wrap preformatted text, including ASCII art (which could represent game state, be an ASCII art text banner, etc.)
<font> - as CSS is not supported, text can be wrapped in <font> tags to set the size of text like so: <font size="7">. Sizes 1-7 are supported. Neither the face attribute nor the color attribute are supported, so do not use them. As a workaround for setting the font face, the user's web browser has configured all <h6> elements to render using the "Times New Roman" font, <h5> elements to use the "Palatino" font, and <h4> to use the "Chicago" font. By default, these elements will render at font size 1, so you may want to use <font> tags with the size attribute set to enlarge these if you use them).
<center> - as CSS is not supported, to center a group of elements, you can wrap them in the <center> tag. You can also use the "align" attribute on p, div, and table attributes to align them horizontally.
<table>s render well on the user's browser, so use them liberally to format tabular data such as posts in forum threads, messages in an inbox, etc. You can also render a table without a border to arrange information without giving the appearance of a table.
<tt> - use this tag to render text as it would appear on a fixed-width device such as a teletype (telegrams, simulated command-line interfaces, etc.)
Never use script tags or style tags.
</formatting>"""

CONVERT_CHARACTERS = True

CONVERSION_TABLE = {
	"¢": b"cent",
	"&cent;": b"cent",
	"€": b"EUR",
	"&euro;": b"EUR",
	"&yen;": b"YEN",
	"&pound;": b"GBP",
	"«": b"'",
	"&laquo;": b"'",
	"»": b"'",
	"&raquo;": b"'",
	"‘": b"'",
	"&lsquo;": b"'",
	"’": b"'",
	"&rsquo;": b"'",
	"“": b"''",
	"&ldquo;": b"''",
	"”": b"''",
	"&rdquo;": b"''",
	"–": b"-",
	"&ndash;": b"-",
	"—": b"--",
	"&mdash;": b"--",
	"―": b"-",
	"&horbar;": b"-",
	"·": b"-",
	"&middot;": b"-",
	"‚": b",",
	"&sbquo;": b",",
	"„": b",,",
	"&bdquo;": b",,",
	"†": b"*",
	"&dagger;": b"*",
	"‡": b"**",
	"&Dagger;": b"**",
	"•": b"-",
	"&bull;": b"*",
	"…": b"...",
	"&hellip;": b"...",
	"\u00A0": b" ",
	"&nbsp;": b" ",
	"±": b"+/-",
	"&plusmn;": b"+/-",
	"≈": b"~",
	"&asymp;": b"~",
	"≠": b"!=",
	"&ne;": b"!=",
	"&times;": b"x",
	"⁄": b"/",
	"°": b"*",
	"&deg;": b"*",
	"′": b"'",
	"&prime;": b"'",
	"″": b"''",
	"&Prime;": b"''",
	"™": b"(tm)",
	"&trade;": b"(TM)",
	"&reg;": b"(R)",
	"®": b"(R)",
	"&copy;": b"(c)",
	"©": b"(c)",
	"é": b"e",
	"ø": b"o",
	"Å": b"A",
	"â": b"a",
	"Æ": b"AE",
	"æ": b"ae",
	"á": b"a",
	"ō": b"o",
	"ó": b"o",
	"ū": b"u",
	"⟨": b"<",
	"⟩": b">",
	"←": b"<",
	"›": b">",
	"‹": b"<",
	"&larr;": b"<",
	"→": b">",
	"&rarr;": b">",
	"↑": b"^",
	"&uarr;": b"^",
	"↓": b"v",
	"&darr;": b"v",
	"↖": b"\\",
	"&nwarr;": b"\\",
	"↗": b"/",
	"&nearr;": b"/",
	"↘": b"\\",
	"&searr;": b"\\",
	"↙": b"/",
	"&swarr;": b"/",
	"─": b"-",
	"&boxh;": b"-",
	"│": b"|",
	"&boxv;": b"|",
	"┌": b"+",
	"&boxdr;": b"+",
	"┐": b"+",
	"&boxdl;": b"+",
	"└": b"+",
	"&boxur;": b"+",
	"┘": b"+",
	"&boxul;": b"+",
	"├": b"+",
	"&boxvr;": b"+",
	"┤": b"+",
	"&boxvl;": b"+",
	"┬": b"+",
	"&boxhd;": b"+",
	"┴": b"+",
	"&boxhu;": b"+",
	"┼": b"+",
	"&boxvh;": b"+",
	"█": b"#",
	"&block;": b"#",
	"▌": b"|",
	"&lhblk;": b"|",
	"▐": b"|",
	"&rhblk;": b"|",
	"▀": b"-",
	"&uhblk;": b"-",
	"▄": b"_",
	"&lhblk;": b"_",
	"▾": b"v",
	"&dtrif;": b"v",
	"&#x25BE;": b"v",
	"&#9662;": b"v",
	"♫": b"",
	"&spades;": b"",
	"\u200B": b"",
	"&ZeroWidthSpace;": b"",
	"\u200C": b"",
	"\u200D": b"",
	"\uFEFF": b"",
}