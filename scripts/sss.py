# sss.py
# Commonly used routines to analyse small patterns in isotropic 2-state rules
# Includes giveRLE.py, originally by Nathaniel Johnston
# Includes code from get_all_iso_rules.py, originally by Nathaniel Johnston and Peter Naszvadi
# by Arie Paap, Oct 2017

import itertools
import math
import golly as g

try:
    # Avoid xrange argument overflowing type C long on Python2
    if xrange(1):
        xrange = lambda stop: iter(itertools.count().next, stop)
except NameError:
    xrange = range

# Interpret a pattern in sss format
# Return a tuple with corresponding fields
# Format: (minpop, 'rulestr', dx, dy, period, 'shiprle')
def parseshipstr(shipstr):
    if (not shipstr) or (not shipstr[0] in '123456789'):
        return
    ship = shipstr.split(', ')
    if not len(ship) == 6:
        return
    ship[0] = int(ship[0])
    ship[1] = ship[1].strip()
    ship[2] = int(ship[2])
    ship[3] = int(ship[3])
    ship[4] = int(ship[4])
    ship[5] = ship[5].strip()
    return tuple(ship)


# Determine the minimum population, displacement and period of a spaceship
# Input ship is given by an rle string and a separate rule string. If either 
# string is empty then use the current pattern / rule (respectively).
# Clears the current layer and leaves the ship in the layer, in a minimum 
# population phase which has minimum bounding box area.
# XXX True displacement returned - consider returning 5S canonical displacement.
# XXX Might be better to shift choice of phase to canon5Sship() which also sets
#     the minimum isotropic rule and adjusts orientation to 5S project standard.
# XXX Only works in rules with 2 states.
# --------------------------------------------------------------------
def testShip(rlepatt, rule, maxgen = 2000):
    # Clear the layer and place the ship
    r = g.getrect()
    if rlepatt:
        patt = g.parse(rlepatt)
        # If rlepatt is in a multistate representation then patt will be
        # a multistate cell list. testShip() only works for ships in two
        # state rules, so convert to two state cell list.
        if (len(patt)%2):
            # This assumes all cells have non-zero state - which is reasonable
            # for the results of g.parse()
            patt = [ patt[i] for j, i in enumerate(patt[:-1]) if (j+1)%3 ]
    else:
        # Use the current pattern
        if not r:
            return (0, tuple())
        patt = g.getcells(r)
        patt = g.transform(patt, -r[0], -r[1])
    # g.note(str((rlepatt, rule)))
    if r:
        g.select(r)
        g.clear(0)
    g.putcells(patt)
    # g.note(str(len(patt)) + ", " + str(patt))
    # rlepatt might be different to the rle representation determined by
    # giveRLE(), so ensure we have the correct representation
    testrle = giveRLE(patt)
    if rule:
        g.setrule(rule)
    speed = ()
    startpop = int(g.getpop())
    bbox = g.getrect()
    minpop = startpop
    minbboxarea = bbox[2]*bbox[3]
    mingen = 0
    # Keep track of the total bbox
    maxx = bbox[2]
    maxy = bbox[3]
    maxpop = startpop
    # Ignore ship if rule is not a 2-state rule
    if not g.numstates()==2:
        return (minpop, speed)
    for ii in xrange(maxgen):
        g.run(1)
        r = g.getrect()
        if not r:
            # Pattern has died out and is therefore not a ship
            mingen = 0
            break
        pop = int(g.getpop())
        bboxarea = r[2]*r[3]
        if pop < minpop:
            # Find phase with minimimum population
            minpop = pop
            minbboxarea = r[2]*r[3]
            mingen = ii+1
        elif pop == minpop:
            # Amongst phases with min pop, find one with minimum bbox area
            # bboxarea = r[2]*r[3]
            if bboxarea < minbboxarea:
                minbboxarea = bboxarea
                mingen = ii+1
        # Track the bounding box of the pattern's evolution
        maxx = max(maxx, r[2])
        maxy = max(maxy, r[3])
        maxpop = max(maxpop, pop)
        if (pop == startpop and r[2:4] == bbox[2:4]):
            if (giveRLE(g.getcells(r)) == testrle):
                # Starting ship has reappeared
                speed = (r[0]-bbox[0], r[1]-bbox[1], ii+1) # displacement and period
                break
        # Check for rotated pattern 
        elif (pop == startpop and r[2:4] == bbox[3:1:-1]):
            # For 2-cell oscillators this is sufficient
            if minpop == 2:
                speed = (0, 0, 2*(ii+1))
                mingen = ii+1
                break
    g.run(mingen) # Evolve ship to generation with minimum population
    # return (minpop, speed)
    # return (minpop, speed, maxpop)
    return (minpop, speed, maxx*maxy)
# --------------------------------------------------------------------


# Return the minimum and maximum of the absolute value of a list of numbers
def minmaxofabs(v):
    v = [abs(x) for x in v]
    return min(v), max(v)

# Define a sign function
sign = lambda x: int(math.copysign(1, x))

# Find the canonical pattern for a sss format ship
# This is determined by orienting the ship so that it travels E, SE, or ESE,
# setting the rule to the minimal isotropic rule which supports the ship, and
# choosing a minimal bounding box phase from all phases with minimal population
# Input ship is in sss format: (minpop, 'rulestr', dx, dy, period, 'shiprle')
# XXX Two cases where the resulting pattern is not guaranteed to be canonical:
#   - asymmetrical ships travelling orthogonally or diagonally (either one of
#     the two orientations in the canonical direction may be returned)
#   - multiple phases having the minimal population and bounding box area
def canon5Sship(ship, maxgen=2000):
    minpop, rulestr, dx, dy, period, shiprle = ship
    shipPatt = g.parse(shiprle)
    # Transform ship to canonical direction
    if abs(dx) >= abs(dy):
        a, b, c, d = sign(dx), 0, 0, sign(dy)
    else:
        a, b, c, d = 0, sign(dy), sign(dx), 0
    dy, dx = minmaxofabs((dx, dy))
    shipPatt = g.transform(shipPatt, 0, 0, a, b, c, d)
    # Clear the layer and place the ship
    r = g.getrect()
    if r:
        g.select(r)
        g.clear(0)
    g.putcells(shipPatt)
    shiprle = giveRLE(g.getcells(g.getrect()))
    g.setrule(rulestr)
    # Determine the minimal isotropic rule
    setminisorule(period)
    return minpop, g.getrule(), dx, dy, period, shiprle
    

# Python function to convert a cell list to RLE
# Author: Nathaniel Johnston (nathaniel@nathanieljohnston.com), June 2009.
#    DMG: Refactored slightly so that the function input is a simple cell list.
#         No error checking added.
#         TBD:  check for multistate rule, show appropriate warning.
#    AJP: Replace g.evolve(clist,0) with Python sort (faster for small patterns)
# --------------------------------------------------------------------
def chunks(l, n):
    for i in range(0, len(l), n):
        yield l[i:i+n]

def giveRLE(clist):
    # clist_chunks = list (chunks (g.evolve(clist,0), 2))
    clist_chunks = list(chunks(clist, 2))
    clist_chunks.sort(key=lambda l:(l[1], l[0]))
    mcc = min(clist_chunks)
    rl_list = [[x[0]-mcc[0],x[1]-mcc[1]] for x in clist_chunks]
    rle_res = ""
    rle_len = 1
    rl_y = rl_list[0][1] - 1
    rl_x = 0
    for rl_i in rl_list:
        if rl_i[1] == rl_y:
            if rl_i[0] == rl_x + 1:
                rle_len += 1
            else:
                if rle_len == 1: rle_strA = ""
                else: rle_strA = str (rle_len)
                if rl_i[0] - rl_x - 1 == 1: rle_strB = ""
                else: rle_strB = str (rl_i[0] - rl_x - 1)
                
                rle_res = rle_res + rle_strA + "o" + rle_strB + "b"
                rle_len = 1
        else:
            if rle_len == 1: rle_strA = ""
            else: rle_strA = str (rle_len)
            if rl_i[1] - rl_y == 1: rle_strB = ""
            else: rle_strB = str (rl_i[1] - rl_y)
            if rl_i[0] == 1: rle_strC = "b"
            elif rl_i[0] == 0: rle_strC = ""
            else: rle_strC = str (rl_i[0]) + "b"
            
            rle_res = rle_res + rle_strA + "o" + rle_strB + "$" + rle_strC
            rle_len = 1
            
        rl_x = rl_i[0]
        rl_y = rl_i[1]
    
    if rle_len == 1: rle_strA = ""
    else: rle_strA = str (rle_len)
    rle_res = rle_res[2:] + rle_strA + "o"
    
    return rle_res+"!"
# --------------------------------------------------------------------

# Isotropic rule range functions
# Based on the rule computation scripts by Nathaniel Johnston and Peter Naszvadi
# Functions:
#   - parseTransitions:
#       Interpret the totalistic and isotropic rule elements as a list of isotropic transitions
#   - rulestringopt:
#       Cleanup a rulestring. Only used when rulestring will be displayed
#   - getRuleRangeElems:
#       Determines the minimum and maximum isotropic rules in which a pattern's
#       evolution remains unchanged for a given number of generations.
#       Returns the required and allowed isotropic rule transitions in four lists.
#       Optionally compute only the minimum or the maximum rule.
# --------------------------------------------------------------------

Hensel = [
    ['0'],
    ['1c', '1e'],
    ['2a', '2c', '2e', '2i', '2k', '2n'],
    ['3a', '3c', '3e', '3i', '3j', '3k', '3n', '3q', '3r', '3y'],
    ['4a', '4c', '4e', '4i', '4j', '4k', '4n', '4q', '4r', '4t', '4w', '4y', '4z'],
    ['5a', '5c', '5e', '5i', '5j', '5k', '5n', '5q', '5r', '5y'],
    ['6a', '6c', '6e', '6i', '6k', '6n'],
    ['7c', '7e'],
    ['8']
]

def parseTransitions(ruleTrans):
    ruleElem = []
    if not ruleTrans:
        return ruleElem
    context = ruleTrans[0]
    bNonTot = False
    bNegate = False
    for ch in ruleTrans[1:] + '9':
        if ch in '0123456789':
            if not bNonTot:
                ruleElem += Hensel[int(context)]
            context = ch
            bNonTot = False
            bNegate = False
        elif ch == '-':
            bNegate = True
            ruleElem += Hensel[int(context)]
        else:
            bNonTot = True
            if bNegate:
                ruleElem.remove(context + ch)
            else:
                ruleElem.append(context + ch)
    return ruleElem

def rulestringopt(a):
    result = ''
    context = ''
    lastnum = ''
    lastcontext = ''
    for i in a:
        if i in 'BS':
            context = i
            result += i
        elif i in '012345678':
            if (i == lastnum) and (lastcontext == context):
                pass
            else:
                lastcontext = context
                lastnum = i
                result += i
        else:
            result += i
    result = result.replace('4aceijknqrtwyz', '4')
    result = result.replace('3aceijknqry', '3')
    result = result.replace('5aceijknqry', '5')
    result = result.replace('2aceikn', '2')
    result = result.replace('6aceikn', '6')
    result = result.replace('1ce', '1')
    result = result.replace('7ce', '7')
    return result

def getRuleRangeElems(period, ruleRange = 'minmax'):
    if g.empty():
        return
    if period < 1:
        return
    
    rule = g.getrule().split(':')[0]
    
    if not (rule[0] == 'B' and '/S' in rule):
        g.exit('Please set Golly to an isotropic 2-state rule.')
    
    # Parse rule string to list of transitions for Birth and Survival
    oldrule = rule
    Bstr, Sstr = rule.split('/')
    Bstr = Bstr.lstrip('B')
    Sstr = Sstr.lstrip('S')
    b_need = parseTransitions(Bstr)
    b_OK = list(b_need)
    s_need = parseTransitions(Sstr)
    s_OK = list(s_need)
    
    patt = g.getcells(g.getrect())
    
    # Record behavior of pattern in current rule
    clist = []
    poplist = []
    for i in range(0,period):
        g.run(1)
        clist.append(g.getcells(g.getrect()))
        poplist.append(g.getpop())
    finalpop = g.getpop()
    
    if 'min' in ruleRange:
        # Test all rule transitions to determine if they are required
        for t in b_OK:
            b_need.remove(t)
            g.setrule('B' + ''.join(b_need) + '/S' + Sstr)
            r = g.getrect()
            if r: 
                g.select(r)
                g.clear(0)
            g.putcells(patt)
            for j in range(0, period):
                g.run(1)
                try:
                    if not(clist[j] == g.getcells(g.getrect())):
                        b_need.append(t)
                        break
                except:
                    b_need.append(t)
                    break
        b_need.sort()

        for t in s_OK:
            s_need.remove(t)
            g.setrule('B' + Bstr + '/S' + ''.join(s_need))
            r = g.getrect()
            if r: 
                g.select(r)
                g.clear(0)
            g.putcells(patt)
            for j in range(0, period):
                g.run(1)
                try:
                    if not(clist[j] == g.getcells(g.getrect())):
                        s_need.append(t)
                        break
                except:
                    s_need.append(t)
                    break
        s_need.sort()
    
    if 'max' in ruleRange:
        # Test unused rule transitions to determine if they are allowed
        allRuleElem = [t for l in Hensel for t in l]
        
        for t in allRuleElem:
            if t in b_OK:
                continue
            b_OK.append(t)
            g.setrule('B' + ''.join(b_OK) + '/S' + Sstr)
            r = g.getrect()
            if r: 
                g.select(r)
                g.clear(0)
            g.putcells(patt)
            for j in range(0, period):
                g.run(1)
                try:
                    if not(clist[j] == g.getcells(g.getrect())):
                        b_OK.remove(t)
                        break
                except:
                    b_OK.remove(t)
                    break
        b_OK.sort()
        
        for t in allRuleElem:
            if t in s_OK:
                continue
            s_OK.append(t)
            g.setrule('B' + Bstr + '/S' + ''.join(s_OK))
            r = g.getrect()
            if r: 
                g.select(r)
                g.clear(0)
            g.putcells(patt)
            for j in range(0, period):
                g.run(1)
                try:
                    if not(clist[j] == g.getcells(g.getrect())):
                        s_OK.remove(t)
                        break
                except:
                    s_OK.remove(t)
                    break
        s_OK.sort()
    
    r = g.getrect()
    if r: 
        g.select(r)
        g.clear(0)
    g.putcells(patt)
    g.setrule(oldrule)
    
    return b_need, s_need, b_OK, s_OK

def setminisorule(period):
    if g.empty():
        return
    if period < 1:
        return
    
    b_need, s_need, b_OK, s_OK = getRuleRangeElems(period, ruleRange = 'min')
    
    minrulestr = 'B' + ''.join(sorted(b_need)) + '/S' + ''.join(sorted(s_need))
    g.setrule(minrulestr)
    return minrulestr

# --------------------------------------------------------------------

# Generator for random order rule iterator over a given rulespace
# Uses a linear congruential generator to iterate over all the rules
# in the given rulespace in a pseudo random order
# The rule space is specified by four lists:
#   B_need - the required Birth transitions
#   S_need - the required Survival transitions
#   B_OK - the optional Birth transitions
#   S_OK - the optional Survival transitions
# Provide a value to seed to specify the starting point of the generator
#   seed < 2^(len(B_OK) + len(S_OK))
# --------------------------------------------------------------------

def iterRuleStr(B_OK, S_OK, B_need=[], S_need=[], seed=1):
    # Pseudo-random rule index generator using an LCG
    def randRuleIdx(nB_OK, nS_OK, seed=1):
        # LCG state initialisation
        m = 2**(nB_OK + nS_OK)
        c = 7
        a = 5
        # Reduce collisions for small seed values
        for _ in range(3):
            seed = (a*seed+c) % m
        
        # Masks for birth and survival transitions
        maskS = 2**nS_OK - 1
        maskB = (2**nB_OK - 1) << nS_OK
        
        for ii in xrange(m):
            seed = (a*seed+c) % m
            randS = seed & maskS
            randB = (seed & maskB) >> nS_OK
            yield (randB, randS)
    
    # Transition String retrieval
    def getTransStr(tList, idx):
        trans = ''
        for t in tList:
            if (idx & 1):
                trans += t
            idx = idx >> 1
        return trans
    
    Bstr = 'B' + ''.join(B_need)
    Sstr = '/S' + ''.join(S_need)
    
    for (Bidx, Sidx) in randRuleIdx(len(B_OK), len(S_OK), seed):
        rulestr = Bstr + getTransStr(B_OK, Bidx) + Sstr + getTransStr(S_OK, Sidx)
        yield rulestr

# --------------------------------------------------------------------
