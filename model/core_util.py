import logging.config
import logging
import os

config = {
    'version': 1,
    'formatters': {
        'simple': {
            'format': '[%(levelname)s]%(asctime)s  %(module)s/%(funcName)s : %(message)s',
        },
        # 其他的 formatter
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
            'formatter': 'simple'
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'log/logging.log',
            'level': 'DEBUG',
            'formatter': 'simple'
        },
        # 其他的 handler
    },
    'loggers': {
        'StreamLogger': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'FileLogger': {
            # 既有 console Handler，还有 file Handler
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
        },
        # 其他的 Logger
    }
}

os.makedirs("log", exist_ok=True)
logging.config.dictConfig(config)

if __name__ == '__main__':
    StreamLogger = logging.getLogger("StreamLogger")
    FileLogger = logging.getLogger("FileLogger")
    FileLogger.debug("111111")
    FileLogger.debug("222222")
    FileLogger.debug("333333")
