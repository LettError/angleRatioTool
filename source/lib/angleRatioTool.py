import os
import math
import AppKit
from mojo.extensions import ExtensionBundle
from mojo.events import installTool, EditingTool, addObserver, removeObserver
from mojo.drawingTools import *
from mojo.UI import UpdateCurrentGlyphView, getDefault
import merz
from merz.tools.drawingTools import NSImageDrawingTools

#     A visualisation for RoboFont 4 XX
#     Show the ratio between the length of outgoing and incoming sections of bcps and tangents.
#     Show the angle
#     Draw in active and inactive views so we can compare different glyphs
#     erik@letterror.com

angleRatioToolBundle = ExtensionBundle("AngleRatioTool")
toolbarIconPath = os.path.join(angleRatioToolBundle.resourcesFolder, "icon.pdf")
toolbarIcon = AppKit.NSImage.alloc().initWithContentsOfFile_(toolbarIconPath)





def dotSymbolFactory(
        size,
        color,
        strokeColor,
        strokeWidth=0,
        ):
    # create a image draw bot 
    bot = NSImageDrawingTools((size, size))

    bot.fill(None)
    if not color == None:
        bot.fill(*color)
    bot.stroke(None)
    if not strokeColor == None:
        bot.stroke(*strokeColor)
    bot.strokeWidth(strokeWidth)
    # bot.translate(width / 2 + 0.25, height / 2 + 0.25)
    bot.oval(strokeWidth/2,strokeWidth/2,size-strokeWidth,size-strokeWidth)
    # return the image
    return bot.getImage()

merz.SymbolImageVendor.registerImageFactory("angleRatio.dot", dotSymbolFactory)

def lineSymbolFactory(
        size,
        strokeColor,
        strokeWidth=2,
        ):
    # create a image draw bot 
    bot = NSImageDrawingTools((size, size))

    bot.fill(None)
    bot.stroke(None)
    if not strokeColor == None:
        bot.stroke(*strokeColor)
    bot.strokeWidth(strokeWidth)
    bot.line((0,size/2),(size,size/2))
    # return the image
    return bot.getImage()

merz.SymbolImageVendor.registerImageFactory("angleRatio.line", lineSymbolFactory)


class RatioTool(EditingTool):

    incomingColor = ( 1, 0, .5, 0.8)
    outgoingColor = (.5, 0,  1, 0.8)
    _offcurveNames = ['offcurve']     # RF1.8: offcurve, RF2.0 offCurve
    balloonDistance = 20

    def setup(self):
        self._rin = None
        self._rout = None
        self.markerWidth = 12
        self.snapThreshold = .5

        self.dot_size = int(getDefault('glyphViewOffCurvePointsSize')) * 3
        self.snap_size = self.dot_size + 6
        self.font_size = int(getDefault('textFontSize')) + 2

        foregroundLayer = self.extensionContainer(
            identifier="com.letterror.angleRatioTool.fg", 
            location="foreground", 
            clear=True
            )

        self.outgoingLayer = foregroundLayer.appendPathSublayer(
            fillColor=None,
            strokeColor=self.outgoingColor
        )

        self.incomingLayer = foregroundLayer.appendPathSublayer(
            fillColor=None,
            strokeColor=self.incomingColor
        )

        self.captionTextLayer = foregroundLayer.appendTextLineSublayer(
           #position=(0, 0),
           #size=(400, 100),
           backgroundColor=self.outgoingColor,
           text="",
           fillColor=(1, 1, 1, 1),
           horizontalAlignment="center"
        )

        self.outgoingLayer.setVisible(True)
        self.incomingLayer.setVisible(True)
        self.captionTextLayer.setVisible(True)

        addObserver(self, "didUndo", "didUndo")

        self.update()

    def getToolbarTip(self):
        return 'Angle Ratio Tool'

    def getToolbarIcon(self):
        ## return the toolbar icon
        return toolbarIcon
    
    def getRatio(self, g):
        # get the in/out ratio of selected smooth points
        for c in g.contours:
            if c is None: continue
            l = len(c.points)
            for i, p in enumerate(c.points):
                # we're dragging a bcp so we need the previous and the one before that
                # or, the next and the one after that.
                if not p.selected: continue
                if c is None:
                    continue

                pppt = c.points[i-2]
                ppt = c.points[i-1]
                npt = c.points[(i+1)%l]
                nnpt = c.points[(i+2)%l]

                apt = bpt = cpt = r = rin = rout = None
                
                if p.type in self._offcurveNames and npt.type=="curve" and npt.smooth==True and nnpt.type in self._offcurveNames:
                    #print('aa 1')
                    apt = p
                    bpt = npt
                    cpt = nnpt
                elif ppt.type == "curve" and p.type in self._offcurveNames and npt.type in self._offcurveNames and ppt.smooth==True:
                    #print('aa 2')
                    apt = pppt
                    bpt = ppt
                    cpt = p
                elif ppt.type in self._offcurveNames and p.smooth==True and p.type=="curve" and npt.type in self._offcurveNames:
                    #print('aa 3')
                    apt = ppt
                    bpt = p
                    cpt = npt
                elif ppt.type in self._offcurveNames and p.smooth==True and p.type=="curve" and npt.type == "line":
                    #print('aa 4')
                    apt = ppt
                    bpt = p
                    cpt = npt
                elif pppt.type in self._offcurveNames and ppt.type=="curve" and p.smooth==True and p.type=="line" and npt.type in self._offcurveNames:
                    #print('aa 5')
                    apt = ppt
                    bpt = p
                    cpt = npt
                elif ppt.type in["curve", "line"] and p.smooth==True and p.type=="line" and npt.type in self._offcurveNames:
                    #print('aa 6')
                    apt = ppt
                    bpt = p
                    cpt = npt
                elif ppt.type in self._offcurveNames and p.type in self._offcurveNames and npt.type == "curve"  and npt.smooth == True:
                    # dragging an offcurve from a tangent
                    #print('aa 7', npt.smooth)
                    apt = p
                    bpt = npt
                    cpt = nnpt
                elif p.type in self._offcurveNames and npt.type in self._offcurveNames and ppt.smooth==True:
                    # dragging an offcurve from a tangent, other direction
                    #print('aa 8')
                    apt = pppt
                    bpt = ppt
                    cpt = p

                ratioText = ""
                angleText = ""
                if apt is not None and bpt is not None and cpt is not None:
                    rin = math.hypot(apt.x-bpt.x,apt.y-bpt.y)
                    rout = math.hypot(cpt.x-bpt.x,cpt.y-bpt.y)
                    r = rin / rout
                if r is not None:
                    # text bubbles
                    angle = math.atan2(apt.y-cpt.y,apt.x-cpt.x) + .5* math.pi
                    sbd = self.balloonDistance * 3
                    mp = math.cos(angle) * self.markerWidth , math.sin(angle) * self.markerWidth 
                    
                    if math.isclose(r,1,abs_tol=0.001):
                        ratioText = "snap!"
                    else:
                        ratioText = f"ratio: {round(r, 2)}"

                    angle_degrees = math.degrees(angle)%180

                    angleText = f"angle: {round(angle_degrees, 2)}"

                    cap_dist = 1.3 # distance of caption from on-curve

                    tp1 = math.cos(angle)*sbd*cap_dist, math.sin(angle)*sbd*cap_dist
                    tp2 = -math.cos(angle)*sbd*cap_dist, -math.sin(angle)*sbd*cap_dist

                    self.caption((bpt.x, bpt.y), tp1, tp2, ratioText, angleText)

                    p = bpt.x + bpt.x - apt.x, bpt.y + bpt.y - apt.y
                    q = bpt.x + bpt.x - cpt.x, bpt.y + bpt.y - cpt.y
                    dab = math.hypot(bpt.x - apt.x, bpt.y - apt.y)
                    dcb = math.hypot(bpt.x - cpt.x, bpt.y - cpt.y)
                    snap = False
                    m = self.dot_size
                    if max(dab, dcb) - min(dab, dcb) < self.snapThreshold:
                        snap = True
                        m = self.snap_size

                    self.outgoingShape(q, m, angle_degrees)
                    self.incomingShape(p, m, angle_degrees)
                    self._rin = rin
                    self._rout = rout
    
    def caption(self, point, offset1, offset2, text1, text2):
        pd_x = 10
        pd_y = 2
        ps = self.font_size
        cr = ps

        ratioCaptionLayer = self.captionTextLayer.appendTextLineSublayer(
           position=point,
           offset=offset1,
           size=(20, 20),
           pointSize=ps,
           backgroundColor=None,
           text=f"{text1}",
           fillColor=self.outgoingColor,
           horizontalAlignment="center",
           verticalAlignment="bottom",
           weight='bold',
           figureStyle='tabular',
           padding=(pd_x, pd_y),
           cornerRadius = cr
        )
        angleCaptionLayer = self.captionTextLayer.appendTextLineSublayer(
           position=point,
           offset=offset2,
           size=(20, 20),
           pointSize=ps,
           backgroundColor=None,
           text=f"{text2}",
           fillColor=self.incomingColor,
           horizontalAlignment="center",
           verticalAlignment="bottom",
           weight='bold',
           figureStyle='tabular',
           padding=(pd_x, pd_y),
           cornerRadius = cr
        )

    def incomingShape(self, pos, m=200, angle=0):
        fc = self.incomingColor
        sc = None
        sw = 0
        lsw = 1
        lsc = self.incomingColor
        if m == self.snap_size:
            fc = None
            sc = self.incomingColor
            sw = 1
            lsw = 0
            lsc = None

        # using symbols so the dot doesn't scale upon zoom
        dotLayer = self.incomingLayer.appendSymbolSublayer(
                position        = (pos[0], pos[1]),
                imageSettings   = dict(
                                    name        = "angleRatio.dot",
                                    size        = m+sw, 
                                    color       = fc,
                                    strokeColor = sc,
                                    strokeWidth = sw 
                                    )
                )
        lineLayer = self.outgoingLayer.appendSymbolSublayer(
                position        = (pos[0], pos[1]),
                rotation        = angle,
                imageSettings   = dict(
                                    name        = "angleRatio.line",
                                    size        = m + 20, 
                                    strokeColor = lsc,
                                    strokeWidth = lsw 
                                    )
                )
        

    def outgoingShape(self, pos, m=200, angle=0):
        fc = self.outgoingColor
        sc = None
        sw = 0
        lsw = 1
        lsc = self.outgoingColor
        if m == self.snap_size:
            fc = None
            sc = self.outgoingColor
            sw = 1
            lsw = 0
            lsc = None

        # using symbols so the dot doesn't scale upon zoom
        dotLayer = self.outgoingLayer.appendSymbolSublayer(
                position        = (pos[0], pos[1]),
                imageSettings   = dict(
                                    name        = "angleRatio.dot",
                                    size        = m+sw, 
                                    color       = fc,
                                    strokeColor = sc,
                                    strokeWidth = sw 
                                    )
                )
        lineLayer = self.outgoingLayer.appendSymbolSublayer(
                position        = (pos[0], pos[1]),
                rotation        = angle,
                imageSettings   = dict(
                                    name        = "angleRatio.line",
                                    size        = m + 20, 
                                    strokeColor = lsc,
                                    strokeWidth = lsw 
                                    )
                )

    def update(self):
        self.clearAll()
        g = CurrentGlyph()
        self.getRatio(g)
        
    def mouseDragged(self, point=None, delta=None):
        self.update()

    def mouseDown(self, point, event):
        self.update()

    def mouseUp(self, xx):
        self._rin = None
        self._rout = None
        self.update()
    
    def keyDown(self, event):
        self.update()

    def didUndo(self, notification):
        self.update()

    def becomeInactive(self):
        self.clearAll()
        removeObserver(self, "didUndo")

    def clearAll(self):
        self.outgoingLayer.clearSublayers()
        self.incomingLayer.clearSublayers()
        self.captionTextLayer.clearSublayers()
            
p = RatioTool()
installTool(p)

print('installed', p)
