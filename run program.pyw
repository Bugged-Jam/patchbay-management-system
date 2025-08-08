import tkinter as tk
import subprocess
import sys


import os
Windows = (os.name == 'nt')


root = tk.Tk()
root.config(background="#111111")
title = tk.Label(root, text="PatchBay Manager",font=('Helvetica',30),bg="#111111",fg = 'white')
title.pack(padx=10)

def load():
    print(Windows)
    root.destroy()

    if Windows:
        subprocess.call([sys.executable, 'code\\main.py', '--f'],
            creationflags=subprocess.CREATE_NO_WINDOW)
    else:
        subprocess.Popen(
            [sys.executable, 'code/main.py', '--f'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
def new():
    print(Windows)
    root.destroy()
    
    if Windows:
        subprocess.call([sys.executable, 'code\\main.py'],
            creationflags=subprocess.CREATE_NO_WINDOW)
    else:
        subprocess.Popen(
            [sys.executable, 'code/main.py'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )

load_button = tk.Button(root,text="Open",command=load,width=30, background="#303030",fg="white")
new_button = tk.Button(root,text="New",command=new,width=30, background="#303030",fg="white")

load_button.pack(pady=20)
new_button.pack(pady=20)

root.mainloop()