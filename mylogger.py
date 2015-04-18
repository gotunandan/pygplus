
import logging


class MyLogger:

    @classmethod
    def setupLogger(cls, moduleName='main', level=logging.INFO):
        mainLogger = logging.getLogger(moduleName)
        mainLogger.setLevel(level)
        fileLogger = logging.FileHandler('{}.log'.format(moduleName))
        fileLogger.setLevel(level)
        logFormat = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fileLogger.setFormatter(logFormat)
        mainLogger.addHandler(fileLogger)
        return mainLogger
