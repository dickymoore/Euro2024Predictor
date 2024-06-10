import logging
from argparse import ArgumentParser

from scripts.config import load_config
from scripts.calculations import perform_calculations

# Configure logging
logger = logging.getLogger(__name__)

def main(debug=False):
    if debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    config = load_config()
    logger.info('Running Predictor')
    
    perform_calculations(config)
    
    # Simulate matches
    from scripts.group_match_calculations import main as simulate_matches
    simulate_matches()

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    args = parser.parse_args()
    main(debug=args.debug)
