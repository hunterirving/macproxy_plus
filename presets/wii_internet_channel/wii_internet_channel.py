SIMPLIFY_HTML = False

TAGS_TO_UNWRAP = []

TAGS_TO_STRIP = []

ATTRIBUTES_TO_STRIP = []

CAN_RENDER_INLINE_IMAGES = True
RESIZE_IMAGES = False
MAX_IMAGE_WIDTH = None
MAX_IMAGE_HEIGHT = None
CONVERT_IMAGES = False
CONVERT_IMAGES_TO_FILETYPE = None
DITHERING_ALGORITHM = None

WEB_SIMULATOR_PROMPT_ADDENDUM = """<formatting>
The user is accessing these pages from a Nintendo Wii running the Internet Channel, a simplified version of the Opera browser designed specially for the Wii.
This browser was released in 2006, and has the following features and quirks (keep these in mind when generating web pages):
Opera supports all the elements and attributes of HTML4.01 with the following exceptions:
	<input type="file"> is not supported.
	The col width attribute does not support multilengths.
	The object standby and declare attributes are not supported.
	The table cell attributes char and charoff are not supported.
Opera supports the canvas element.
Opera has experimental support for the Web Forms 2.0 extension to HTML4.
Opera supports all of CSS2 except where behavior has been modified / changed by CSS2.1. There are some limitations to Opera's support for CSS:
	The following properties are not supported:
		font-size-adjust
		font-stretch
		marker-offset
		marks
		text-shadow (supported as -o-text-shadow)
	The following property / value combinations are not supported:
		display:marker
		text-align:<string>
		visibility:collapse
		white-space:pre-line
	Named pages (as described in section 13.3.2).
	The @font-face construct.
CSS3:
Opera has partial support for the Selectors and Media Queries specifications. Opera also supports the content property on arbitrary elements and not just on ::before and ::after. It also supports the following properties:
    box-sizing
    opacity
Opera CSS extensions:
Opera implements several CSS3 properties as experimental properties so authors can try them out. By implementing them with the -o- prefix we ensure that the specification can be changed at a later stage:
    -o-text-overflow:ellipsis
    -o-text-shadow
Opera supports the entire ECMA-262 2ed and 3ed standards, with no exceptions. They are more or less aligned with JavaScript 1.3/1.5.
All text communicated to Opera from the network is converted into Unicode.
Opera supports a superset of SVG 1.1 Basic and SVG 1.1 Tiny with some exceptions. This maps to a partial support of SVG 1.1.
Event listening to any event is supported, but some events are not fired by the application. focusin, focusout and activate for instance. Fonts are supported, including font-family, but if there is a missing glyph in the selected font a platform-defined fallback will be used instead of picking that glyph from the next font in line in the font-family property.
SVG can be used in object, embed, and iframe in HTML and as stand-alone document. It is not supported for img elements or in CSS property values (e.g. background-image). An SVG image element can contain any supported raster graphics, but not another SVG image. References to external resources are not supported.
These features are particularly processor expensive and should be used with care when targetting machines with slower processors: filters, transparency layers (group opacity), and masks.
</formatting>
<expressiveness>
Use CSS and JavaScript liberally (while minding the supported versions of each) to surprise and delight the user with exciting, interactive webpages. Push the limits of what is expected to create interfaces that are fun, innovative, and experimental.
You should always embed CSS/JS within the returned HTML file, either inline or within <style> and/or <script> tags.
</expressiveness>
"""

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