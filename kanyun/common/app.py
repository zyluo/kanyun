import logging
import traceback
import ConfigParser

class App():
    """Application Framework:
    Depend:
        xxxx.conf:
            [log]
            file=xxxxx.log
    """
    def __init__(self, conf, 
                 log="/tmp/app.log", 
                 level=logging.INFO,
                 format='%(asctime)s %(levelname)s %(message)s'):
        """conf example:
            conf = 'deduct.conf'  --> ./deduct.conf --> /etc/deduct.conf
        """
        self.logger = None
        self.cfg = None
        self.config = None
        self.log_file = log
        self.log_level = level
        self.format = format
        
        self.config = ConfigParser.ConfigParser()
        if len(self.config.read(conf))==0:
            self.config.read("/etc/" + conf)
            
        try:
            cfg = dict(self.config.items('log'))
            if cfg.has_key('file'):
                self.log_file = cfg['file']
        except ConfigParser.NoSectionError:
            cfg = None

    def get_logger(self):
        if self.logger is None:
            self.logger = logging.getLogger()
            handler = logging.FileHandler(self.log_file)
            formatter = logging.Formatter(self.format)
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(self.log_level)
            
        return self.logger
            
    def get_cfg(self, item):
        cfg = None
                
        try:
            cfg = dict(self.config.items(item))
        except ConfigParser.NoSectionError:
            pass
            
        return cfg
        
