
import logging
import os

from logging.handlers import TimedRotatingFileHandler

import click

from main import MyClient


@click.group()
def cli():
    pass


@cli.command()
def run():

    if not os.path.exists('logs'):
        os.makedirs('logs')
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s::%(levelname)s:%(filename)s:%(lineno)d - %(message)s')
    fh = TimedRotatingFileHandler(filename='logs/koyomi.log', when='midnight')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    sh = logging.StreamHandler()
    sh.setFormatter(formatter)
    logger.addHandler(sh)
    MyClient().run()


if __name__ == "__main__":
    cli()