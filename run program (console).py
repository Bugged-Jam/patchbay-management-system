import tkinter as tk
import subprocess


root = tk.Tk()
root.config(background="#111111")
title = tk.Label(root, text="PatchBay Manager",font=('Helvetica',30),bg="#111111",fg = 'white')
title.pack(padx=10)

def load():
    root.destroy()

    subprocess.call('python code\\main.py --f')
   
def new():
    root.destroy()
    subprocess.call('python code\\main.py --f')

load_button = tk.Button(root,text="Open",command=load,width=30, background="#303030",fg="white")
new_button = tk.Button(root,text="New",command=new,width=30, background="#303030",fg="white")

load_button.pack(pady=20)
new_button.pack(pady=20)

root.mainloop()