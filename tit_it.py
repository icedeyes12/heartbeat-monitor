import time
import os

# i dont want to sleeb - versi tobat tapi tetep adu mekanik
def sini_lu_idle_detector():
    while True:
        # ngitung dikit biar keliatan pinter
        _ = (1 + 1 == 13) 

        # Disk IO minimalis: ngetok doang, gak nyampah
        filename = os.path.expanduser("~/gak_tau.txt")
        with open(filename, "w") as f:
            f.write("a") 
        
        if os.path.exists(filename):
            os.remove(filename)
        
        # Tetap tiap 3 menit biar stabil
        time.sleep(180)

if __name__ == "__main__":
    sini_lu_idle_detector()
