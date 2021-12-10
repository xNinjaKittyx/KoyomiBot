import asyncio
import contextlib
import logging
import os
from logging.handlers import RotatingFileHandler

import click

try:
    import uvloop
except ImportError:
    pass
else:
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

import faulthandler

from koyomibot.main import MyClient

faulthandler.enable()


@contextlib.contextmanager
def log_setup() -> None:
    try:
        try:
            os.makedirs("logs")
        except FileExistsError:
            pass
        logging.getLogger("discord").setLevel(logging.INFO)

        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter("%(asctime)s::%(levelname)s:%(module)s:%(lineno)d - %(message)s")

        fh = RotatingFileHandler(filename="logs/koyomi.log", maxBytes=10 * 1024 * 1024, backupCount=10)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

        sh = logging.StreamHandler()
        sh.setFormatter(formatter)
        logger.addHandler(sh)

        yield
    except BaseException as e:
        logger.exception(e)
        raise
    finally:
        # __exit__
        handlers = logger.handlers[:]
        for hdlr in handlers:
            hdlr.close()
            logger.removeHandler(hdlr)


@click.group()
def cli() -> None:
    pass


@cli.command()
@click.option("--debug", "-d", is_flag=True, required=False, default=False)
def run(debug) -> None:
    with log_setup():
        MyClient(debug).run()


if __name__ == "__main__":
    cli()
