"""Widgets for app status (lower pane)
"""
import logging
import typing

import httpx
import urwid
import urwid.util

import hdtop.config
import hdtop.const

logger = logging.getLogger("hdtop.cluster_metric")


class AppStatus(urwid.Frame):
    text_attr: typing.Dict[str, hdtop.const._Attr]

    def __init__(self) -> None:
        # load settings
        display_columns = [
            hdtop.config.get_config("apps", f"displayColumn.{idx}")
            for idx in range(hdtop.const.CONSOLE_MAX_COLUMN)
        ]
        display_columns = [column for column in display_columns if column]

        # width for each column
        self.text_attr = {
            column: hdtop.const.HADOOP_APP_INFO[column] for column in display_columns
        }

        # view
        self.header = HeaderRow(self.text_attr)
        self.header.set_data(
            {
                column: hdtop.const.HADOOP_APP_INFO[column][0]
                for column in display_columns
            }
        )

        self.body = urwid.ListBox([])
        super().__init__(
            header=urwid.AttrWrap(self.header, "header"),
            body=self.body,
        )

        # placeholder
        self.uri = None
        self.client = None

    def set_event(self, loop: "urwid.MainLoop", api_uri):
        self.uri = api_uri + "/ws/v1/cluster/apps"
        self.query = {"states": "NEW,NEW_SAVING,SUBMITTED,ACCEPTED,RUNNING"}

        self.client = httpx.Client()

        loop.set_alarm_in(1.2, self.event)

    def event(self, loop, user_data):
        # query
        try:
            resp = self.client.get(self.uri, params=self.query)
        except httpx.HTTPError:
            logger.exception("Failed to query cluster metric")
            return

        # update
        apps = resp.json().get("apps", {})
        if not apps:
            return

        rows = []
        for app in apps.get("app", []):
            row = Row(self.text_attr)
            row.set_data(app)
            rows.append(row)

        self.body.body = rows

        # schedule next query
        loop.set_alarm_in(hdtop.config.get_config("core", "queryInterval"), self.event)


class Row(urwid.Columns):

    display_attr: typing.Dict[str, hdtop.const._Attr]

    def __init__(self, display_attr: dict) -> None:
        super().__init__([])
        self.display_attr = display_attr

    def rows(self, size, focus):
        return 1

    def set_data(self, data: dict):
        sep = (urwid.Text(" "), (urwid.GIVEN, 1, False))

        columns = []
        for column, attr in self.display_attr.items():
            widget = self.get_text(data.get(column, ""), attr.formatter, attr.align)

            if attr.width > 0:
                option = (urwid.GIVEN, attr.width, False)
            else:
                option = (urwid.WEIGHT, -attr.width, False)

            columns += [(widget, option), sep]

        self.contents = columns

    def get_text(self, text, formatter, align):
        text = formatter(text)
        return urwid.Text(text, align=align, wrap=urwid.CLIP)


class HeaderRow(Row):
    def get_text(self, text, formatter, align):
        return urwid.Text(text, align=urwid.LEFT, wrap=urwid.CLIP)
