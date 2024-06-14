# logger_config.py
import logging
import os

# Clear the predictor.log file
predictor_log_path = os.path.abspath("data/tmp/predictor.log")
with open(predictor_log_path, 'w'):
    pass

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
log_handler = logging.FileHandler(predictor_log_path)
formatter = logging.Formatter('%(asctime)s - %(message)s')
log_handler.setFormatter(formatter)

logger = logging.getLogger('euro2024predictor')
logger.setLevel(logging.DEBUG)
logger.addHandler(log_handler)

# Avoid duplicate logs in the console
logger.propagate = False
