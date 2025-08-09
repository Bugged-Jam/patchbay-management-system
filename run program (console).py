import tkinter as tk
import subprocess

import os
Windows = (os.name == 'nt')


root = tk.Tk()
root.config(background="#111111")
title = tk.Label(root, text="PatchBay Manager",font=('Helvetica',30),bg="#111111",fg = 'white')
title.pack(padx=10)

def load():
    root.destroy()

    if Windows:
        subprocess.call('python code\\main.py --f')
    else:
        subprocess.call('python3 code\\main.py --f')
   
def new():
    root.destroy()
    
    if Windows:
        subprocess.call('python code\\main.py')
    else:
        subprocess.call('python3 code\\main.py')
   


load_button = tk.Button(root,text="Open",command=load,width=30, background="#303030",fg="white")
new_button = tk.Button(root,text="New",command=new,width=30, background="#303030",fg="white")

load_button.pack(pady=20)
new_button.pack(pady=20)

root.mainloop()