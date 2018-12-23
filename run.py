import logging
import os
import sys

import config
from app import routes

default_log_level = logging.DEBUG
default_log_file = 'app.log'
default_log_entry_format = '%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s'

if __name__ == "__main__":

    config_file_path = config.get_config_path()
    if not os.path.exists(config_file_path):
        logging.fatal('Configuration file %s not found', config_file_path)
        sys.exit(1)

    conf = config.load_config(config_file_path)

    log_file_handler = logging.FileHandler(conf.get('logger.file', default_log_file), 'a')
    formatter = logging.Formatter(conf.get('logger.format', default_log_entry_format))
    log_file_handler.setFormatter(formatter)
    log_file_handler.setLevel(conf.get('logger.level', default_log_level))

    stream_log_handler = logging.StreamHandler()
    stream_log_handler.setFormatter(logging.Formatter(default_log_entry_format))

    logger = logging.getLogger()
    logger.addHandler(log_file_handler)
    logger.addHandler(stream_log_handler)
    logger.setLevel(default_log_level)

    routes.app.secret_key = os.urandom(24)
    routes.app.jinja_env.add_extension('jinja2.ext.loopcontrols')
    routes.app.run(debug=False)
