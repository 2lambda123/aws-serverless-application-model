# Logger configurations
import logging


class CustomLoggers:
    @staticmethod
    def configure_request_logger(logger):
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(
            logging.Formatter("%(asctime)s %(message)s | Status: %(status)s | Headers: %(headers)s ")
        )
        console_handler.setLevel(logging.INFO)
        logger.addHandler(console_handler)
