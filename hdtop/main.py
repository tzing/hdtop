"""Main loop / UI handler for hdtop. Not the main loop.
"""
import argparse
import sys

import urwid
import urwid.raw_display

import hdtop.apps_status
import hdtop.cluster_metric
import hdtop.config
import hdtop.const


def setup_argparse():
    """argparser for starting main UI"""
    parser = argparse.ArgumentParser()
    parser.set_defaults(action="config", func=start_ui)
    parser.add_argument(
        "uri",
        nargs="?",
        type=hdtop.const.extract_api_base,
        default=hdtop.config.get_config("core", "hadoopAddress"),
        help="URI to hadoop cluster",
    )
    return parser


def start_ui(args):
    """Entry point for UI main loop."""
    # pre check
    if not args.uri:
        print("Config `core.hadoopAddress` is required.", file=sys.stderr)
        print("Use `hdtop config {wanted_key} <value>` to set one.", file=sys.stderr)
        return 1

    # start main loop
    MainDisplay().main(args.uri)


class MainDisplay:
    """Main display controller."""

    def __init__(self) -> None:
        # panels
        self.upper_pane = hdtop.cluster_metric.ClusterMetricMonitor()
        self.body = hdtop.apps_status.AppStatus()

        # footer
        footer_text = [
            # platte, text
            ("footer key", "F10"),
            ("footer", "Quit"),
        ]
        self.footer = urwid.AttrWrap(urwid.Text(footer_text), "footer")

        # main view
        self.view = urwid.Frame(
            header=self.upper_pane,
            body=self.body,
            footer=self.footer,
            focus_part="header",
        )

        # screen
        self.screen = urwid.raw_display.Screen()
        self.screen.set_terminal_properties(16, False)

        # placeholder
        self.loop = None

    def main(self, api_uri):
        self.loop = urwid.MainLoop(
            widget=self.view,
            palette=hdtop.const.PALETTE,
            screen=self.screen,
            unhandled_input=self.unhandled_input,
        )

        self.upper_pane.set_event(self.loop, api_uri)
        self.body.set_event(self.loop, api_uri)

        self.loop.run()

    def unhandled_input(self, key):
        if key in ("q", "Q", "f10"):
            raise urwid.ExitMainLoop()
