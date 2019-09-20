# sssViewer.py v0.3
# Golly Python script to peview patterns in sss format
# Author: Arie Paap

import re
import time
from timeit import default_timer as timer 
import golly as g

# Check if pattern is in view and shift view / resize if necessary
def checkFit():
  r = g.getrect()
  if not r:
    return
  if not g.visrect(r):
    g.setpos(str(r[0] + r[2]/2), str(r[1] + r[3]/2))
    if not g.visrect(r):
      g.setmag(g.getmag()-1)

# regex for sss format ships
sssFormat = re.compile(r'(\d+), (B[0-9aceijknqrtwyz-]+/S[0-9aceijknqrtwyz-]*), (\d+), (\d+), (\d+), ([0-9ob$]+!)')

sssPatterns = []
filetypes = "sss Files (*.sss.txt;*.txt)|*.sss.txt;*.txt"
sssFile = g.opendialog("Choose spaceship file", filetypes)

# Grab a string containing all the sss format patterns
if sssFile:
  with open(sssFile, 'r') as F:
    sssFileLines = F.readlines()
else:
  sssFileLines = g.getclipstr().splitlines()

for line in sssFileLines:
  m = sssFormat.match(line)
  if m:
    # Format: (minpop, 'rulestr', dx, dy, period, 'shiprle')
    s = m.groups()
    sssPatterns.append((int(s[0]), s[1], int(s[2]), int(s[3]), int(s[4]), s[5]))

g.new('sss Patterns')
g.show('%d patterns imported' % len(sssPatterns))

# For frame rate and timing
frameRate = 100
framePeriod = 1.0/frameRate
# Attainable sleep resolution on most modern Python/OS combinations (1ms)
sleepTime = 0.001

N = 0
Npatts = len(sssPatterns)
while N < Npatts:
  ship = sssPatterns[N]
  r = g.getrect()
  if r:
    g.select(r)
    g.clear(0)
    g.select([])
  g.setgen('0')
  g.putcells(g.parse(ship[5]))
  g.setrule(ship[1])
  g.setpos('0', '0')
  g.setmag(2)
  status = "Pattern %d of %d, " % (N+1, Npatts)
  status += "Speed is (%d, %d)/ %d, " % ship[2:5]
  status += "press 'space' for next pattern, 'p' for previous, 'q' to quit"
  g.show(status)
  g.update()
  start = timer()
  frameTime = start
  while True:
    # Wait until next frame
    frameTime += framePeriod
    now = timer()
    if now > frameTime:
      frameTime = now
    else:
      while (frameTime - timer()) > sleepTime:
        time.sleep(sleepTime)
    g.step()
    
    # Keep the pattern in view
    checkFit()
    g.update()
    
    # Check for key presses and do events
    evt = g.getevent()
    if evt:
      parts = evt.split()
      if parts[0] == "key" and parts[1] == "space":
        N += 1
        break
      elif parts[0] == "key" and parts[1] == "p":
        N = max(0, N - 1)
        break
      elif parts[0] == "key" and parts[1] == "q":
        g.exit()
      else:
        g.doevent(evt)

r = g.getrect()
if r:
  g.select(r)
  g.clear(0)
  g.select([])
g.setgen('0')
g.show("Finished")
