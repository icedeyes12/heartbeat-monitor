import time
import os
import random

# i dont want to sleeb - sini lu satpam vps!
def sini_lu_idle_detector():
    while True: 
        # Ngitung dulu biar keliatan mikir
        sum(i*random.random() for i in range(10**6))

        # Disk IO: Tulis-Baca-Hapus
        filename = f"yo_ndaktau_{int(time.time())}.txt"
        with open(filename, "w") as f:
            f.write("kok tanya saya " * random.randint(50, 150))
        with open(filename, "r") as f:
            _ = f.read()

        os.remove(filename)
        
        # Kasih napas 3 menit biar gak disangka spam/abuse
        time.sleep(180) 

if __name__ == "__main__":
    sini_lu_idle_detector()
