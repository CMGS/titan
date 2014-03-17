#!/usr/bin/python
#coding:utf-8

from dev_server.dev_appserver import main, populate_argument_parser

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    populate_argument_parser(parser)

    args = parser.parse_args()
    main(args)

