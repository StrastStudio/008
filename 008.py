import pygame as pg
import sys
import xml.etree.ElementTree as ET
import json
from all_colors import *

def ReadXmlFile(Name):
    Tree = ET.parse(Name)
    Root = Tree.getroot()
    return Root

s = pg.display.set_mode((1280, 720), vsync=1)
vec2 = pg.math.Vector2
clock = pg.time.Clock()
pg.init()

class Fonts:
    def __init__(self, LoadFonts):
        self.CreaingChars()
        self.Fonts = LoadFonts(self.LoadFontFromTtf, self.LoadFont)

    def CreaingChars(self):
        self.Chars = {}
        try:
            with open("FONTS/FONT_CHARS.json") as file:
                Chars = json.load(file)
            for Char in Chars["Chars"]:
                self.Chars[str(Char[0])] = Char[1]
        except FileNotFoundError: pass

    def LoadFontFromTtf(self, Name, Size):
        return {0: "Ttf", 1: pg.font.Font(Name, Size)}

    def LoadFont(self, Name):
        FontFromXml = ReadXmlFile(f"{Name}")
        Texture = pg.image.load(f"{FontFromXml.attrib["texture"]}").convert_alpha()
        CharsList = FontFromXml.findall("Char")
        Chars = {0: "File"}
        for Char in CharsList:
            CharAttribs = Char.attrib
            Id = CharAttribs["id"]
            if Id in list(self.Chars.keys()): Id = self.Chars[Id]
            Id = int(Id)
            XAdv = 0
            if "xadvanced" in CharAttribs: XAdv = int(CharAttribs["xadvanced"])
            Chars[chr(Id)] = [Texture.subsurface(int(CharAttribs["x"]), int(CharAttribs["y"]), int(CharAttribs["width"]), int(CharAttribs["height"])), int(CharAttribs["xoffset"]), int(CharAttribs["yoffset"]), XAdv]
        return Chars
    
    def WriteFont(self, Font, Text, Color=None, Align=None):
        if self.Fonts[Font][0] == "File":
            W = H = 0
            OffsetX = 0
            OffsetY = 0
            for Letter in Text:
                Img = self.Fonts[Font][Letter]
                W += Img[0].get_width() + Img[1] + Img[3]
                OffsetX = Img[1]
                if Img[2] < 0 and abs(Img[2]) > OffsetY:
                    OffsetY = abs(Img[2])
                if H < Img[0].get_height() + Img[2]: H = Img[0].get_height() + Img[2]
            W -= OffsetX
            Surface = pg.Surface((W, H + OffsetY), flags=pg.SRCALPHA)
            X = 0
            for Letter in Text:
                Img = self.Fonts[Font][Letter]
                if X == 0: X -= Img[1]
                Surface.blit(Img[0], (X + Img[1], Img[2] + OffsetY))
                X += Img[0].get_width() + Img[1] + Img[3]
        elif Color != None:
            Surface = self.Fonts[Font][1].render(Text, 1, Color)
        else:
            raise AttributeError("Color is invalid")
        return (Surface, Align)
    
class App:
    def __init__(self, s, clock):
        self.s = s
        self.DrawSurf = pg.Surface(self.s.get_size(), flags=pg.SRCALPHA)
        self.clock = clock
        self.Fonts = Fonts(self.LoadFonts)
        self.PalleteColors = [RED, GREEN, BLUE, YELLOW, LIGHTBLUE, PINK, GRAY, ORANGE, DARKGREY, DARKRED, DARKVIOLET, DARKGREEN]
        self.PalleteIndex = 0
        self.PalleteTileSize = 40
        self.PalletePos = vec2(10, 10)
        self.Radius = 10
        self.CTRLPressed = False
        self.Eraser = False
        self.EPressed = False
        self.Pressed = False
        self.SaveWithHotKey = [pg.K_LALT, pg.K_LCTRL, pg.K_LSHIFT, pg.K_s]
        self.SaveWithTrans = False
        self.SaveTransPressed = False
        self.RMBPressed = False
        self.BgColor = "gray"
        self.StartRectPos = None
        self.RectsSurf = self.DrawSurf.copy()
        self.DrawFilled = False
        self.SpacePressed = False

    def LoadFonts(self, TtfFunc, FileFunc):
        return {"PP_Dialog": FileFunc("FONTS/PP_Dialog.xml")}

    def update(self):
        self.MousePos = vec2(*pg.mouse.get_pos())
        keys = pg.key.get_pressed()
        self.CTRLPressed = False
        SaveTransHotKeyPressed = all([keys[Key] for Key in self.SaveWithHotKey])
        if SaveTransHotKeyPressed and not self.SaveTransPressed: self.SaveTransPressed = True
        if not SaveTransHotKeyPressed and self.SaveTransPressed:
            self.SaveWithTrans = not self.SaveWithTrans
            self.SaveTransPressed = False
        if keys[pg.K_LCTRL]: self.CTRLPressed = True
        if keys[pg.K_e] and not self.EPressed: self.EPressed = True
        if not keys[pg.K_e] and self.EPressed:
            self.Eraser = not self.Eraser
            self.EPressed = False
        PalleteRect = pg.Rect(*self.PalletePos, len(self.PalleteColors) * self.PalleteTileSize, self.PalleteTileSize)
        Collide = PalleteRect.collidepoint(self.MousePos)
        if not Collide and pg.mouse.get_pressed()[0]: 
            Color = self.PalleteColors[self.PalleteIndex] if not self.Eraser else (0, 0, 0, 0)
            pg.draw.circle(self.DrawSurf, Color, self.MousePos, self.Radius)
            if self.Eraser: pg.draw.circle(self.RectsSurf, (0, 0, 0, 0), self.MousePos, self.Radius)
        elif Collide:
            if pg.mouse.get_pressed()[0] and not self.Pressed: self.Pressed = True
            if not pg.mouse.get_pressed()[0] and self.Pressed: 
                Diff = self.MousePos - self.PalletePos
                self.PalleteIndex = int(Diff.x // self.PalleteTileSize)
                self.Pressed = False
        if pg.mouse.get_pressed()[2] and not self.RMBPressed: self.RMBPressed = True
        if not pg.mouse.get_pressed()[2] and self.RMBPressed:
            if self.StartRectPos == None: self.StartRectPos = self.MousePos.copy()
            else:
                Pos, Size = self.GetRect()
                pg.draw.rect(self.DrawSurf, self.PalleteColors[self.PalleteIndex], (*Pos, *Size), 2 if not self.DrawFilled else 0)
                self.DrawFilled = False
                self.StartRectPos = None
            self.RMBPressed = False
        if keys[pg.K_SPACE] and not self.SpacePressed: self.SpacePressed = True
        if not keys[pg.K_SPACE] and self.SpacePressed: 
            self.DrawFilled = not self.DrawFilled
            self.SpacePressed = False

    def GetRect(self):
        Diff = self.MousePos - self.StartRectPos
        Pos = vec2()
        Size = vec2()
        if Diff.x < 0: 
            Pos.x = self.MousePos.x
        else: Pos.x = self.StartRectPos.x
        Size.x = abs(Diff.x)
        if Diff.y < 0: 
            Pos.y = self.MousePos.y
            Size.y = abs(Size.y)
        else: Pos.y = self.StartRectPos.y
        Size.y = abs(Diff.y)
        return Pos, Size

    def draw(self):
        self.s.fill(self.BgColor)
        self.RectsSurf.fill((0, 0, 0, 0))
        for Index, Color in enumerate(self.PalleteColors):
            pg.draw.rect(self.s, Color, (self.PalletePos.x + self.PalleteTileSize * Index, self.PalletePos.y, *[self.PalleteTileSize] * 2))
            if Index == self.PalleteIndex: pg.draw.rect(self.s, "black", (self.PalletePos.x + self.PalleteTileSize * Index, self.PalletePos.y, *[self.PalleteTileSize] * 2), 2)
        Offset = vec2(-10, 10)
        SizeWhat = "кисти" if not self.Eraser else "ластика"
        Rendered = self.Fonts.WriteFont("PP_Dialog", f"Размер {SizeWhat}: {self.Radius}")[0]
        self.s.blit(Rendered, (self.s.get_width() - Rendered.get_width() + Offset.x, Offset.y))
        Offset = vec2(-10, -10)
        Rendered = self.Fonts.WriteFont("PP_Dialog", f"Сохр. рис. с прозр. фоном: {self.SaveWithTrans}")[0]
        self.s.blit(Rendered, (self.s.get_width() - Rendered.get_width() + Offset.x, self.s.get_height() - Rendered.get_height() + Offset.y))
        if self.StartRectPos != None:
            Pos, Size = self.GetRect()
            pg.draw.rect(self.RectsSurf, self.PalleteColors[self.PalleteIndex], (*Pos, *Size), 2 if not self.DrawFilled else 0)
        self.s.blit(self.DrawSurf, vec2())
        self.s.blit(self.RectsSurf, vec2())

    def check_events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                if not self.SaveWithTrans: pg.image.save(self.DrawSurf, "БУТЫРКА!!!.png")
                else:
                    Surf = self.DrawSurf.copy()
                    Surf.fill(self.BgColor)
                    Surf.blit(self.DrawSurf, vec2())
                    pg.image.save(Surf, "БУТЫРКА!!!.png")
                sys.exit()
            if event.type == pg.MOUSEWHEEL: 
                if not self.CTRLPressed:
                    self.PalleteIndex += event.y
                    self.PalleteIndex = max(min(self.PalleteIndex, len(self.PalleteColors) - 1), 0)
                else: 
                    self.Radius += event.y
                    self.Radius = max(min(self.Radius, 4000), 1)

    def run(self):
        while True:
            self.dt = clock.tick() / 10
            self.update()
            self.draw()
            self.check_events()
            pg.display.update()

if __name__ == "__main__":
    app = App(s, clock)
    app.run()