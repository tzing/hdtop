import argparse

import hdtop.config
import hdtop.const
import hdtop.main


_SUBPARSERS = {
    "start": hdtop.main.setup_argparse,
    "config": hdtop.config.setup_argparse,
}


def main():
    """The 'real' entry point of this program"""
    # parse args
    parser = argparse.ArgumentParser(
        prog=hdtop.const.PROG_NAME, description=hdtop.const.DESCRIPTION
    )
    parser.add_argument(
        "action",
        default="start",
        nargs="?",
        choices=_SUBPARSERS,
        help="Action for the program",
    )

    args, remain = parser.parse_known_args()

    # parse sub args
    subparser: argparse.ArgumentParser = _SUBPARSERS[args.action]()
    args = subparser.parse_args(remain, args)

    # action
    return args.func(args)


exit(main())
