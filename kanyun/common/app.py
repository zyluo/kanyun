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
    def __init__(self, conf, log=None):
        """conf example:
            conf = 'deduct.conf'  --> ./deduct.conf --> /etc/deduct.conf
        """
        self.logger = None
        self.cfg = None
        self.config = None
        self.log_file = "/tmp/app.log"
        self.log_level = logging.NOTSET
        
        self.config = ConfigParser.ConfigParser()
        if len(self.config.read(conf))==0:
            self.config.read("/etc/" + conf)
            
        cfg = dict(self.config.items('log'))
        if log is None:
            self.log_file = cfg['file']
        else:
            self.log_file = log
        
    def getLogger(self):
        if self.logger is None:
            self.logger = logging.getLogger()
            handler = logging.FileHandler(self.log_file)
            self.logger.addHandler(handler)
            self.logger.setLevel(self.log_level)
            
        return self.logger
            
    def getCfg(self, item):
        cfg = None
        try:
            cfg = dict(self.config.items(item))
        except ConfigParser.NoSectionError:
            pass
            
        return cfg
        
if __name__ == '__main__':
    app = App("test.conf")
    
    log = app.getLogger()
    log.debug("app test")
    
    cfg = app.getCfg("Test")
    print cfg
    
