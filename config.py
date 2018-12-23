import configparser
import logging
import os
import sys


def load_config(file, config={}):
    config = config.copy()
    parser = configparser.ConfigParser()
    parser.read(file)
    for section in parser.sections():
        name = section.lower()
        for opt in parser.options(section):
            config[name + "." + opt.lower()] = parser.get(section, opt)
    return config


def get_config_path():
    mode_default = 'test'
    env_mode = os.getenv('APP_MODE', None)

    config_file = {
        "prod": "config.prod.ini",
        "test": "config.test.ini"
    }

    if len(sys.argv) >= 2:
        mode = sys.argv[1]
    elif env_mode:
        mode = env_mode
    else:
        mode = mode_default

    if config_file.get(mode) is None:
        logging.error("Invalid value for mode arg[%s]", sys.argv[1])
        logging.info('Use test configuration file')
        mode = mode_default

    return os.path.abspath(config_file[mode])
