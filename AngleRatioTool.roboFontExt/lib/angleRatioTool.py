import os
import math
import AppKit
from mojo.extensions import ExtensionBundle
from mojo.events import installTool, EditingTool, BaseEventTool, setActiveEventTool
from mojo.drawingTools import *
from mojo.UI import UpdateCurrentGlyphView
from defconAppKit.windows.baseWindow import BaseWindowController

#
#
#     A visualisation for RoboFont 4
#     Show the ratio between the length of incoming and outgoing sections of bcps and tangents.
#     Show the angle
#     Draw in active and inactive views so we can compare different glyphs
#     erik@letterror.com

angleRatioToolBundle = ExtensionBundle("AngleRatioTool")
toolbarIconPath = os.path.join(angleRatioToolBundle.resourcesPath(), "icon.pdf")
toolbarIcon = AppKit.NSImage.alloc().initWithContentsOfFile_(toolbarIconPath)


class RatioTool(EditingTool):

    incomingColor = (1,0,.5, .6)
    outgoingColor = (.5,0,1, .6)
    _offcurveNames = ['offcurve']     # RF1.8: offcurve, RF2.0 offCurve
    balloonDistance = 20

    def setup(self):
        self._rin = None
        self._rout = None
        self.markerWidth = 12
        self.snapThreshold = .5
        
        drawingLayer = self.extensionContainer("com.letterror.angleRatioTool")

        self.incomingLayer = drawingLayer.appendPathSublayer(
            fillColor=None,
            strokeColor=self.incomingColor,
            strokeWidth=-1
        )

        self.outgoingLayer = drawingLayer.appendPathSublayer(
            fillColor=None,
            strokeColor=self.outgoingColor,
            strokeWidth=-1
        )

        self.captionTextLayer = drawingLayer.appendTextLineSublayer(
           #position=(0, 0),
           #size=(400, 100),
           backgroundColor=self.incomingColor,
           text="",
           fillColor=(1, 1, 1, 1),
           horizontalAlignment="center"
        )

        # self.outgoingTextLayer = drawingLayer.appendTextLineSublayer(
        #    position=(0, 0),
        #    size=(20, 10),
        #    backgroundColor=self.outgoingColor,
        #    text="Ratio",
        #    fillColor=(1, 1, 1, 1),
        #    horizontalAlignment="center"
        # )

        self.incomingLayer.setVisible(True)
        self.outgoingLayer.setVisible(True)
        self.captionTextLayer.setVisible(True)
        #self.outgoingTextLayer.setVisible(True)

    def getToolbarTip(self):
        return 'Angle Ratio Tool'

    def getToolbarIcon(self):
        ## return the toolbar icon
        return toolbarIcon
    
    # def drawInactive(self, glyph=None, view=None):
    #     # also draw when the view is inactive so we can compare different windows
    #     self.draw(RGlyph(glyph))
        
    # def draw(self, g=None):
    #     if g is None:
    #         g =  self.getGlyph()
    #     if g is not None:
    #         self.getRatio(g)
    
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

                captionText = ""
                if apt is not None and bpt is not None and cpt is not None:
                    rin = math.hypot(apt.x-bpt.x,apt.y-bpt.y)
                    rout = math.hypot(cpt.x-bpt.x,cpt.y-bpt.y)
                    r = rin / rout
                if r is not None:
                    # text bubble for the ratio
                    angle = math.atan2(apt.y-cpt.y,apt.x-cpt.x) + .5* math.pi
                    sbd = self.balloonDistance *  .25
                    mp = math.cos(angle) * self.markerWidth , math.sin(angle) * self.markerWidth 
                    
                    tp = bpt.x + math.cos(angle)*sbd*2, bpt.y + math.sin(angle)*sbd*2
                    if math.isclose(r,1,abs_tol=0.001):
                        captionText = "snap!"
                    else:
                        captionText = f'ratio: {r:3.3f}'
                    tp = bpt.x - math.cos(angle)*sbd*2, bpt.y - math.sin(angle)*sbd*2
                    captionText += "\nangle %3.4f"%(math.degrees(angle)%180 )
                    self.caption(tp, captionText)

                    p = bpt.x + bpt.x - apt.x, bpt.y + bpt.y - apt.y
                    q = bpt.x + bpt.x - cpt.x, bpt.y + bpt.y - cpt.y
                    dab = math.hypot(bpt.x - apt.x, bpt.y - apt.y)
                    dcb = math.hypot(bpt.x - cpt.x, bpt.y - cpt.y)
                    snap = False
                    m = 10
                    if max(dab, dcb) - min(dab, dcb) < self.snapThreshold:
                        snap = True
                        m = 20
                    #stroke(1,0,.5)
                    #strokeWidth(.75)
                    #line((p[0]+mp[0], p[1]+mp[1]), (p[0]-mp[0], p[1]-mp[1]))
                    #line((q[0]+mp[0], q[1]+mp[1]), (q[0]-mp[0], q[1]-mp[1]))
                    #fill(1,0,.5)
                    self.incomingDot(q, m)
                    self.outgoingDot(p, m)
                    self._rin = rin
                    self._rout = rout
    
    def caption(self, point, text):
        captionLayer = self.captionTextLayer.appendTextLineSublayer(
           position=point,
           size=(20, 20),
           pointSize=20,
           backgroundColor=self.incomingColor,
           text=f"{text}",
           fillColor=(1, 1, 1, 1),
           horizontalAlignment="center"
        )

    def outgoingDot(self, pos, m=200):
        dotLayer = self.outgoingLayer.appendOvalSublayer(
            position=(pos[0]-.5*m, pos[1]-.5*m),
            size=(m,m),
            fillColor=self.outgoingColor,
            strokeColor=None,
        )

    def incomingDot(self, pos, m=200):
        dotLayer = self.incomingLayer.appendOvalSublayer(
            position=(pos[0]-.5*m, pos[1]-.5*m),
            size=(m,m),
            fillColor=self.incomingColor,
            strokeColor=None,
        )

    def update(self):
        self.incomingLayer.clearSublayers()
        self.outgoingLayer.clearSublayers()
        self.captionTextLayer.clearSublayers()
        g = CurrentGlyph()
        self.getRatio(g)
        
    def mouseDragged(self, point=None, delta=None):
        self.update()

    def mouseDown(self, point, event):
        self.update()

    def mouseUp(self, xx):
        self._rin = None
        self._rout = None
    
    def keyDown(self, event):
        self.update()
            
p = RatioTool()
installTool(p)

print('installed', p)