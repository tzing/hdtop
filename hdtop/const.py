"""Constants
"""
import datetime
import urllib.parse
import typing

import urwid

import hdtop.exception


#
# Basic information
#
PROG_NAME = "hdtop"
DESCRIPTION = """Top-liked real-time monitoring console for hadoop.
"""


#
# UI
#
PALETTE = [
    ("background", "default", "default"),
    ("footer", "black", "dark cyan"),
    ("footer key", "white", "default"),
    # cluster metric pane
    ("metric text", "dark cyan", "default"),
    ("metric number", "dark cyan,bold", "default"),
    ("metric text success", "dark green", "default"),
    ("metric number success", "dark green,bold", "default"),
    ("metric text fail", "dark red", "default"),
    ("metric number fail", "dark red,bold", "default"),
    ("metric text warn", "brown", "default"),
    ("metric number warn", "brown,bold", "default"),
    ("progressbar description", "dark cyan", "default"),
    ("progressbar boundary", "white,bold", "default"),
    ("progressbar fill", "dark green", "default"),
    ("progressbar empty", "dark gray,bold", "default"),
    # app info
    ("header", "black", "dark green"),
    ("app info", "white", "default"),
]


#
# Main Panel
#
CONSOLE_MAX_COLUMN = 16


class _Attr(typing.NamedTuple):
    display_text: str
    width: int
    formatter: typing.Callable[[typing.Any], str]
    align: typing.TypeVar("align", urwid.LEFT, urwid.CENTER, urwid.RIGHT)


def format_memory(mb: int) -> str:
    UNITS = [
        (2 << 30, "P"),
        (2 << 20, "T"),
        (2 << 10, "G"),
    ]

    for size, unit in UNITS:
        if mb >= size:
            return "%.2f%s" % (mb / size, unit)

    return "%.2fM" % mb


def format_percent(f: float) -> str:
    return "{:.1f}".format(f)


def format_datetime(t: int) -> str:
    return datetime.datetime.fromtimestamp(t / 1000).strftime("%H:%M:%S")


def format_elapsed_time(t: int) -> str:
    UNITS = [
        (86400, "d"),
        (3600, "h"),
        (60, "m"),
    ]

    t //= 1000  # ms to sec

    output = []
    for size, unit in UNITS:
        if t > size:
            n = t // size
            output.append("%d%s" % (n, unit))
            t -= size * t

    if output:
        return " ".join(output)
    else:
        return "<1m"


HADOOP_APP_INFO = {
    # name: (header display, width, formatter, align)
    "id": _Attr("AppID", 32, str, urwid.LEFT),
    "user": _Attr("User", 8, str, urwid.LEFT),
    "name": _Attr("Name", -1, str, urwid.LEFT),
    "queue": _Attr("Queue", 8, str, urwid.LEFT),
    "state": _Attr("State", 7, str, urwid.LEFT),
    "progress": _Attr("Progress", 5, format_percent, urwid.RIGHT),
    "clusterId": _Attr("Clust", 15, str, urwid.LEFT),
    "applicationType": _Attr("Type", 5, str, urwid.LEFT),
    "applicationTags": _Attr("Tags", 15, str, urwid.LEFT),
    "priority": _Attr("Pri", 5, str, urwid.LEFT),
    "startedTime": _Attr("Start", 8, format_datetime, urwid.RIGHT),
    "elapsedTime": _Attr("Time", 9, format_elapsed_time, urwid.RIGHT),
    "allocatedMB": _Attr("Mem", 7, format_memory, urwid.RIGHT),
    "allocatedVCores": _Attr("vCore", 5, str, urwid.RIGHT),
    "runningContainers": _Attr("Pod", 5, str, urwid.RIGHT),
    "memorySeconds": _Attr("MemSec", 7, format_memory, urwid.RIGHT),
    "vcoreSeconds": _Attr("vCoreSec", 6, str, urwid.RIGHT),
    "queueUsagePercentage": _Attr("Queue%", 6, format_percent, urwid.RIGHT),
    "clusterUsagePercentage": _Attr("Clust%", 6, format_percent, urwid.RIGHT),
    "logAggregationStatus": _Attr("logAggregationStatus", 9, str, urwid.LEFT),
    # items that I don't known its usage criteria
    "preemptedResourceMB": _Attr("???", 7, format_memory, urwid.RIGHT),
    "preemptedResourceVCores": _Attr("???", 5, str, urwid.RIGHT),
    "numNonAMContainerPreempted": _Attr("???", 5, str, urwid.RIGHT),
    "numAMContainerPreempted": _Attr("???", 5, str, urwid.RIGHT),
    "preemptedMemorySeconds": _Attr("???", 7, format_memory, urwid.RIGHT),
    "preemptedVcoreSeconds": _Attr("???", 5, str, urwid.RIGHT),
    "unmanagedApplication": _Attr("???", 5, str, urwid.LEFT),
    "amNodeLabelExpression": _Attr("???", 5, str, urwid.LEFT),
    # HIDDEN items - this program does not read finished apps
    # finalStatus
    # trackingUI
    # trackingUrl
    # diagnostics
    # finishedTime
    # amContainerLogs
    # amHostHttpAddress
}


#
# default values
#
def extract_api_base(string: str):
    """Extract URI base from input string"""
    splitted = urllib.parse.urlsplit(string)
    if not splitted.scheme or not splitted.netloc:
        raise hdtop.exception.ConfigValueError(string)
    base = "%s://%s" % (splitted.scheme, splitted.hostname)
    if splitted.port:
        base += ":%d" % splitted.port
    return base


def _displayColumn(string: str):
    if string not in HADOOP_APP_INFO:
        raise hdtop.exception.ConfigValueError(string, HADOOP_APP_INFO)
    return string


DEFAULT_CONFIGS = [
    # section, key, type, value
    ("core", "hadoopAddress", extract_api_base, None),
    ("core", "queryInterval", float, 2.0),
    ("apps", "displayColumn.0", _displayColumn, "id"),
    ("apps", "displayColumn.1", _displayColumn, "state"),
    ("apps", "displayColumn.2", _displayColumn, "startedTime"),
    ("apps", "displayColumn.3", _displayColumn, "name"),
    ("apps", "displayColumn.4", _displayColumn, "allocatedMB"),
    ("apps", "displayColumn.5", _displayColumn, "allocatedVCores"),
    ("apps", "displayColumn.6", _displayColumn, "runningContainers"),
    ("apps", "displayColumn.7", _displayColumn, "queueUsagePercentage"),
    ("apps", "displayColumn.8", _displayColumn, "clusterUsagePercentage"),
    ("apps", "displayColumn.9", _displayColumn, None),
    ("apps", "displayColumn.10", _displayColumn, None),
    ("apps", "displayColumn.11", _displayColumn, None),
    ("apps", "displayColumn.12", _displayColumn, None),
    ("apps", "displayColumn.13", _displayColumn, None),
    ("apps", "displayColumn.14", _displayColumn, None),
    ("apps", "displayColumn.15", _displayColumn, None),
]
