# encoding: utf-8
#  This file is part of ansi2html
#  Convert ANSI (terminal) colours and attributes to HTML
#  Copyright (C) 2012  Ralph Bean <rbean@redhat.com>
#  Copyright (C) 2013  Sebastian Pipping <sebastian@pipping.org>
#
#  Inspired by and developed off of the work by pixelbeat and blackjack.
#
#  This program is free software: you can redistribute it and/or
#  modify it under the terms of the GNU General Public License as
#  published by the Free Software Foundation, either version 3 of
#  the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see
#  <http://www.gnu.org/licenses/>.

from collections import OrderedDict
import re


ANSI_FULL_RESET = 0
ANSI_INTENSITY_INCREASED = 1
ANSI_INTENSITY_REDUCED = 2
ANSI_INTENSITY_NORMAL = 22
ANSI_STYLE_ITALIC = 3
ANSI_STYLE_NORMAL = 23
ANSI_BLINK_SLOW = 5
ANSI_BLINK_FAST = 6
ANSI_BLINK_OFF = 25
ANSI_UNDERLINE_ON = 4
ANSI_UNDERLINE_OFF = 24
ANSI_CROSSED_OUT_ON = 9
ANSI_CROSSED_OUT_OFF = 29
ANSI_VISIBILITY_ON = 28
ANSI_VISIBILITY_OFF = 8
ANSI_FOREGROUND_CUSTOM_MIN = 30
ANSI_FOREGROUND_CUSTOM_MAX = 37
ANSI_FOREGROUND_256 = 38
ANSI_FOREGROUND_DEFAULT = 39
ANSI_BACKGROUND_CUSTOM_MIN = 40
ANSI_BACKGROUND_CUSTOM_MAX = 47
ANSI_BACKGROUND_256 = 48
ANSI_BACKGROUND_DEFAULT = 49
ANSI_NEGATIVE_ON = 7
ANSI_NEGATIVE_OFF = 27
ANSI_FOREGROUND_HIGH_INTENSITY_MIN = 90
ANSI_FOREGROUND_HIGH_INTENSITY_MAX = 97
ANSI_BACKGROUND_HIGH_INTENSITY_MIN = 100
ANSI_BACKGROUND_HIGH_INTENSITY_MAX = 107

VT100_BOX_CODES = {
    "0x71": "─",
    "0x74": "├",
    "0x75": "┤",
    "0x76": "┴",
    "0x77": "┬",
    "0x78": "│",
    "0x6a": "┘",
    "0x6b": "┐",
    "0x6c": "┌",
    "0x6d": "└",
    "0x6e": "┼",
}

_html_template = """\
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=%(output_encoding)s">
<title>%(title)s</title>
<style type="text/css">\n%(style)s\n</style>
</head>
<body class="body_foreground body_background" style="font-size: %(font_size)s;" >
<pre class="ansi2html-content">
%(content)s
</pre>
</body>

</html>
"""  # noqa: E501


class Rule(object):
    def __init__(self, klass, **kw):

        self.klass = klass
        self.kw = "; ".join(
            [(k.replace("_", "-") + ": " + kw[k]) for k in sorted(kw.keys())]
        ).strip()
        self.kwl = [(k.replace("_", "-"), kw[k][1:]) for k in sorted(kw.keys())]

    def __str__(self):
        return "%s { %s; }" % (self.klass, self.kw)


def index(r, g, b):
    return str(16 + (r * 36) + (g * 6) + b)


def color_component(x):
    if x == 0:
        return 0
    return 0x37 + (0x28 * x)


def color(r, g, b):
    return "#%.2x%.2x%.2x" % (
        color_component(r),
        color_component(g),
        color_component(b),
    )


def level(grey):
    return "#%.2x%.2x%.2x" % (((grey * 10) + 8,) * 3)


def index2(grey):
    return str(232 + grey)


# http://en.wikipedia.org/wiki/ANSI_escape_code#Colors
SCHEME = {
    # black red green brown/yellow blue magenta cyan grey/white
    "ansi2html": (
        "#000316",
        "#aa0000",
        "#00aa00",
        "#aa5500",
        "#0000aa",
        "#E850A8",
        "#00aaaa",
        "#F5F1DE",
        "#7f7f7f",
        "#ff0000",
        "#00ff00",
        "#ffff00",
        "#5c5cff",
        "#ff00ff",
        "#00ffff",
        "#ffffff",
    ),
    "xterm": (
        "#000000",
        "#cd0000",
        "#00cd00",
        "#cdcd00",
        "#0000ee",
        "#cd00cd",
        "#00cdcd",
        "#e5e5e5",
        "#7f7f7f",
        "#ff0000",
        "#00ff00",
        "#ffff00",
        "#5c5cff",
        "#ff00ff",
        "#00ffff",
        "#ffffff",
    ),
    "osx": (
        "#000000",
        "#c23621",
        "#25bc24",
        "#adad27",
        "#492ee1",
        "#d338d3",
        "#33bbc8",
        "#cbcccd",
    )
    * 2,
    # http://ethanschoonover.com/solarized
    "solarized": (
        "#262626",
        "#d70000",
        "#5f8700",
        "#af8700",
        "#0087ff",
        "#af005f",
        "#00afaf",
        "#e4e4e4",
        "#1c1c1c",
        "#d75f00",
        "#585858",
        "#626262",
        "#808080",
        "#5f5faf",
        "#8a8a8a",
        "#ffffd7",
    ),
    "mint-terminal": (
        "#2E3436",
        "#CC0000",
        "#4E9A06",
        "#C4A000",
        "#3465A4",
        "#75507B",
        "#06989A",
        "#D3D7CF",
        "#555753",
        "#EF2929",
        "#8AE234",
        "#FCE94F",
        "#729FCF",
        "#AD7FA8",
        "#34E2E2",
        "#EEEEEC",
    ),
}


def intensify(color, dark_bg, amount=64):
    if not dark_bg:
        amount = -amount
    rgb = tuple(max(0, min(255, amount + int(color[i : i + 2], 16))) for i in (1, 3, 5))
    return "#%.2x%.2x%.2x" % rgb


def get_styles(dark_bg=True, line_wrap=True, scheme="ansi2html"):
    css = [
        Rule(
            ".ansi2html-content",
            white_space=("pre", "pre-wrap")[line_wrap],
            word_wrap="break-word",
            display="inline",
        ),
        Rule(".body_foreground", color=("#000000", "#AAAAAA")[dark_bg]),
        Rule(".body_background", background_color=("#AAAAAA", "#000000")[dark_bg]),
        Rule(
            (
                ".body_foreground > .bold,.bold > .body_foreground, "
                "body.body_foreground > pre > .bold"
            ),
            color=("#000000", "#FFFFFF")[dark_bg],
            font_weight=("bold", "normal")[dark_bg],
        ),
        Rule(".inv_foreground", color=("#000000", "#FFFFFF")[not dark_bg]),
        Rule(".inv_background", background_color=("#AAAAAA", "#000000")[not dark_bg]),
        Rule(".ansi1", font_weight="bold"),
        Rule(".ansi2", font_weight="lighter"),
        Rule(".ansi3", font_style="italic"),
        Rule(".ansi4", text_decoration="underline"),
        Rule(".ansi5", text_decoration="blink"),
        Rule(".ansi6", text_decoration="blink"),
        Rule(".ansi8", visibility="hidden"),
        Rule(".ansi9", text_decoration="line-through"),
    ]

    # set palette
    pal = SCHEME[scheme]
    for _index in range(8):
        css.append(Rule(".ansi3%s" % _index, color=pal[_index]))
        css.append(Rule(".inv3%s" % _index, background_color=pal[_index]))
    for _index in range(8):
        css.append(Rule(".ansi4%s" % _index, background_color=pal[_index]))
        css.append(Rule(".inv4%s" % _index, color=pal[_index]))
    for _index in range(8):
        css.append(Rule(".ansi9%s" % _index, color=intensify(pal[_index], dark_bg)))
        css.append(
            Rule(".inv9%s" % _index, background_color=intensify(pal[_index], dark_bg))
        )
    for _index in range(8):
        css.append(
            Rule(".ansi10%s" % _index, background_color=intensify(pal[_index], dark_bg))
        )
        css.append(Rule(".inv10%s" % _index, color=intensify(pal[_index], dark_bg)))

    # set palette colors in 256 color encoding
    pal = SCHEME[scheme]
    for _index in range(len(pal)):
        css.append(Rule(".ansi38-%s" % _index, color=pal[_index]))
        css.append(Rule(".inv38-%s" % _index, background_color=pal[_index]))
    for _index in range(len(pal)):
        css.append(Rule(".ansi48-%s" % _index, background_color=pal[_index]))
        css.append(Rule(".inv48-%s" % _index, color=pal[_index]))

    # css.append("/* Define the explicit color codes (obnoxious) */\n\n")

    for green in range(0, 6):
        for red in range(0, 6):
            for blue in range(0, 6):
                css.append(
                    Rule(
                        ".ansi38-%s" % index(red, green, blue),
                        color=color(red, green, blue),
                    )
                )
                css.append(
                    Rule(
                        ".inv38-%s" % index(red, green, blue),
                        background=color(red, green, blue),
                    )
                )
                css.append(
                    Rule(
                        ".ansi48-%s" % index(red, green, blue),
                        background=color(red, green, blue),
                    )
                )
                css.append(
                    Rule(
                        ".inv48-%s" % index(red, green, blue),
                        color=color(red, green, blue),
                    )
                )

    for grey in range(0, 24):
        css.append(Rule(".ansi38-%s" % index2(grey), color=level(grey)))
        css.append(Rule(".inv38-%s" % index2(grey), background=level(grey)))
        css.append(Rule(".ansi48-%s" % index2(grey), background=level(grey)))
        css.append(Rule(".inv48-%s" % index2(grey), color=level(grey)))

    return css


class _State(object):
    def __init__(self):
        self.reset()

    def reset(self):
        self.intensity = ANSI_INTENSITY_NORMAL
        self.style = ANSI_STYLE_NORMAL
        self.blink = ANSI_BLINK_OFF
        self.underline = ANSI_UNDERLINE_OFF
        self.crossedout = ANSI_CROSSED_OUT_OFF
        self.visibility = ANSI_VISIBILITY_ON
        self.foreground = (ANSI_FOREGROUND_DEFAULT, None)
        self.background = (ANSI_BACKGROUND_DEFAULT, None)
        self.negative = ANSI_NEGATIVE_OFF

    def adjust(self, ansi_code, parameter=None):
        if ansi_code in (
            ANSI_INTENSITY_INCREASED,
            ANSI_INTENSITY_REDUCED,
            ANSI_INTENSITY_NORMAL,
        ):
            self.intensity = ansi_code
        elif ansi_code in (ANSI_STYLE_ITALIC, ANSI_STYLE_NORMAL):
            self.style = ansi_code
        elif ansi_code in (ANSI_BLINK_SLOW, ANSI_BLINK_FAST, ANSI_BLINK_OFF):
            self.blink = ansi_code
        elif ansi_code in (ANSI_UNDERLINE_ON, ANSI_UNDERLINE_OFF):
            self.underline = ansi_code
        elif ansi_code in (ANSI_CROSSED_OUT_ON, ANSI_CROSSED_OUT_OFF):
            self.crossedout = ansi_code
        elif ansi_code in (ANSI_VISIBILITY_ON, ANSI_VISIBILITY_OFF):
            self.visibility = ansi_code
        elif ANSI_FOREGROUND_CUSTOM_MIN <= ansi_code <= ANSI_FOREGROUND_CUSTOM_MAX:
            self.foreground = (ansi_code, None)
        elif (
            ANSI_FOREGROUND_HIGH_INTENSITY_MIN
            <= ansi_code
            <= ANSI_FOREGROUND_HIGH_INTENSITY_MAX
        ):
            self.foreground = (ansi_code, None)
        elif ansi_code == ANSI_FOREGROUND_256:
            self.foreground = (ansi_code, parameter)
        elif ansi_code == ANSI_FOREGROUND_DEFAULT:
            self.foreground = (ansi_code, None)
        elif ANSI_BACKGROUND_CUSTOM_MIN <= ansi_code <= ANSI_BACKGROUND_CUSTOM_MAX:
            self.background = (ansi_code, None)
        elif (
            ANSI_BACKGROUND_HIGH_INTENSITY_MIN
            <= ansi_code
            <= ANSI_BACKGROUND_HIGH_INTENSITY_MAX
        ):
            self.background = (ansi_code, None)
        elif ansi_code == ANSI_BACKGROUND_256:
            self.background = (ansi_code, parameter)
        elif ansi_code == ANSI_BACKGROUND_DEFAULT:
            self.background = (ansi_code, None)
        elif ansi_code in (ANSI_NEGATIVE_ON, ANSI_NEGATIVE_OFF):
            self.negative = ansi_code

    def to_css_classes(self):
        css_classes = []

        def append_unless_default(output, value, default):
            if value != default:
                css_class = "ansi%d" % value
                output.append(css_class)

        def append_color_unless_default(
            output, color, default, negative, neg_css_class
        ):
            value, parameter = color
            if value != default:
                prefix = "inv" if negative else "ansi"
                css_class_index = (
                    str(value) if (parameter is None) else "%d-%d" % (value, parameter)
                )
                output.append(prefix + css_class_index)
            elif negative:
                output.append(neg_css_class)

        append_unless_default(css_classes, self.intensity, ANSI_INTENSITY_NORMAL)
        append_unless_default(css_classes, self.style, ANSI_STYLE_NORMAL)
        append_unless_default(css_classes, self.blink, ANSI_BLINK_OFF)
        append_unless_default(css_classes, self.underline, ANSI_UNDERLINE_OFF)
        append_unless_default(css_classes, self.crossedout, ANSI_CROSSED_OUT_OFF)
        append_unless_default(css_classes, self.visibility, ANSI_VISIBILITY_ON)

        flip_fore_and_background = self.negative == ANSI_NEGATIVE_ON
        append_color_unless_default(
            css_classes,
            self.foreground,
            ANSI_FOREGROUND_DEFAULT,
            flip_fore_and_background,
            "inv_background",
        )
        append_color_unless_default(
            css_classes,
            self.background,
            ANSI_BACKGROUND_DEFAULT,
            flip_fore_and_background,
            "inv_foreground",
        )

        return css_classes


def linkify(line):
    url_matcher = re.compile(
        r"(((((https?|ftps?|gopher|telnet|nntp)://)|"
        r"(mailto:|news:))(%[0-9A-Fa-f]{2}|[-()_.!~*"
        r"\';/?:@&=+$,A-Za-z0-9])+)([).!\';/?:,][[:blank:]])?)"
    )
    return url_matcher.sub(r'<a href="\1">\1</a>', line)


def map_vt100_box_code(char):
    char_hex = hex(ord(char))
    return VT100_BOX_CODES[char_hex] if char_hex in VT100_BOX_CODES else char


def _needs_extra_newline(text):
    if not text or text.endswith("\n"):
        return False
    return True


class CursorMoveUp(object):
    pass


class Ansi2HTMLConverter(object):
    """Convert Ansi color codes to CSS+HTML.

    Example:
    >>> conv = Ansi2HTMLConverter()
    >>> ansi = " ".join(sys.stdin.readlines())
    >>> html = conv.convert(ansi)
    """

    def __init__(
        self,
        inline=False,
        dark_bg=True,
        line_wrap=True,
        font_size="normal",
        linkify=False,
        escaped=True,
        markup_lines=False,
        output_encoding="utf-8",
        scheme="ansi2html",
        title="",
    ):

        self.inline = inline
        self.dark_bg = dark_bg
        self.line_wrap = line_wrap
        self.font_size = font_size
        self.linkify = linkify
        self.escaped = escaped
        self.markup_lines = markup_lines
        self.output_encoding = output_encoding
        self.scheme = scheme
        self.title = title
        self._attrs = None

        if inline:
            self.styles = dict(
                [
                    (item.klass.strip("."), item)
                    for item in get_styles(self.dark_bg, self.line_wrap, self.scheme)
                ]
            )

        self.vt100_box_codes_prog = re.compile("\033\\(([B0])")
        self.ansi_codes_prog = re.compile("\033\\[" "([\\d;]*)" "([a-zA-z])")

    def apply_regex(self, ansi):
        styles_used = set()
        parts = self._apply_regex(ansi, styles_used)
        parts = self._collapse_cursor(parts)
        parts = list(parts)

        if self.linkify:
            parts = [linkify(part) for part in parts]

        combined = "".join(parts)

        if self.markup_lines:
            combined = "\n".join(
                [
                    """<span id="line-%i">%s</span>""" % (i, line)
                    for i, line in enumerate(combined.split("\n"))
                ]
            )

        return combined, styles_used

    def _apply_regex(self, ansi, styles_used):
        if self.escaped:
            specials = OrderedDict([("&", "&amp;"), ("<", "&lt;"), (">", "&gt;")])
            for pattern, special in specials.items():
                ansi = ansi.replace(pattern, special)

        def _vt100_box_drawing():
            last_end = 0  # the index of the last end of a code we've seen
            box_drawing_mode = False
            for match in self.vt100_box_codes_prog.finditer(ansi):
                trailer = ansi[last_end : match.start()]
                if box_drawing_mode:
                    for char in trailer:
                        yield map_vt100_box_code(char)
                else:
                    yield trailer
                last_end = match.end()
                box_drawing_mode = match.groups()[0] == "0"
            yield ansi[last_end:]

        ansi = "".join(_vt100_box_drawing())

        state = _State()
        inside_span = False
        last_end = 0  # the index of the last end of a code we've seen
        for match in self.ansi_codes_prog.finditer(ansi):
            yield ansi[last_end : match.start()]
            last_end = match.end()

            params, command = match.groups()

            if command not in "mMA":
                continue

            # Special cursor-moving code.  The only supported one.
            if command == "A":
                yield CursorMoveUp
                continue

            try:
                params = list(map(int, params.split(";")))
            except ValueError:
                params = [ANSI_FULL_RESET]

            # Find latest reset marker
            last_null_index = None
            skip_after_index = -1
            for i, v in enumerate(params):
                if i <= skip_after_index:
                    continue

                if v == ANSI_FULL_RESET:
                    last_null_index = i
                elif v in (ANSI_FOREGROUND_256, ANSI_BACKGROUND_256):
                    skip_after_index = i + 2

            # Process reset marker, drop everything before
            if last_null_index is not None:
                params = params[last_null_index + 1 :]
                if inside_span:
                    inside_span = False
                    yield "</span>"
                state.reset()

                if not params:
                    continue

            # Turn codes into CSS classes
            skip_after_index = -1
            for i, v in enumerate(params):
                if i <= skip_after_index:
                    continue

                if v in (ANSI_FOREGROUND_256, ANSI_BACKGROUND_256):
                    try:
                        parameter = params[i + 2]
                    except IndexError:
                        continue
                    skip_after_index = i + 2
                else:
                    parameter = None
                state.adjust(v, parameter=parameter)

            if inside_span:
                yield "</span>"
                inside_span = False

            css_classes = state.to_css_classes()
            if not css_classes:
                continue
            styles_used.update(css_classes)

            if self.inline:
                style = [
                    self.styles[klass].kw
                    for klass in css_classes
                    if klass in self.styles
                ]
                yield '<span style="%s">' % "; ".join(style)
            else:
                yield '<span class="%s">' % " ".join(css_classes)
            inside_span = True

        yield ansi[last_end:]
        if inside_span:
            yield "</span>"
            inside_span = False

    def _collapse_cursor(self, parts):
        """ Act on any CursorMoveUp commands by deleting preceding tokens """

        final_parts = []
        for part in parts:

            # Throw out empty string tokens ("")
            if not part:
                continue

            # Go back, deleting every token in the last 'line'
            if part == CursorMoveUp:
                if final_parts:
                    final_parts.pop()

                while final_parts and "\n" not in final_parts[-1]:
                    final_parts.pop()

                continue

            # Otherwise, just pass this token forward
            final_parts.append(part)

        return final_parts

    def prepare(self, ansi="", ensure_trailing_newline=False):
        """ Load the contents of 'ansi' into this object """

        body, styles = self.apply_regex(ansi)

        if ensure_trailing_newline and _needs_extra_newline(body):
            body += "\n"

        self._attrs = {
            "dark_bg": self.dark_bg,
            "line_wrap": self.line_wrap,
            "font_size": self.font_size,
            "body": body,
            "styles": styles,
        }

        return self._attrs

    def attrs(self):
        """ Prepare attributes for the template """
        if not self._attrs:
            raise Exception("Method .prepare not yet called.")
        return self._attrs

    def convert(self, ansi, full=True, ensure_trailing_newline=False):
        attrs = self.prepare(ansi, ensure_trailing_newline=ensure_trailing_newline)
        if not full:
            return attrs["body"]
        else:
            _template = _html_template
            all_styles = get_styles(self.dark_bg, self.line_wrap, self.scheme)
            backgrounds = all_styles[:6]
            used_styles = filter(
                lambda e: e.klass.lstrip(".") in attrs["styles"], all_styles
            )

            return _template % {
                "style": "\n".join(list(map(str, backgrounds + list(used_styles)))),
                "title": self.title,
                "font_size": self.font_size,
                "content": attrs["body"],
                "output_encoding": self.output_encoding,
            }

    def produce_headers(self):
        return '<style type="text/css">\n%(style)s\n</style>\n' % {
            "style": "\n".join(
                map(str, get_styles(self.dark_bg, self.line_wrap, self.scheme))
            )
        }
