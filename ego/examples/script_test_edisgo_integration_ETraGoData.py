import logging
import sys

from pypsa import Network

from ego.tools.edisgo_integration import _ETraGoData

logger = logging.getLogger(__name__)

if __name__ == "__main__":

    logger = logging.getLogger(__name__)
    logger.propagate = False
    log_level = logging.DEBUG
    logger.setLevel(log_level)

    console_handler = logging.StreamHandler(stream=sys.stdout)
    console_handler.setLevel(log_level)
    stream_formatter = logging.Formatter("%(name)s - %(levelname)s: %(message)s")
    console_handler.setFormatter(stream_formatter)
    logger.addHandler(console_handler)

    class ETraGo:
        def __init__(self):
            self.network = Network()
            self.network.import_from_csv_folder(
                "/home/local/RL-INSTITUT/malte.jahn/Desktop/etrago-results"
            )

    etrago_obj = ETraGo()
    etrago_data_obj = _ETraGoData(etrago_obj)
