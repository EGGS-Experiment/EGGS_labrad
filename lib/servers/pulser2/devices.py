from artiq_master.device_db import device_db

#todo: need get_devices; device_mgr?

class Devices:
    def __init__(self):
        self.device_db = device_db
        self.cores = {}
        self.ttls = {}
        self.edge_counters = {}
        self.urukuls = {}
        self.ad9910s = {}
        for kk in device_db:
            if "module" in device_db[kk]:
                module = device_db[kk]["module"]
                content = device_db[kk]
                if module == "artiq.coredevice.core":
                    self.cores[kk] = content
                if module == "artiq.coredevice.ttl":
                    self.ttls[kk] = content
                elif module == "artiq.coredevice.edge_counter":
                    self.edge_counters[kk] = content
                elif module == "artiq.coredevice.urukul":
                    self.urukuls[kk] = content
                elif module == "artiq.coredevice.ad9910":
                    self.ad9910s[kk] = content