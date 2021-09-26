import os, sdcard

class logger():
    
    def __init__(self, spi, pin):
        sd = sdcard.SDCard(spi, pin)
        vfs = os.VfsFat(sd)
        os.mount(vfs, "/fc")
        print("Filesystem check")
        files = os.listdir("/fc")
        
        self.columns = ['AcX','AcY','AcZ','GyX','GyY','GyZ','temp','press','alt','avg_acx','avg_alt','launch_detect','apogee_detect','flight_mode'];
        self.filename = '/fc/log_' + str(len(files) + 1) + '.csv'
        line = ','.join(self.columns) + "\n"
 
        with open(self.filename, "w") as f:
            n = f.write(line)
            print(n, "bytes written")

    def write_line(self, line):
        print(line)
        # todo: if len(line) != len(self.columns): throw a wobbler
        log_line = ','.join(str(e) for e in line) + "\n"
        with open(self.filename, "a") as f:
            f.write(log_line)