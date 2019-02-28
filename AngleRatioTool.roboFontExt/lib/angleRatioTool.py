import mojo
import os
import AppKit
from mojo.events import installTool, EditingTool, BaseEventTool, setActiveEventTool
from mojo.drawingTools import *
from mojo.UI import UpdateCurrentGlyphView
from defconAppKit.windows.baseWindow import BaseWindowController
import math

#
#
#     A visualisation for RoboFont
#     Show the ratio between the length of incoming and outgoing sections of bcps and tangents.
#     Show the angle
#     Draw in active and inactive views so we can compare different glyphs
#     erik@letterror.com

angleRatioToolBundle = mojo.extensions.ExtensionBundle("AngleRatioTool")
toolbarIconPath = os.path.join(angleRatioToolBundle.resourcesPath(), "icon.pdf")
toolbarIcon = AppKit.NSImage.alloc().initWithContentsOfFile_(toolbarIconPath)

class RatioTool(EditingTool):
    balloonDistance = 100
    textAttributes = {
        AppKit.NSFontAttributeName : AppKit.NSFont.systemFontOfSize_(10),
        AppKit.NSForegroundColorAttributeName : AppKit.NSColor.whiteColor(),
    }
    aa = .6
    incomingColor = AppKit.NSColor.colorWithCalibratedRed_green_blue_alpha_(1,0,.5, aa)
    outgoingColor = AppKit.NSColor.colorWithCalibratedRed_green_blue_alpha_(.5,0,1, aa)
    _offcurveNames = ['offcurve', 'offCurve']     # RF1.8: offcurve, RF2.0 offCurve

    def setup(self):
        self._rin = None
        self._rout = None
        self.markerWidth = 12
        self.snapThreshold = .5

    def getToolbarTip(self):
        return 'Angle Ratio Tool'

    def getToolbarIcon(self):
        ## return the toolbar icon
        return toolbarIcon
    
    def drawInactive(self, viewScale, glyph=None, view=None):
        # also draw when the view is inactive so we can compare different windows
        self.draw(viewScale, RGlyph(glyph))
        
    def draw(self, viewScale, g=None):
        if g is None:
            g =  self.getGlyph()
        if g is not None:
            save()
            self.getRatio(g, viewScale)
            restore()
    
    def getRatio(self, g, viewScale):
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

                # if True:
                #     print('\npppt', pppt, "\t", pppt.type, "\t", pppt.smooth, pppt.index)
                #     print('ppt', ppt, "\t", ppt.type, "\t", ppt.smooth)
                #     print('p', p, "\t", p.type, "\t", p.smooth)
                #     print('npt', npt, "\t", npt.type, "\t", npt.smooth)
                #     print('nnpt', nnpt, "\t", nnpt.type, "\t", nnpt.smooth)
                
                #     print('-'*40)
                #     print("ppt.type in self._offcurveNames", ppt.type in self._offcurveNames, ppt.type)
                #     print("ppt.type==curve", ppt.type=="curve")
                #     print("p.smooth==True", p.smooth==True)
                #     print("p.type==line", p.type=="line")
                #     print("npt.type in self._offcurveNames", npt.type in self._offcurveNames)
                #     print('-'*40)
                
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

                if apt is not None and bpt is not None and cpt is not None:
                    rin = math.hypot(apt.x-bpt.x,apt.y-bpt.y)
                    rout = math.hypot(cpt.x-bpt.x,cpt.y-bpt.y)
                    r = rin / rout
                if r is not None:
                    # text bubble for the ratio
                    angle = math.atan2(apt.y-cpt.y,apt.x-cpt.x) + .5* math.pi
                    sbd = self.balloonDistance * viewScale * .25
                    mp = math.cos(angle) * self.markerWidth* viewScale , math.sin(angle) * self.markerWidth* viewScale 
                    tp = bpt.x + math.cos(angle)*sbd*2, bpt.y + math.sin(angle)*sbd*2
                    self.getNSView()._drawTextAtPoint(
                        "ratio %3.4f"%(r ),
                        self.textAttributes,
                        tp,
                        yOffset=0,
                        drawBackground=True,
                        backgroundColor=self.outgoingColor)
                    tp = bpt.x - math.cos(angle)*sbd*2, bpt.y - math.sin(angle)*sbd*2
                    self.getNSView()._drawTextAtPoint(
                        "angle %3.4f"%(math.degrees(angle)%180 ),
                        self.textAttributes,
                        tp,
                        yOffset=0,
                        drawBackground=True,
                        backgroundColor=self.incomingColor)
                    p = bpt.x + bpt.x - apt.x, bpt.y + bpt.y - apt.y
                    q = bpt.x + bpt.x - cpt.x, bpt.y + bpt.y - cpt.y
                    dab = math.hypot(bpt.x - apt.x, bpt.y - apt.y)
                    dcb = math.hypot(bpt.x - cpt.x, bpt.y - cpt.y)
                    snap = False
                    m = 3
                    if max(dab, dcb) - min(dab, dcb) < self.snapThreshold:
                        snap = True
                        m = 5
                    stroke(1,0,.5)
                    strokeWidth(.75*viewScale)
                    line((p[0]+mp[0], p[1]+mp[1]), (p[0]-mp[0], p[1]-mp[1]))
                    line((q[0]+mp[0], q[1]+mp[1]), (q[0]-mp[0], q[1]-mp[1]))
                    fill(1,0,.5)
                    self.dot(p, viewScale, m)
                    self.dot(q, viewScale, m)
                    self._rin = rin
                    self._rout = rout
    
    def dot(self, pos, viewScale, m=3):
        save()
        stroke(None)
        m = m * viewScale
        oval(pos[0]-m, pos[1]-m, 2*m, 2*m)
        restore()

    def mouseDown(self, point, event):
        pass

    def mouseUp(self, xx):
        self._rin = None
        self._rout = None
    
    # def keyDown(self, event):
    #     letter = event.characters()
    #     mods = self.getModifiers()
    #     cmd = mods['commandDown'] > 0
    #     option = mods['optionDown'] > 0
            
p = RatioTool()
installTool(p)

