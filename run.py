
import contextlib
import logging
import os

from logging.handlers import TimedRotatingFileHandler

import click

try:
    import uvloop
except ImportError:
    pass
else:
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

from main import MyClient


@contextlib.contextmanager
def log_setup():
    # Taken from Rapptz' RoboDanny
    try:
        try:
            os.makedirs('logs')
        except FileExistsError:
            pass
        logging.getLogger('discord').setLevel(logging.INFO)

        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s::%(levelname)s:%(filename)s:%(lineno)d - %(message)s')
        fh = TimedRotatingFileHandler(filename='logs/koyomi.log', when='midnight')
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        sh = logging.StreamHandler()
        sh.setFormatter(formatter)
        logger.addHandler(sh)

        yield
    finally:
        # __exit__
        handlers = logger.handlers[:]
        for hdlr in handlers:
            hdlr.close()
            logger.removeHandler(hdlr)

@click.group()
def cli():
    pass


@cli.command()
def run():
    with log_setup():
        MyClient().run()


if __name__ == "__main__":
    cli()
