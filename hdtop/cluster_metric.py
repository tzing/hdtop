"""Widgets for cluster metric (upper pane)
"""
import logging
import typing

import httpx
import urwid
import urwid.canvas

import hdtop.config
import hdtop.const
import hdtop.exception

logger = logging.getLogger("hdtop.cluster_metric")


class ClusterMetricMonitor(urwid.BoxAdapter):
    """Upper pane that shows cluster metric."""

    uri: "str"
    client: "httpx.Client"
    loop: "urwid.MainLoop"

    def __init__(self) -> None:
        # left part
        self.usage_bar = ClusterResourceUsageBox()

        # right part
        self.app_count = AppsCount()
        self.node_count = NodeCount()
        self.container_count = ContainerCount()
        self.numbers = urwid.ListBox(
            [
                self.app_count,
                self.node_count,
                self.container_count,
            ]
        )

        # main
        main = urwid.Filler(
            urwid.Columns(
                [
                    ("weight", 1, self.usage_bar),
                    ("weight", 1, self.numbers),
                ]
            ),
            height=3,  # inner height
            top=1,  # padding
        )
        super().__init__(main, height=5)  # outer height

        # placeholder
        self.uri = None
        self.client = None

    def set_event(self, loop: "urwid.MainLoop", api_uri: str):
        self.uri = api_uri + "/ws/v1/cluster/metrics"
        self.client = httpx.Client()

        loop.set_alarm_in(0.6, self.event)

    def event(self, loop, user_data):
        # query
        try:
            resp = self.client.get(self.uri)
        except httpx.HTTPError:
            logger.exception("Failed to query cluster metric")
            return

        # update
        metrics: dict = resp.json().get("clusterMetrics", {})
        self.app_count.set_counts(**metrics)
        self.node_count.set_counts(**metrics)
        self.container_count.set_counts(**metrics)

        self.usage_bar.v_cores.set_progress(
            metrics.get("allocatedVirtualCores", 0),
            metrics.get("totalVirtualCores", 0),
        )
        self.usage_bar.memory.set_progress(
            metrics.get("allocatedMB", 0),
            metrics.get("totalMB", 0),
        )

        # schedule next query
        loop.set_alarm_in(hdtop.config.get_config("core", "queryInterval"), self.event)


class ClusterResourceUsageBox(urwid.ListBox):
    TEXT_COLUMN_WIDTH = 7

    def __init__(self) -> None:
        w_vcores, self.v_cores = self.create_usagebar("vCore")
        w_memory, self.memory = self.create_usagebar("Mem", hdtop.const.format_memory)
        super().__init__([w_vcores, w_memory])

    def create_usagebar(
        self, text, textify=str
    ) -> "typing.Tuple[urwid.Columns, UsageBar]":
        bar = UsageBar(textify)
        view = urwid.Columns(
            [
                (
                    self.TEXT_COLUMN_WIDTH,
                    urwid.Text(("progressbar description", text), urwid.RIGHT),
                ),
                (1, urwid.Text(("progressbar boundary", "["))),
                ("weight", 1, bar),
                (4, urwid.Text(("progressbar boundary", "]"))),
            ]
        )
        return view, bar


class UsageBar(urwid.Text):
    """Top-liked styled resource usage progress bar"""

    def __init__(self, textify: typing.Callable[[typing.Any], str] = str) -> None:
        """
        Parameters
        ----------
            textify : callable
                Text formatter
        """
        self._current = 0
        self._complete = 0
        self._textify = textify

        super().__init__(
            ("progressbar empty", self.get_text()), align=urwid.RIGHT, wrap=urwid.CLIP
        )

    def set_progress(self, current, complete):
        self._current = current
        self._complete = complete
        self._invalidate()

    def get_text(self):
        return self._textify(self._current) + "/" + self._textify(self._complete)

    def rows(self, size, focus):
        return 1

    def render(self, size, focus):
        # size
        (maxcol,) = size
        ncol_fill = round(self._current / max(self._complete, 1) * maxcol)

        # text
        txt_status = self.get_text()
        if maxcol < len(txt_status):
            txt_status = txt_status[:maxcol]
        txt_fill = "|" * min(ncol_fill, max(0, maxcol - len(txt_status)))
        txt_space = " " * max(0, maxcol - len(txt_status) - len(txt_fill))

        # markup
        text = txt_fill + txt_space + txt_status
        attr = [
            ("progressbar fill", ncol_fill),
            ("progressbar empty", maxcol - ncol_fill),
        ]

        trans = self.get_line_translation(maxcol, (text, attr))
        return urwid.canvas.apply_text_layout(text, attr, trans, maxcol)


class AppsCount(urwid.Text):
    def __init__(self) -> None:
        super().__init__("")
        self.set_counts()

    def set_counts(
        self, appsSubmitted=0, appsCompleted=0, appsPending=0, appsRunning=0, **kwargs
    ):
        markup = [("metric text", "Apps: ")]

        if appsPending:
            markup += [
                ("metric number", str(appsPending)),
                ("metric text", " pending, "),
            ]

        markup += [
            ("metric number success", str(appsRunning)),
            ("metric text success", " running"),
        ]

        for key in ("appsFailed", "appsKilled"):
            value = kwargs.get(key, -1)
            if value <= 0:
                continue
            display_key = key[4:]
            markup += [
                ("metric text", ", "),
                ("metric number fail", str(value)),
                ("metric text fail", " " + display_key),
            ]

        markup += [
            ("metric text", ", "),
            ("metric number", str(appsCompleted)),
            ("metric text", "/"),
            ("metric number", str(appsSubmitted)),
            ("metric text", " done"),
        ]

        self.set_text(markup)


class NodeCount(urwid.Text):
    def __init__(self) -> None:
        super().__init__("")
        self.set_counts()

    def set_counts(
        self,
        totalNodes=0,
        activeNodes=0,
        decommissioningNodes=0,
        decommissionedNodes=0,
        **kwargs
    ):
        markup = [
            ("metric text", "Nodes: "),
            ("metric number", str(totalNodes)),
            ("metric text", "; "),
            ("metric number success", str(activeNodes)),
            ("metric text success", " active"),
            ("metric text", ", "),
            ("metric number", str(decommissioningNodes + decommissionedNodes)),
            ("metric text", " decommission"),
        ]

        for key in ("unhealthyNodes", "rebootedNodes"):
            value = kwargs.get(key, -1)
            if value <= 0:
                continue
            display_key = key[:-5]
            markup += [
                ("metric text", ", "),
                ("metric number warn", str(value)),
                ("metric text warn", " " + display_key),
            ]

        for key in ("lostNodes", "shutdownNodes"):
            value = kwargs.get(key, -1)
            if value <= 0:
                continue
            display_key = key[:-5]
            markup += [
                ("metric text", ", "),
                ("metric number fail", str(value)),
                ("metric text fail", " " + display_key),
            ]

        self.set_text(markup)


class ContainerCount(urwid.Text):
    def __init__(self) -> None:
        super().__init__("")
        self.set_counts()

    def set_counts(
        self, containersAllocated=0, containersReserved=0, containersPending=0, **kwargs
    ):
        markup = [
            ("metric text", "Containers: "),
            ("metric number success", str(containersAllocated)),
            ("metric text success", " allocated"),
        ]

        if containersReserved:
            markup += [
                ("metric text", ", "),
                ("metric number", str(containersReserved)),
                ("metric text", " reserved"),
            ]

        if containersPending:
            markup += [
                ("metric text", ", "),
                ("metric number", str(containersPending)),
                ("metric text", " pending"),
            ]

        self.set_text(markup)
