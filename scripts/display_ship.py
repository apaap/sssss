# display_ship.py
# This script will take a string representing a ship with some additional metadata
# and display it in the current layer
# It first checks the clipboard for a valid string and then requests input if necessary
# There is minimal error checking
# ship format: "minPop, rulestr, dx, dy, period, rlestr"

import golly as g
import sss

shipstr = g.getclipstr()
ship = sss.parseshipstr(shipstr)
if not ship:
    shipstr = g.getstring('Enter ship string:')
ship = sss.parseshipstr(shipstr)
if not ship:
    g.exit('Invalid ship string: ' + shipstr)
    
rulestr = ship[1]
shiprle = ship[5]

# g.new('')
r = g.getrect()
if r:
    g.select(r)
    g.clear(0)
g.select([])
g.setrule(rulestr)
g.putcells(g.parse(shiprle))

if not g.visrect(g.getrect()):
    g.fit()
