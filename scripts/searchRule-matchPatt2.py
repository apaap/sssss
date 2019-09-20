# searchRule-matchPatt2.py
# A new implementation of searchRule-matchPatt.py
# Searches for small oscillators and spaceships in the isotropic 2-state CA
# rulespace where several phases of the starting pattern match the evolution
# of the pattern in the current layer.
#
# by Arie Paap, Jun 2019
# Original random rule search scripts by Arie Paap and Rhombic
#
# Differences from searchRule-matchPatt.py:
#   - Press 'q' to stop searching (instead of aborting with 'Esc')
#   - Uses routines from sss.py library to analyse small patterns in isotropic
#       2-state rules
#   - Maintains record of found spaceship speeds to avoid reporting duplicate
#       results (set bUniqueSpeeds to false to disable)
#   - Optionally allows pattern to be run for a short stabilisation time prior
#       to testing for periodicity
#   - Optionally loads previously found speeds from output file at start of
#       search
#   - Optionally also load ships from 5S project into record of known speeds
#   - Random rule generator uses an iterator which pseudo randomly scans the
#       entire rulespace
#
# Potential features to be added
#   - XXX Save the random rule iterators' current state when interrupting the
#       search so that it can be resumed (repeating the same search without
#       changing the seed will search the same rules)

import time
import timeit
import golly as g
import sss
reload(sss)

timer = timeit.default_timer

# Search parameters

# Exclude ships with period less than minShipP
minShipP = 30
# Fast ships have a lower threshold for interesting period
minSpeed = 0.5
fastShipP = 9
# Exclude oscillators with period less than minOscP
minOscP = 3
# Maximum period to test the pattern for
maxGen = 20000 # 20000
# Maximum population in any phase
maxPop = 1000 # 1000
# Maximum bounding box dimension (0 to disable)
# - Early abort testRule() when stabilisation not detected e.g. when
#   spaceships emitted in multiple directions
maxDim = 500 # 500
# Allow search for oscillators
bOsc = False
# Output file
resultsFile = 'matchPatt2-test.txt'
# Only record ships with unique speed? (or smaller than previously found)
bUniqueSpeeds = True
# Import 5S project into known speeds?
bImport5S = True
# Special case speeds to ignore (useful when bUniqueSpeeds = False)
ignoreResults = [] # A list of the form: [(dx, dy, P)]

# Number of generations to match pattern behaviour
s = g.getstring('How many generations to remain unchanged:', '', 'Rules calculator')
if not s.isdigit():
    g.exit('Bad number: %s' % s)
numgen = int(s)
if numgen < 1:
    g.exit('Generations to match must be at least 1.')
# Seed for random rule generator
seed = 1

# Initial stabilisation time
# Test pattern is run in each random rule for stabGen generations before 
# periodicity detection begins
# Set to 0 to only match the test pattern
stabCycles = 5 # 5
stabGen = stabCycles * numgen
# Stability check periodicity
# - Used to detect if pattern becomes periodic after initial stabilisation time
#   Pattern won't be detected as an oscillator or spaceship, just avoids
#   simulting until maxGen generations have passed.
stabCheckP = 24 # 24

# Minimum population criteria
# - Probably redundant now that stability checking has been added
if bOsc: minPop = 2 # Patterns with 0, or 1 cells can not be oscillators
else: minPop = 3 # Patterns with 0, 1, or 2 cells can not be ships

# Test pattern in given rule
# Original pattern is evolved in the given randomly generated rule.
# Pattern is evolved for a short stabilisation period and then tested to
# determine if it has become an oscillator or a spaceship. 
def testRule(rulestr):
    r = g.getrect()
    if r:
        g.select(r)
        g.clear(0)
    g.putcells(origPatt)
    g.setrule(rulestr)
    g.run(stabGen)
    if g.empty():
        return ()
    pop = int(g.getpop())
    if (pop < minPop or pop > maxPop):
        return ()
    r = g.getrect()
    testPatt = g.transform(g.getcells(r),-r[0],-r[1])
    testPop = int(g.getpop())
    testRect = g.getrect()
    stabPatt = list(testPatt)
    stabPop = testPop
    for ii in xrange(maxGen):
        g.run(1)
        pop = int(g.getpop())
        if (pop < minPop or pop > maxPop):
            break
        if (pop == testPop):
            # Test for periodicity
            r = g.getrect()
            if testPatt == g.transform(g.getcells(r),-r[0],-r[1]):
                period = ii+1
                dy, dx = sss.minmaxofabs((r[0] - testRect[0], r[1] - testRect[1]))
                if (dx == 0):
                    # Oscillator (reject if low period or bOsc is False)
                    if bOsc and period >= minOscP:
                        return (0, 0, period)
                elif ( period >= minShipP ):
                    # Spaceship
                    return (dx, dy, period)
                elif ( (dx + dy/1.9) / (period * 1.0) > minSpeed and period >= fastShipP ):
                    # Fast spaceship
                    return (dx, dy, period)
                break # Pattern is a low period oscillator or spaceship
        # Stability check
        if (ii % stabCheckP == 0):
            r = g.getrect()
            # First check for BBox expansion
            if maxDim > 0 and max(r[2:4]) > maxDim:
                # Pattern is expanding
                # XXX Attempt to separate components expanding in different directions
                break
            currPatt = g.transform(g.getcells(r),-r[0],-r[1])
            if (pop == stabPop and currPatt == stabPatt):
                # Pattern has stabilised to low period oscillator / spaceship
                break
            stabPop = pop
            stabPatt = list(currPatt)
    return ()

# Preload foundSpeeds from existing results file
foundSpeeds = {}
def loadKnownSpeeds(resultsFile):
    global foundSpeeds
    g.show('Loading known speeds from file %s' % resultsFile)
    try:
        with open(resultsFile, 'r') as rF:
            for line in rF:
                # Trust the data in the sss file, no need to test ships
                ship = sss.parseshipstr(line)
                if not ship:
                    continue
                minpop, _, dx, dy, period, _ = ship
                try:
                    if foundSpeeds[(dx, dy, period)] <= minpop:
                        # Skip this speed unless the current ship is smaller
                        continue
                except KeyError:
                    pass
                foundSpeeds[(dx, dy, period)] = minpop
    except IOError:
        return 1
    return 0

if bImport5S:
    bUniqueSpeeds = True
    shipFiles = ['Orthogonal ships.sss.txt', 'Diagonal ships.sss.txt', 'Oblique ships.sss.txt']
else:
    shipFiles = []
    
status = 'Results file: %s.' % resultsFile
if bUniqueSpeeds:
    with open(resultsFile, 'a+') as rF:
        pass
    shipFiles.append(resultsFile)
    for F in shipFiles:
        if loadKnownSpeeds(F):
            g.exit('Failed to load known speeds from file: %s' % F)
    status += ' %d known speeds loaded.' % len(foundSpeeds)

# Set up the search with the current pattern
r = g.getrect()
origPop = int(g.getpop())
origPatt = g.transform(g.getcells(r),-r[0],-r[1])
origRule = g.getrule()

Nfound = 0
updateP = 1000
lastRule = ''

try:
    # Begin the search
    g.new('MatchPatt')
    g.putcells(origPatt)
    
    # Determine the rulespace to search
    B_need, S_need, B_OK, S_OK = sss.getRuleRangeElems(numgen)
    rulerange = sss.rulestringopt('B' + ''.join(sorted(B_need)) + '/S' + ''.join(sorted(S_need)) + \
            ' - B' + ''.join(sorted(B_OK)) + '/S' + ''.join(sorted(S_OK)))
    B_OK = [t for t in B_OK if t not in B_need]
    S_OK = [t for t in S_OK if t not in S_need]
    rulespace = len(B_OK) + len(S_OK)
    status += ' Matching pattern works in 2^%d rules: %s' % (rulespace, rulerange)
    g.show(status)
    g.update()
    time.sleep(2)
    
    # Results header
    with open(resultsFile, 'a') as rF:
        msg = '\n# Search results matching pattern %s for %d gen' % (sss.giveRLE(origPatt), numgen)
        msg += ' in rule %s with searchRule-matchPatt2.py using seed=%d\n' % (origRule, seed)
        rF.write(msg)
    
    start_time = timer()
    
    # Random rule iterator. Change seed to repeat search with different rules from given rulespace
    for (ii, rule) in enumerate(sss.iterRuleStr(B_OK, S_OK, B_need, S_need, seed=seed), start=1):
        result = testRule(rule)
        if result and (not result in ignoreResults):
            minpop = int(g.getpop())
            mingen = 0
            if bUniqueSpeeds:
                # Find minimum population
                for gen in xrange(1, result[2]):
                    g.run(1)
                    pop = int(g.getpop())
                    if pop < minpop:
                        minpop = pop
                        mingen = gen
                g.run(1)
                try:
                    if foundSpeeds[result] <= minpop:
                        # Skip this speed unless the current ship is smaller
                        continue
                except KeyError:
                    pass
                foundSpeeds[result] = minpop
            # Interesting pattern found
            Nfound += 1
            dx, dy, period = result
            lastRule = rule
            if dy == 0:
                if dx == 0:
                    description = 'Found oscillator with period = %d' % period
                else:
                    description = 'Found orthogonal spaceship with speed = %dc/%d' % (dx, period)
            elif dy == dx:
                description = 'Found diagonal spaceship with speed = %dc/%d' % (dx, period)
            else:
                description = 'Found knightship with speed = (%d, %d)c/%d' % (dx, dy, period)
            g.show(description)
            g.run(mingen)
            shipRLE = sss.giveRLE(g.getcells(g.getrect()))
            sss.setminisorule(period)
            newship = (minpop, g.getrule(), dx, dy, period, shipRLE)
            with open(resultsFile, 'a') as rF:
                rF.write(', '.join(map(str, newship))+'\n')
        if (ii % updateP == 0):
            curr_time = timer()
            g.select([])
            msg = '%d ships found after testing %d candidate rules out of 2^%d rule space' % (Nfound, ii, rulespace)
            msg += ', %d rules/second' % (updateP/(curr_time - start_time))
            start_time = curr_time
            g.show(msg)
            g.fit()
            g.setmag(3)
            g.update()
            event = g.getevent()
            if event == "key q none":
                # Interrupt the search
                # XXX Save the current state of the Rule generator's seed so that the search can be continued
                break
            g.new('')
            
except IOError:
    g.note('Failed to open results file %s for writing!' % resultsFile)
    raise
except Exception, e:
    raise
finally:
    g.new('Search result')
    g.putcells(origPatt)
    if lastRule:
        g.setrule(lastRule)
        g.show('%d ships found after testing %d candidate rules.' % (Nfound, ii))
    else:
        g.setrule(origRule)
        g.show('No results found after testing %d candidate rules.' % ii)
