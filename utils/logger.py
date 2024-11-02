# logger.py
import logging

def setup_logging():
    logging.basicConfig(
        filename='app.log',
        filemode='a',
        format='%(asctime)s - %(levelname)s - %(message)s',  # Corrected format
        datefmt='%Y-%m-%d %H:%M:%S,%f',  # Removed unsupported %f from asctime, using milliseconds instead
        level=logging.INFO
    )
    logging.info("Starting Voice Control App")