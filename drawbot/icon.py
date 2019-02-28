s = 400
g = 2
f = .7
newPage(s, s)
s2 = 0.4*s
translate(.5*s,.5*s)
fill(1,0,.5)
oval(-.5*s2,-.5*s2,s2,s2)
rotate(45)
rect(-.125*s2,-1.5*s2,.25*s2,3*s2)
saveImage("icon.png")
saveImage("icon.svg")

newDrawing()
s = 20
g = 2
f = .7
newPage(s, s)
s2 = 0.4*s
translate(.5*s,.5*s)
fill(.2)
oval(-.5*s2,-.5*s2,s2,s2)
rotate(45)
rect(-.125*s2,-1.5*s2,.25*s2,3*s2)
saveImage("icon.pdf")