import time
import tkinter as tk
from tkinter import ttk, Frame
from tkinter import messagebox
from typing import Callable
import os.path

from PIL import Image,ImageTk
import sys

#Trying to abstract stuff (doesn't really work that well)
__all__ = ["RenderLayer", "Circle", "Rect", "Line", "GetMouseCoords"] #What values are visible (from Graphics import *)

class _DrawingObject:
    def __init__(self, screen_pos:tuple[int,int], colour, outline_colour):
        self.x, self.y = screen_pos
        self.col = colour
        self.outline_col = outline_colour

    def draw(self, Canvas: tk.Canvas, still = False):
        pass

class Circle(_DrawingObject):
    """A Circle Drawing Object"""

    def __init__(self, centre: tuple[int, int], colour, radius, outline_colour):
        super().__init__(centre, colour, outline_colour)
        self.radius = radius
    def draw(self, canvas: tk.Canvas, still = False):
        canvas.create_oval(self.x - self.radius, self.y - self.radius,
                           self.x + self.radius, self.y + self.radius,
                           fill=self.col, outline=self.outline_col)

class Line(_DrawingObject):
    """A Line Drawing Object"""
    def __init__(self, begin: tuple[int, int], end: tuple[int, int], colour, width : int | None = None):
        if width is None:
            self.width = 1
        else:
            self.width = width
        super().__init__(begin, colour, None)
        self.begin : tuple[int,int] = begin
        self.end : tuple[int,int] = end
        self.col = colour


    def draw(self, Canvas: tk.Canvas, still = False):
        Canvas.create_line(self.begin[0],self.begin[1],self.end[0],self.end[1],
                           fill=self.col, smooth=True,width=self.width)

class Rect(_DrawingObject):
    """A Rectangle Drawing Object"""
    def __init__(self, screen_pos: tuple[int, int], colour, Size: tuple[int, int], outline_colour):
        super().__init__(screen_pos, colour, outline_colour)
        self.size = Size

    def draw(self, Canvas: tk.Canvas, still = False):
        x = self.x
        y = self.y
        if still:
            x,y = int(Canvas.canvasx(x)), int(Canvas.canvasy(y))
            #print(x,y)
        w,h = self.size
        Canvas.create_rectangle(x,y, x + w, y + h,
                                fill = self.col, outline = self.outline_col)

class RenderLayer:
    """Groups drawing objects together, and manages their drawing order."""
    def __init__(self, layerID:int,still = None):
        self.still = False
        if still:
            self.still = True
        if layerID < 0: raise ValueError(f"Layer ID {layerID} must be >= 0")
        self.layerID = layerID
        self.objects : list = []


    def Draw(self, canvas: tk.Canvas):

        for obj in self.objects:
            obj.draw(canvas,still = self.still)

    def AddObject(self,obj:_DrawingObject):
        self.objects.append(obj)

    def ClearLayer(self):
        self.objects = []

    def __add__(self, other):
        self.objects += other.objects
        return self


current_bay_index=0
starting_module =scroll_bar_percentage = 0
_bays = []

#region Initialise Tkinter Root
_root = tk.Tk()
_root.configure(background="grey5")
_root.title("Patchbay Management System")
_running = False

_root.geometry(f"{1080}x{400}") #Set Size
_root.resizable(False, True) #Don't allow horizontal resizing
_root.maxsize(1080, 800) #Set max height to 800

def on_quit():
    global _running
    _running = False

_root.protocol("WM_DELETE_WINDOW", on_quit)  # When Close Window set running to false
_frame = tk.Frame(_root,background="black")
_frame.grid(column=0,row=0)

OpenFile, SaveFile, AddBay, RemoveBay = tuple([None]*4)


style = ttk.Style()
style.theme_use('clam')

# configure the style
style.configure("Horizontal.TScrollbar", gripcount=0,
    background="gray16", darkcolor="gray24", lightcolor="gray24",
    troughcolor="gray16", bordercolor="gray18", arrowcolor="gray46")
style.configure("Vertical.TScrollbar", gripcount=0,
    background="gray16", darkcolor="gray24", lightcolor="gray24",
    troughcolor="gray16", bordercolor="gray18", arrowcolor="gray46")


menu_bar = tk.Menu(_root)
_root.config(menu=menu_bar)

# File Menu
file_menu = tk.Menu(menu_bar, tearoff=0)



####################SIDE VIEW##########################

side_view = Frame(_root, background='grey5')
side_view.grid(column=1, row=0, padx=5, pady=5,sticky='n')

# Set up Frames
nav_frame = tk.Frame(side_view, bg='grey10')
nav_frame.grid(row=1, column=0, pady=5)

scrollable_frame = tk.Frame(side_view, background='grey10')
scrollable_frame.grid(column=0, row=0)

module_labels = [(tk.Label(scrollable_frame, text=f"Module {str(i + 1).zfill(2)}: C", justify='left', fg="white",
    bg="grey10", font=('Aptos', 30)))
    for i in range(6)]
for i in range(6):
    module_labels[i].grid(column=0, row=i)

scroll_bar_percentage = 0


def updateStartingModule(*args):
    global starting_module, sv_scrollbar, scroll_bar_percentage
    if sv_scrollbar is None: return
    if args[0] == 'moveto':
        scroll_bar_percentage = float(args[1])

    if len(args) == 3:
        a, b, c = args
        if c == 'pages':
            scroll_bar_percentage += 0.333333 * float(b)
        else:
            scroll_bar_percentage += float(b) * 0.04166  # 1/24

    scroll_bar_percentage = max(0., min(1., scroll_bar_percentage))
    starting_module = min(round(scroll_bar_percentage * 18), 18)
    sv_scrollbar.set(scroll_bar_percentage, scroll_bar_percentage + 1 / 24)
    UpdateView()


sv_scrollbar = ttk.Scrollbar(side_view, orient="vertical", command=updateStartingModule)
sv_scrollbar.set(scroll_bar_percentage, scroll_bar_percentage + 1 / 24)
sv_scrollbar.grid(row=0, column=1, sticky="ns", padx=5)


def UpdateView() -> None:
    global current_bay_index, _bays

    if current_bay_index >= len(_bays) or len(_bays) == 0:
        return

    bay = _bays[current_bay_index]

    if not module_labels or len(module_labels) < 6:
        return

    index_label['text'] = current_bay_index + 1
    for i in range(6):
        index = i + starting_module
        if index < len(bay.modules):
            module_labels[i]['text'] = f"Module {str(index + 1).zfill(2)}: {bay.modules[index].GetRule()}"
        else:
            module_labels[i]['text'] = ''


def Increment() -> None:
    global current_bay_index
    current_bay_index = (current_bay_index + 1) % len(_bays)
    UpdateView()


def Decrement() -> None:
    global current_bay_index
    current_bay_index = (current_bay_index - 1) % len(_bays)
    UpdateView()


previous_button = tk.Button(nav_frame, command=Decrement, text='Previous', bg='grey')
next_button = tk.Button(nav_frame, command=Increment, text='Next', bg='grey')
index_label = tk.Label(nav_frame, text='1', bg='grey')
refresh_button = tk.Button(nav_frame, text='Refresh', bg='grey', command=UpdateView)

previous_button.grid(row=0, column=0, padx=5)
index_label.grid(row=0, column=1, padx=5)
next_button.grid(row=0, column=2, padx=5)
refresh_button.grid(row=1, column=0, columnspan=3, pady=5, sticky="ew")

#endregion



#Interal Use Only
class Engine:
    def __init__(self,
                 UpdateMethod : Callable[[], None],
                 ClickMethod : Callable[[tuple[int,int]], None],
                 open_file : Callable[[],  None],
                 save_file : Callable[[],  None],
                 add_bay : Callable[[], None],
                 remove_bay : Callable[[],  None],
                _frame = _frame
    ):
        self._layers : dict[int,RenderLayer] = {}
        self._running = False
        self._updateMethod = UpdateMethod


        self._canvas: tk.Canvas = tk.Canvas(_frame, width=800, height=800,
                                            background='white',
                                            highlightthickness=0)
        
        


        self._canvas.bind("<Motion>", _UpdateCoords)
        def m(event):
            x = self._canvas.canvasx(event.x)#Screen x to Canvas x
            y = self._canvas.canvasy(event.y)#Screen y to Canvas y
            ClickMethod((x,y))


        self._canvas.bind("<Button-1>",m)
        self._canvas.grid(row=0, column=0, sticky="nsew")

        
        

        v_scroll = ttk.Scrollbar(_frame, orient="vertical", command=self._canvas.yview)
        v_scroll.grid(row=0, column=1, sticky="ns")

        self._canvas.configure(yscrollcommand=v_scroll.set)
        self._canvas.configure(scrollregion=(0, 0, 750, 2000))

        _frame.columnconfigure(0, weight=1)
    

        _RenderBackground(self._canvas) #Draw the background (so not blank if interrupeted)







        global OpenFile, SaveFile, AddBay, RemoveBay

        OpenFile, SaveFile, AddBay, RemoveBay = (open_file,
            save_file,
            add_bay,
            remove_bay)

        file_menu.add_command(label="Open", command=OpenFile)
        file_menu.add_command(label="Save", command=SaveFile)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=on_quit)
        menu_bar.add_cascade(label="File", menu=file_menu)

        # Bay Settings
        bay_menu = tk.Menu(menu_bar, tearoff=0)
        bay_menu.add_command(label="Add Bay", command=AddBay)
        bay_menu.add_command(label="Delete Current Bay", command=RemoveBay)

        menu_bar.add_cascade(label="Bays", menu=bay_menu)

    def mainloop(self):
        global _running
        _running = True
        while _running:
            self._canvas.delete("all")
            self._updateMethod()
            _RenderBackground(self._canvas)
            for ID in self._layers:
                self._layers[ID].Draw(self._canvas)
            _root.update() #Actually show the changes
            time.sleep(1.0 / 60)  # Max to 60 fps


    def addRenderLayer(self, layer: RenderLayer):
        """Adds the Render Layer to the scene.
        Auto Merges Layers with same ID"""
        if layer.layerID in self._layers:
            self._layers[layer.layerID] += layer
        else:
            self._layers.update({layer.layerID:layer})
            self._layers = dict(sorted(self._layers.items())) #Sort the Layers.


    def Clear(self):
        self._layers.clear()

    @property
    def canvas(self):
        return self._canvas



#region Background Renderer
try:
    _image = Image.open(os.path.join(os.path.dirname(__file__), "Tile (900x900).png"))
except FileNotFoundError:
    print("Background image not found.")
    messagebox.showerror("Error", "Could not find 'Tile (900x900).png'. Please make sure the file exists.")
    sys.exit(0)


tk_texture = ImageTk.PhotoImage(_image)

def _RenderBackground(canvas:tk.Canvas):
    canvas.texture_image = tk_texture

    img_width = _image.width
    img_height = _image.height
    for x in range(0, 2000 + img_width, img_width):
        for y in range(0, 2000 + img_width, img_height):
            canvas.create_image(x, y, image=tk_texture, anchor="nw")


#endregion


__Mx, __My = -1,-1
def _UpdateCoords(event):
    global __Mx,__My
    __Mx, __My = event.x, event.y


def GetMouseCoords():   return __Mx, __My


def UpdateBays(bay_system: dict):
    global _bays
    _bays = [bay_system[key] for key in bay_system]

