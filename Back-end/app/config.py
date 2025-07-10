import sys
import os
from dotenv import load_dotenv
import logging


def load_configurations(app):
    load_dotenv()

def configure_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout,
    )
