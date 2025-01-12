#!/usr/bin/env python3
from app import Main
import argparse


def main():
    build_host = None
    parser = argparse.ArgumentParser()

    parser.add_argument("-b", "--build-host", help="build host", required=True)
    args = parser.parse_args()
    if args.build_host:
        build_host = args.build_host

    app = Main(host=build_host)
    app.run()


if __name__ == '__main__':
    main()
