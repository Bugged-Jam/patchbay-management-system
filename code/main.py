import random
from tkinter import messagebox
from typing import Tuple
import argparse

import Graphics

ColourIndex = 0

parser = argparse.ArgumentParser()
parser.add_argument('--f', action='store_true', help='Run the extra function')
args = parser.parse_args()



#region Classes

class Connector:
    def __init__(self, is_out: bool, module_position: Tuple[int, int], bayIndex: int, moduleIndex: int):
        if bayIndex < 0: raise ValueError(f"Bay Index ({bayIndex}) has be greater than 0")
        self.is_connected = False
        x, y = module_position
        if is_out: y += 30
        self.position = x, y
        self.tint = None
        self.bayIndex = bayIndex
        self.moduleIndex = moduleIndex

    def sqrDist(self, x, y) -> int:
        pX, pY = self.position
        return (x - pX) ** 2 + (y - pY) ** 2


class Module:
    def __init__(self, position: Tuple[int, int], bayIndex: int, moduleIndex: int):
        self.input = Connector(False, position, bayIndex=bayIndex, moduleIndex=moduleIndex)
        self.output = Connector(True, position, bayIndex=bayIndex, moduleIndex=moduleIndex)

    def GetRule(self):

        if not self.output.is_connected:
            return 'C'
        elif self.input.is_connected:
            return 'B'
        return 'A'


class Bay:
    def __init__(self, offsetX, offsetY, bayIndex: int):
        self.offset = offsetX, offsetY
        self.modules = [Module((30 * i + offsetX, offsetY), bayIndex=bayIndex, moduleIndex=i) for i in range(24)]
        self.bayIndex = bayIndex

    def GenerateRenderLayers(self) -> Tuple[Graphics.RenderLayer, Graphics.RenderLayer]:
        layer1, layer2 = Graphics.RenderLayer(1), Graphics.RenderLayer(2)
        x, y = self.offset
        pos = x - 15, y - 15
        layer1.AddObject(
            Graphics.Rect(pos, "grey10", (690 + 30, 30 + 30), None))

        engine.addRenderLayer(layer1)

        for mod in self.modules:
            layer2.AddObject(
                Graphics.Circle(mod.input.position,
                                tint_to_col.get(mod.input.tint, 'grey20'),
                                10, None)
            )
            layer2.AddObject(
                Graphics.Circle(mod.output.position,
                                tint_to_col.get(mod.output.tint, 'grey20'),
                                10, None)
            )
        return layer1, layer2


class Connection:
    def __init__(self, From: Connector, To: Connector, colour = None):
        global ColourIndex
        self.ID = random.randint(0, 0xFFFFFF)
        if colour is None:
            self.col = ['red', 'blue', 'yellow', 'green'][ColourIndex]
        else:
            self.col = colour


        self.From: Connector = From
        self.To: Connector = To

        self.From.tint = self.col
        self.To.tint = self.col

        self.From.is_connected = True
        self.To.is_connected = True

        ColourIndex = (ColourIndex + 1) % 4

        Graphics.UpdateBays(bay_systems)


#endregion

connections: list[Connection] = []
inp: Connector | None = None
is_clicked = False

tint_to_col = {
    'red': "#4C1E1E",
    'blue': "#0D0D44",
    'yellow': "#7F7F19",
    'green': "#0A330A"
}

MAX_BAYS = 8
selected_bay = 0

bay_systems = {0: Bay(60, 60, 0)}


def AddBay(overrideIndex=-1):
    global selected_bay
    i = 0

    if overrideIndex == -1:
        while i in bay_systems:
            i += 1
            if i == MAX_BAYS: return
    else:
        i = overrideIndex

    selected_bay = i

    bay_systems.update({i: Bay(60, 60 + i * 80, i)})
    Graphics.UpdateBays(bay_systems)
    pass


def RemoveBay():  #Removes the currently selected bay
    global connections

    for conn in connections:
        if conn.From.bayIndex == selected_bay:
            conn.To.tint = None
        if conn.To.bayIndex == selected_bay:
            conn.From.tint = None

    connections = [
        conn for conn in connections
        if conn.From.bayIndex != selected_bay and conn.To.bayIndex != selected_bay
    ]

    if selected_bay in bay_systems:
        del bay_systems[selected_bay]

    Graphics.UpdateBays(bay_systems)


def OpenFile():
    global bay_systems, connections
    from tkinter import filedialog
    file_path = filedialog.askopenfilename(filetypes=[("Nerd Files", "*.bsys")])
    if file_path == '': return

    try:
        with (open(file_path, 'r') as f):
            bay_systems.clear()
            connections.clear()
            first = True
            for line in f.readlines():
                if first:
                    for bay_index in line.split('b'):
                        if bay_index[:1] == '': continue
                        bay_in = int(bay_index[:1])
                        AddBay(bay_in)
                    first = False
                    continue
                if line[0] != 'c': raise ValueError(f"File line invalid {line}")

                colour = {'r': 'red', 'b': 'blue', 'y': 'yellow', 'g': 'green'}[line[1]]
                code = line[2:]
                bF = int(code[1:3])
                mF = int(code[4:6])
                bT = int(code[7:9])
                mT = int(code[10:12])

                conn = Connection(From=bay_systems[bF].modules[mF].input,
                                  To=bay_systems[bT].modules[mT].output,colour=colour)

                connections.append(conn)

    except FileNotFoundError as err:
        messagebox.showerror("Error", f"Could not find {err.filename}")



def SaveFile():
    from tkinter import filedialog
    file_path = filedialog.asksaveasfilename(filetypes=[("Patchbay System File", "*.bsys")], defaultextension=".bsys")
    if file_path == '': return

    with open(file_path, 'w') as f:
        opening_line = ''
        for bay in bay_systems:
            opening_line += f'b{bay}'
        f.write(opening_line)

        for connect in connections:
            f.write("\nc" + connect.col[0]
                    + f"b{str(connect.From.bayIndex).zfill(2)}"
                    + f"m{str(connect.From.moduleIndex).zfill(2)}"
                    + f"b{str(connect.To.bayIndex).zfill(2)}"
                    + f"m{str(connect.To.moduleIndex).zfill(2)}")




cutting_mode = False
cutting_from: None | tuple[int, int] = None

foreground = Graphics.RenderLayer(10, still=True)

foreground.AddObject(Graphics.Rect((0, 0), 'red', (20, 20), outline_colour=None))


def Main():
    global foreground, cutting_mode

    engine.Clear()  #Clear the Screen
    engine.addRenderLayer(foreground)

    Mx, My = Graphics.GetMouseCoords()
    Mx, My = int(engine.canvas.canvasx(Mx)), int(engine.canvas.canvasy(My))  # Screen Pos to Canvas Pos

    if cutting_mode and cutting_from is not None:
        knifeLayer = Graphics.RenderLayer(4)
        knifeLayer.AddObject(
            Graphics.Line(cutting_from, (Mx, My)
                          , colour='red', width=1)
        )
        engine.addRenderLayer(knifeLayer)

    layer1 = Graphics.RenderLayer(1)
    layer2 = Graphics.RenderLayer(2)

    for gridCoord in bay_systems:
        l1, l2 = bay_systems[gridCoord].GenerateRenderLayers()
        layer1, layer2 = layer1 + l1, layer2 + l2

    engine.addRenderLayer(layer1)
    engine.addRenderLayer(layer2)

    connLayer = Graphics.RenderLayer(3)
    for connection in connections:
        connLayer.AddObject(
            Graphics.Line(connection.From.position, connection.To.position,
                          connection.col, width=3)
        )

    engine.addRenderLayer(connLayer)

    if inp is not None and is_clicked:  #If there's a pending connection
        pending_connection_layer = Graphics.RenderLayer(4)
        pending_connection_layer.AddObject(
            Graphics.Line(inp.position, (Mx, My),
                          ['red', 'blue', 'yellow', 'green'][ColourIndex],
                          width=1))
        engine.addRenderLayer(pending_connection_layer)

    return


def OnClick(mousePos: tuple[int, int]):
    global inp, is_clicked, selected_bay, cutting_mode, cutting_from, foreground
    x, y = mousePos

    if 0 < x < 20 and 0 < y < 20:
        cutting_mode = not cutting_mode

        foreground.ClearLayer()
        foreground.AddObject(
            Graphics.Rect((0, 0),
                          'red' if not cutting_mode else 'green',
                          (20, 20),
                          outline_colour=None))
        is_clicked = False
        return

    if cutting_mode:
        if cutting_from is None:
            cutting_from = mousePos
            return

        delete = [False for _ in connections]
        for i, connection in enumerate(connections):
            cutting_to = mousePos

            pointC = connection.From.position
            pointD = connection.To.position

            pointA = cutting_from
            pointB = cutting_to

            a, b = pointD[0] - pointC[0], pointD[1] - pointC[1]
            c, d = pointA[0] - pointB[0], pointA[1] - pointB[1]
            x, y = pointA[0] - pointC[0], pointA[1] - pointC[1]

            det = a * d - b * c

            if det == 0: continue

            t = (d * x - c * y) / det
            s = (a * y - b * x) / det

            if 0 <= s <= 1 and 0 <= t <= 1:
                connection.To.tint = None
                connection.To.is_connected = False
                connection.From.tint = None
                connection.From.is_connected = False

                delete[i] = True

        connections[:] = [
            conn for i, conn in enumerate(connections)
            if not delete[i]
        ]

        cutting_from = None

    else:

        for bayIndex in bay_systems:
            bay = bay_systems[bayIndex]
            for module in bay.modules:

                if not is_clicked:
                    if module.input.is_connected: continue
                    if module.input.sqrDist(x, y) <= 225:  # if within 15 pixels
                        is_clicked = True
                        inp = module.input

                        selected_bay = bayIndex

                        return
                elif module.output.sqrDist(x, y) <= 225:  # if within 15 pixels
                    if module.output.is_connected: continue
                    is_clicked = False
                    if connections is not None:
                        connections.append(Connection(inp, module.output))

                    selected_bay = bayIndex

                    return


if __name__ == '__main__':
    
    

    engine = Graphics.Engine(Main, OnClick,
                             OpenFile, SaveFile,
                             AddBay, RemoveBay)
    if args.f:
        OpenFile()
    Graphics.UpdateBays(bay_systems)
    engine.mainloop()
