#!/bin/env python26

"""
Rough Circle Quilt Designer Demo
doug
06-25-11
"""
import sys, os
import math
import struct

from PyQt4.QtOpenGL import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from path import path as Path

from random import    uniform, randint, choice, seed

try:
    from PIL import Image
except ImportError:
    import Image # linux

try:
    from OpenGL import GL
except ImportError:
    print "No GL"
    sys.exit(-1)
    app = QApplication(sys.argv)

from OpenGL.GL import *
from OpenGL.GLU import *

# ------------------------------------------------------------------------------
# Params

MINCOUNT = 3
MAXCOUNT = 12

MINSIZE = 2
MAXSIZE = 8

STYLENAMES = ("Square","Circle")


# ------------------------------------------------------------------------------
# Params

TilesDir = Path("./tiles")
TilePngPaths = TilesDir.files("tile-?.png")

# ------------------------------------------------------------------------------

# Start app

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create('plastique')) #'cleanlooks'))


# ------------------------------------------------------------------------------
#
class ToolEnv(object):
    """
    Global data
    Attributes:
        platform    one of "windows", "linux" or "mac"
        iconPath    path to all the icon PNGs
        appPath     path to the application
    Methods:
        getIcon()   return QIcon for the named icon
    """
    
    def __init__(self):
        self.platform = "linux"
        if sys.platform.lower().startswith("win"):
            self.platform = "windows"
        elif sys.platform.lower().startswith("dar"):
            self.platform = "mac"
        
        #myIcons = dict( [(path.namebase,QIcon(path)) for path in Path(r'C:\Documents and Settings\doug\My Documents\images\icons').files('*.png')])
        self.appPath = Path(__file__).abspath().dirname()
        self.iconPath = self.appPath / r"images\icons"


    def getIcon(self,name):
        """
        Return a QIcon given a name of a PNG icon in the app's resources
        or blank icon if not found.
        """
        p = self.iconPath / ("%s.png" % name)
        if p.exists():
            icon = QIcon(str(p))
            icon.isDummy = False
        else:
            icon = QIcon()
            icon.isDummy = True
        return icon

if __name__ == "__main__":
    E = ToolEnv()

# ------------------------------------------------------------------------------
#

class DragDropLabel(QLabel):
    """
    A label that can have text, items or images dragged into or out of it.
    """
    
    def __init__(self,parent=None,dragText=None):
        super(DragDropLabel,self).__init__(parent)
        self.dragText = dragText
        self.dragPix = None
        self.setAcceptDrops(True)
        self.maxPixmapSize = QSize(640,480)

    def mousePressEvent(self, event):
        if event.button() in (Qt.LeftButton, Qt.MiddleButton):
            # Start a DRAG
            data = QMimeData()
            data.setText(QString(self.dragText))
            drag = QDrag(self)
            if self.dragPix:
                drag.setPixmap(self.dragPix)
            drag.setMimeData(data)
            drag.exec_()
        elif event.button() in (Qt.RightButton,):
            # Context menu
            menu = QMenu(self)
            for name, icon in [  ("Copy", "Page-Copy"), ("Cut","Cut"), ("Paste","Page-Paste"), ("Clear","Bin"), ]:
                action = menu.addAction(E.getIcon(icon),name)
                self.connect(action, SIGNAL("triggered()"), lambda s=self,n=name: s.contextMenuCB(n))
            menu.exec_(event.globalPos())
            event.accept()

    def contextMenuCB(self,name):
        clipboard = E.clipboard.clipboard
        if name == "Copy":
            clipboard.setText(self.text())
        elif name == "Cut":
            clipboard.setText(self.text())
            self.clear()
        elif name == "Paste":
            self.setText(clipboard.text())
        elif name == "Clear":
            self.clear()

    def dragEnterEvent(self, event):
        mimeData = event.mimeData()
        if (    mimeData.hasImage() or 
                mimeData.hasHtml() or 
                mimeData.hasText() or 
                mimeData.hasUrls() ):
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        event.acceptProposedAction()

    def imagePath(self,text):
        p = Path(str(text))
        if p.exists() and p.ext.lower() in (".jpg",".tif",".png",):
            pic = QPixmap(str(p))
            if self.maxPixmapSize:
                return pic.scaled(self.maxPixmapSize, aspectRatioMode=Qt.KeepAspectRatio, transformMode=Qt.SmoothTransformation)
            else:
                return pic
        else:
            return None

    def dropEvent(self, event):
        mimeData = event.mimeData()
        if mimeData.hasImage():
            self.setPixmap(QPixmap(mimeData.imageData()))
            self.dragText = "(image)"
        elif mimeData.hasHtml():
            self.setText(mimeData.html())
            self.setTextFormat(Qt.RichText)
            self.dragText = self.text
        elif mimeData.hasText():
            t = mimeData.text()
            self.dragText = t
            p = self.imagePath(t)
            if p:
                self.setPixmap(p)
            else:
                self.setText(t)
        elif mimeData.hasUrls():
            for u in mimeData.urls():
                t = u.toString()
                self.dragText = t
                p = self.imagePath(t)
                if p:
                    self.setPixmap(p)
                    break
            if not p:
                self.setText('\n'.join([str(u.toString()) for u in mimeData.urls()]))
                self.dragText = self.text()

    def loadImage(self,fileName):
        self.currentPixmap = QPixmap(fileName)
        self.setPixmap(self.currentPixmap)
        #self.autofitImage()

    def autofitImage(self):
        scaledSize = QSize(self.currentPixmap.size())
        scaledSize.scale(QSize(640, 640), Qt.KeepAspectRatio)
        self.setPixmap(self.currentPixmap.scaled( scaledSize, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.polishCB()

    def polishCB(self,*args):
        self.updateImage(True)

    def updateImage(self,polish=False):
        transformType = Qt.SmoothTransformation if polish else Qt.FastTransformation
        if not self.currentPixmap: return
        origWidth  = self.currentPixmap.size().width()
        origHeight = self.currentPixmap.size().height()
        scaledSize = self.imageScale * QSize(self.currentPixmap.size())
        #scaledSize.scale(QSize(640, 640), Qt.KeepAspectRatio)
        croppedHeight = int(640.0 * float(origHeight) / float(origWidth))
        scaledPixmap = self.currentPixmap.scaled( scaledSize, Qt.KeepAspectRatio, transformType)
        u, v = self.pictureOffset.x(), self.pictureOffset.y()
        croppedPixmap = scaledPixmap.copy(u, v, 640, croppedHeight)
        self.image.setPixmap(croppedPixmap)

# ------------------------------------------------------------------------------
#

class QuiltW(QGLWidget):

    def __init__(self,parent,tiles):
        QGLWidget.__init__(self,parent)
        self.setAcceptDrops(True)
        self.x  = 0.0
        self.y  = 0.0
        self.z  = -30.0
        self.tiles = tiles
        self.numTiles = len(self.tiles)
        self.counts = (MINCOUNT,MINCOUNT)
        self.tileSize = float(MAXSIZE)
        avg = 1.0 / self.numTiles
        self.quantities = dict( [ (i,avg) for i in range(self.numTiles)] )
        self.styles = dict( [ (i,STYLENAMES[i%2]) for i in range(self.numTiles)] )
        self.textures = None
        self.probability = dict( [ (i,avg) for i in range(self.numTiles)] ) # probability of texture number i
        self.numCirclePts = 20
        self.circleFraction = 0.75
        self.randomSeed = 1
        self.tileMap = dict()

    def setZ(self,z): self.z = z

    def initializeGL(self):
        glClearColor(0.012, 0.012, 0.012, 0.0)
        glClear(GL_COLOR_BUFFER_BIT)
        glEnable(GL_TEXTURE_2D)

    def resizeGL(self,w,h):
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(60., w / float(h), 1, 10000.)
        glMatrixMode(GL_MODELVIEW)

    def paintGL(self):

        if self.textures == None: # first run, set up textures
            self.textures = list()
            for i,tp in enumerate(self.tiles):
                self.textures.append( self.bindTexture(QPixmap(str(tp))) )
            self.updateTiles()
        
        glClear(GL_COLOR_BUFFER_BIT)
        glLoadIdentity()
        glTranslatef(self.x, self.y, self.z)
        self.drawTiles()
        self.hud()

    def hud(self):
        status = '%s" x %s"' % (self.tileSize*self.counts[0],self.tileSize*self.counts[1],)
        glColor4f(0.0, 0.0, 0.0, 0.4)
        self.renderText(10+2,30+2, QString(status), QFont("helvetica", 16, 120.0))
        glColor4f(1.0, 1.0, 1.0, 0.4)
        self.renderText(10+0,30+0, QString(status), QFont("helvetica", 16, 120.0))

    def wheelEvent(self, event):
        dz = 0.05 * 10 * (event.delta() / 120.0)
        self.z += dz
        self.updateCamera()

    def updateCamera(self):
        self.updateGL()
        self.emit(SIGNAL("viewChanged()"))

    def mousePressEvent(self, event):
        self.lastPos = QPoint(event.pos())
        if event.modifiers() & Qt.AltModifier:
            tileId = self.drawTiles(event)
            if tileId:
                print "SELECTED",(tileId[0],tileId[1]),(tileId[2],tileId[3]),tileId[4]
            self.drawTiles()

    def mouseMoveEvent(self, event):
        dx = event.x() - self.lastPos.x()
        dy = event.y() - self.lastPos.y()
        if event.buttons() & Qt.LeftButton:
            self.x += dx/25.0
            self.y -= dy/25.0
        elif event.buttons() & Qt.RightButton:
            self.z += 2 * dx/15.0
        self.lastPos = QPoint(event.pos())
        self.updateCamera()
    
    def dragEnterEvent(self, event):
        mimeData = event.mimeData()
        event.acceptProposedAction()
        if (    mimeData.hasImage() or 
                mimeData.hasHtml() or 
                mimeData.hasText() or 
                mimeData.hasUrls() ):
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        event.acceptProposedAction()

    def dropEvent(self,event):
        try:
            tileNum = int(event.mimeData().text())
        except:
            return
        
        key = self.drawTiles(event)
        if key:
            self.tileMap[key] = tileNum
        self.drawTiles()
        self.updateGL()
        self.drawTiles()
        self.updateGL()
        

    def setSeed(self,s):
        self.randomSeed = s
        self.updateTiles()

    def setCounts(self, h,v):
        self.counts = (h,v)
        self.updateTiles()
        
    def setTileSize(self, s):
        self.tileSize = s
        self.updateTiles()

    def setCircleFraction(self, s):
        self.circleFraction = s
        self.updateTiles()
        
    def setQuantity(self, tileNum, fraction):
        self.quantities[tileNum] = fraction
        self.updateTiles()
        
    def setStyle(self, tileNum, style):
        self.styles[tileNum] = str(style)
        self.updateTiles()
     
    def updateTiles(self,randomize=False):
        # Build the tileMap
        if not self.tileMap:
            randomize = True
        
        #if len(self.styles.keys()) < self.numTiles: 
        #    print self.styles
        #    return
    
        # There are N x N squares, each square has four smaller ones
        # with four quarter circles.
        # A set of four square texture choices and
        # four Circle texture choices is needed
        # "Fractions" is the weight average of how many we want
        # of each texture, indexed by which type.
        
        # First, get the squares and the circles as lists of indices
        self.styleIndex = dict( [ (s,list()) for s in STYLENAMES ] )
        for i in range(self.numTiles):
            self.styleIndex[ self.styles[i] ].append(i)
        
        # Make a large pool of choices based on weightings
        POOLSIZE = 30
        pool = dict()
        # If either list is empty, it's an error
        self.probability = dict()
        for style in STYLENAMES:
            if len(self.styleIndex[style]) < 1:
                QMessageBox.critical(None, "Styles",
                            "Program error, cannot have zero style '%s'" % style,
                            QMessageBox.Ok | QMessageBox.Default,
                            QMessageBox.NoButton)
                return

            totalPerStyle = sum([ self.quantities[i] for i in self.styleIndex[style] ])
        
            pool[style] = list()
            for i in self.styleIndex[style]:
                self.probability[i] = self.quantities[i] / totalPerStyle
            
                pool[style].extend([i] * (POOLSIZE * int(self.probability[i])))
                #print pool[style]

        # We now have a probability for each texture based on its style
        if randomize == True:
            seed(self.randomSeed)
            for xi in range(self.counts[0]):
                for yi in range(self.counts[1]):
                    for subX in (0, 1):
                        for subY in (0, 1):
                            for style in STYLENAMES:
                                key = (xi,yi,subX,subY,style)
                                texIndex = randint(0,self.numTiles-1)
                                self.tileMap[key] = texIndex
        
        self.updateGL()

    def drawTiles(self,selectEvent=None):
        """
        If select is a mousePress event, return the tuple 
            (xi,yi,subX,subY,styleString)
        where:
            (xi,yi)       the tile
            (subX,subY)   the quadrant subtile
            styleString   either "Square" or "Circle"
        """
        
        # Picking
        if selectEvent != None:
            pos = QPoint(selectEvent.pos())
            selX = pos.x()
            selY = self.size().height() - pos.y()
            selectMap = dict()
            glDisable(GL_TEXTURE_2D)
        else:
            glEnable(GL_TEXTURE_2D)
        
        i = 0
        for xi in range(self.counts[0]):
            for yi in range(self.counts[1]):
                selColR = yi * 16 + xi # limited to 16 x 16 tiles
                
                glPushMatrix()
                
                glTranslatef(
                    (float(xi)-self.counts[0]/2.0)*self.tileSize,
                    (float(yi)-self.counts[1]/2.0)*self.tileSize,
                    0.0)
                glScalef( self.tileSize, self.tileSize, 1.0)
                
                uv = self.tileSize / MAXSIZE / 2
                
                # Now we loop thru four sub squares, and four quarter circles
                
                for subX in (0, 1):
                    scaleX = (-1.0,1.0)[subX]
                    for subY in (0, 1):
                        scaleY = (-1.0,1.0)[subY]
                        selColG = subX + subY * 16
                        
                        glPushMatrix()
                        glTranslatef(subX/2,subY/2,0.0)
                        glScalef( 0.5*scaleX, 0.5*scaleY, 1.0)
                        
                        # The SQUARE (less circle)
                        key = (xi,yi,subX,subY,'Square')
                        texIndex = self.tileMap.get(key,0)
                        
                        if selectEvent != None:
                            glColor3ub(selColR, selColG, 0)
                            selectMap[ (selColR, selColG, 0) ] = key
                            glBindTexture(GL_TEXTURE_2D, 0)
                        else:
                            if texIndex == -1:
                                glBindTexture(GL_TEXTURE_2D, 0)
                            else:
                                glBindTexture(GL_TEXTURE_2D, self.textures[texIndex])
                
                        gap = 1.001
                        glBegin(GL_TRIANGLE_FAN)
                        glTexCoord2f(uv, uv); glVertex3f(1.0, 1.0,  0.0)
                        glTexCoord2f(0, uv);  glVertex3f(0.0, 1.0,  0.0)
                        for i in range(self.numCirclePts):
                            ang = math.pi/2 * (1.0 - float(i) / float(self.numCirclePts-1))
                            ca, sa = math.cos(ang), math.sin(ang)
                            x, y = ca*gap*self.circleFraction,    sa*gap*self.circleFraction
                            glTexCoord2f(x*uv, y*uv); glVertex3f(x, y,  0.0)
                        glTexCoord2f(uv, 0);  glVertex3f(1.0, 0.0,  0.0)
                        glEnd()
                        
                        # The CIRCLE
                        key = (xi,yi,subX,subY,'Circle')
                        texIndex = self.tileMap.get(key,-1)
                        
                        if selectEvent != None:
                            glColor3ub(selColR, selColG, 128)
                            selectMap[ (selColR, selColG, 128) ] = (xi,yi,subX,subY,'Circle')
                            glBindTexture(GL_TEXTURE_2D, 0)
                        else:
                            if texIndex == -1:
                                glBindTexture(GL_TEXTURE_2D, 0)
                            else:
                                glBindTexture(GL_TEXTURE_2D, self.textures[texIndex])
                
                        glBegin(GL_TRIANGLE_FAN)
                        glTexCoord2f(0.0, 0.0); glVertex3f(0.0, 0.0,  0.0)
                        for i in range(self.numCirclePts):
                            ang = math.pi/2 * float(i) / float(self.numCirclePts-1)
                            ca, sa = math.cos(ang), math.sin(ang)
                            x, y = ca*self.circleFraction, sa*self.circleFraction
                            glTexCoord2f(x*uv, y*uv); glVertex3f(x, y,  0.0)
                        glEnd()
                        
                        glPopMatrix()
                        				
                        i += 1
                        
                glPopMatrix()	
        
        if selectEvent != None:
            readPix = glReadPixels(selX,selY,1,1,GL_RGB,GL_UNSIGNED_BYTE)
            r,g,b = struct.unpack("BBB",readPix)
            if (r,g,b) in selectMap:
                return selectMap[(r,g,b)]
            else:
                return None


# ------------------------------------------------------------------------------
#

class MainWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        
        self.setWindowTitle('Rough Circle Quilt')
        self.setWindowIcon(E.getIcon("roundQuilt"))

        # Central widget
        self.quiltW = QuiltW(self,TilePngPaths)
        self.setCentralWidget(self.quiltW)

        self.styleNames = STYLENAMES
        
        # Tools
        self.makeMenus()
        self.makeToolBar()
        self.makeToolBoxDW()
        
        #self.initializeUI()
        QTimer.singleShot(200, self.initializeUi)

        self.statusBar().showMessage('Ready',2000)

    def makeMenus(self):
        exit = QAction('Exit', self)
        exit.setShortcut('Ctrl+Q')
        exit.setStatusTip('Exit application')
        self.connect(exit, SIGNAL('triggered()'), SLOT('close()'))

        menubar = self.menuBar()
        
        file = menubar.addMenu('&Application')
        file.addAction(exit)

        view = menubar.addMenu("&View")
        
        toolboxViewAction = QAction(E.getIcon("Setting-Tools"), 'Toolbox', self)
        view.addAction(toolboxViewAction)
        def toolboxViewActionCB(b):
            self.toolboxDW.show()
        self.connect(toolboxViewAction,SIGNAL("triggered (bool)"),toolboxViewActionCB)

    def makeToolBar(self):
        self.toolbar = QToolBar(self)
        self.toolbar.setFloatable(True)
        self.toolbar.setMovable(True)
        #self.toolbar.setAllowedAreas(Qt.TopDockWidgetArea)
        self.addToolBar(Qt.TopToolBarArea,self.toolbar)
        self.toolbar.addAction(E.getIcon("camera"),  "Snapshot", self.genericCB)

    def genericCB(self):
        print "hello"

    def makeToolBoxDW(self):
        self.toolboxDW = QDockWidget("Toolbox")
        self.addDockWidget(Qt.LeftDockWidgetArea,self.toolboxDW)
        self.toolbox = QToolBox()
        self.toolboxDW.setWidget( self.toolbox )

        self.imageOptionsW = QWidget(self.toolbox)
        iLayout = QVBoxLayout()
        self.imageOptionsW.setLayout(iLayout)
        parameterLayout = QGridLayout()
        iLayout.addLayout(parameterLayout)
        self.toolbox.addItem(self.imageOptionsW,E.getIcon("gear"),"Parameters")

        self.seedSB = QSpinBox(self.toolbox)
        self.seedSB.setMinimum(1)
        self.seedSB.setMaximum(100)
        self.connect(self.seedSB,SIGNAL("valueChanged (int)"), self.seedCB)
        parameterLayout.addWidget(self.seedSB,0,1)
        parameterLayout.addWidget(QLabel("Seed"),0,0)

        self.horzCountSB = QSpinBox(self.toolbox)
        self.horzCountSB.setMinimum(MINCOUNT)
        self.horzCountSB.setMaximum(MAXCOUNT)
        self.connect(self.horzCountSB,SIGNAL("valueChanged (int)"), self.countCB)
        parameterLayout.addWidget(self.horzCountSB,1,1)
        parameterLayout.addWidget(QLabel("H Count"),1,0)

        self.vertCountSB = QSpinBox(self.toolbox)
        self.vertCountSB.setMinimum(MINCOUNT)
        self.vertCountSB.setMaximum(MAXCOUNT)
        self.connect(self.vertCountSB,SIGNAL("valueChanged (int)"), self.countCB)
        parameterLayout.addWidget(self.vertCountSB,2,1)
        parameterLayout.addWidget(QLabel("V Count"),2,0)

        self.sizeSB = QSpinBox(self.toolbox)
        self.sizeSB.setMinimum(MINSIZE)
        self.sizeSB.setMaximum(MAXSIZE)
        self.sizeSB.setSuffix('"')
        self.connect(self.sizeSB,SIGNAL("valueChanged (int)"), self.tileSizeCB)
        parameterLayout.addWidget(self.sizeSB,3,1)
        parameterLayout.addWidget(QLabel("Size"),3,0)

        self.circleSizeS = QSlider(Qt.Horizontal,self.toolbox)
        self.circleSizeS.setMinimum(0)
        self.circleSizeS.setMaximum(100)
        self.circleSizeS.setValue(75)
        self.circleSizeCB(75)
        self.connect(self.circleSizeS, SIGNAL("valueChanged (int)"), self.circleSizeCB)
        parameterLayout.addWidget(self.circleSizeS,4,1)
        parameterLayout.addWidget(QLabel("Circle size"),4,0)

        iLayout.addStretch()

        self.tileToolWidget = dict()
        self.icon   = dict( Square=dict(), Circle=dict())
        self.pixmap = dict( Square=dict(), Circle=dict())
        
        for i,tilePath in enumerate(TilePngPaths):
            thumbPath = TilesDir / ("%s_thumb%s" % (tilePath.namebase,tilePath.ext))
            self.icon["Square"][i] = QIcon(str(thumbPath))
            self.pixmap["Square"][i] = QPixmap(str(thumbPath))
            
            thumbRoundPath = TilesDir / ("%s_thumbRound%s" % (tilePath.namebase,tilePath.ext))
            self.icon["Circle"][i] = QIcon(str(thumbRoundPath))
            self.pixmap["Circle"][i] = QPixmap(str(thumbRoundPath))
            
            style = self.styleNames[i>3]
            
            w = self.tileToolWidget[i] = QWidget(self.toolbox)
            iLayout = QVBoxLayout()
            w.setLayout(iLayout)
            parameterLayout = QGridLayout()
            iLayout.addLayout(parameterLayout)
            #self.toolbox.addItem(w,self.icon[style][i],"Tile #%d %s" % (i+1,style))
            self.toolbox.addItem(w,self.icon[style][i],"Tile #%d" % (i+1,))

            w.swatchL = DragDropLabel(self.toolbox)
            w.swatchL.setPixmap(self.pixmap["Square"][i])
            w.swatchL.dragText = QString(str(i))
            w.swatchL.dragPix  = self.pixmap["Square"][i]
            parameterLayout.addWidget(w.swatchL,0,1)
            
            w.quantityLE = QSlider(Qt.Horizontal,self.toolbox)
            w.quantityLE.setMinimum(0)
            w.quantityLE.setMaximum(100)
            w.quantityLE.setValue(50)
            self.quantityCB(i,50)
            self.connect(w.quantityLE,
                SIGNAL("valueChanged (int)"), 
                lambda v,s=self,tn=i: s.quantityCB(tn,v))
            parameterLayout.addWidget(w.quantityLE,1,1)
            parameterLayout.addWidget(QLabel("Quantity"),1,0)
            
            w.styleC = QComboBox(self.toolbox)
            w.styleC.addItems(list(self.styleNames))
            w.styleC.setCurrentIndex(int(i>3))
            self.connect(w.styleC,
                SIGNAL("currentIndexChanged (const QString&)"), 
                lambda v,s=self,tn=i: s.styleCB(tn,str(v)))
            self.styleCB(i,QString(style))
            parameterLayout.addWidget(w.styleC,2,1)
            parameterLayout.addWidget(QLabel("Style"),2,0)
            
            iLayout.addStretch()

    def initializeUi(self):
        self.sizeSB.setValue(MAXSIZE)
        self.horzCountSB.setValue(MINCOUNT)
        self.vertCountSB.setValue(MINCOUNT)
        self.circleSizeCB(75)

    def countCB(self,value):
        self.setCounts(self.horzCountSB.value(), self.vertCountSB.value())

    def tileSizeCB(self,value):
        self.setTileSize( float(self.sizeSB.value()))

    def circleSizeCB(self,value):
        self.setCircleSize(value/100.0)

    def quantityCB(self,tileNum,value):
        self.setTileQuantity(tileNum,value/100.0)

    def countStyles(self):
        counts = dict( (style,0) for style in self.styleNames )
        for w in self.tileToolWidget.values():
            style = (self.styleNames)[w.styleC.currentIndex()]
            counts[style] += 1
        return counts

    def styleCB(self,tileNum,style):
        if self.countStyles()[str(style)] < 2:
            #QMessageBox.critical(None, "Styles",
            #                "Need at least one of each style",
            #                QMessageBox.Ok | QMessageBox.Default,
            #                QMessageBox.NoButton)
            return
        self.setStyle(tileNum,style)
        self.toolbox.setItemIcon(tileNum+1,self.icon[str(style)][tileNum])
        #self.toolbox.setItemText(tileNum+1,"Tile #%d %s" % (tileNum+1,style))

    def seedCB(self,s):
        self.quiltW.setSeed(s)

    def setCounts(self,h,v):
        self.quiltW.setCounts(h,v)

    def setTileSize(self,size):
        self.quiltW.setTileSize(size)

    def setCircleSize(self,size):
        self.quiltW.setCircleFraction(size)

    def setTileQuantity(self,tileNum,fraction):
        self.quiltW.setQuantity(tileNum,fraction)

    def setStyle(self,tileNum,style):
        self.quiltW.setStyle(tileNum,style)


# ------------------------------------------------------------------------------
#

if __name__ == '__main__':
    #app = QApplication(sys.argv)
    window = MainWindow()
    deskRect = app.desktop().availableGeometry()
    window.setGeometry(deskRect.adjusted(10, 30, -10, -10))
    window.show()
    sys.exit(app.exec_())
