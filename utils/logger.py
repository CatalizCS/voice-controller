# logger.py
import logging

def setup_logging():
    logging.basicConfig(
        filename='app.log',
        filemode='a',
        format='%(Y)s-%(m)s-%(d)s %H:%M:%S,%f - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S,%f',
        level=logging.INFO
    )
    logging.info("Starting Voice Control App")