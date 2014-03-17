#!/usr/bin/python
# encoding: UTF-8

import os, sys
import config
config.init_config('config.yaml', 'local_config.yaml')

from application import TitanApp

def populate_argument_parser(parser):
    parser.add_argument('-p', '--port', type=int, default=8080,
                        help="port for the server to run on [default: 8080]")
    parser.add_argument('--pidfile', help="file path to put pid in")
    parser.add_argument('--daemon', action='store_true', default=False,
                        help="daemonize the server process [default: false]")
    parser.add_argument('-w', '--nworkers', default='2',
                        help="workers number [default: 2]")
    parser.add_argument('-t', '--timeout', default='300',
                        help="request timeout sec [default: 300]")

def main(args):
    return run_server(args.port, args.pidfile, args.daemon, args.nworkers, args.timeout)

def run_server(port=8080, pidfile=None, \
        daemon=False, nworkers='2', timeout='300'):

    sys.argv = ['titan serve', '-b', '0.0.0.0:{0}'.format(port)]

    if pidfile:
        sys.argv += ['-p', pidfile]

    if daemon:
        sys.argv += ['-D']

    sys.argv += ['-k', 'gevent']
    sys.argv += ['-n', 'titan run in %d' % port]

    sys.argv += ['-w', nworkers]
    sys.argv += ['-t', timeout]

    os.environ['TITAN_APPROOT'] = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    sys.argv.append(os.environ['TITAN_APPROOT'])  # must be the only positional parameter

    app = TitanApp()
    return app.run()

