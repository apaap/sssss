# 5S_update.py
# Update the current 5S spaceship collection with imported ships
# - Import candidate ships from clipboard in sss and rle format
# - Load 5S collection from sss file
# - For each candidate ship:
#   * Check if it is a new speed or improves on the current ship
# - Sort new record ships into place in the collection
# - Export updated collection to sss file

import golly as g
import os
import itertools
import timeit
import sss
reload(sss)

timer = timeit.default_timer

# 5S project files
orthoFile = 'Orthogonal ships.txt'
diagFile = 'Diagonal ships.txt'
obliqueFile = 'Oblique ships.txt'
updatedFile = 'Updated ships.sss.txt'

# 5S Project parameters
MAXGEN = 20000
# This script will always find new and updated results from the clipboard and
# report them in updatedFile. Updated files written to *.ss2.txt files.
# If UPDATE == True then the *.sss.txt files will be updated.
UPDATE = True

def importNewShips():
    newshiptxt = g.getclipstr()
    status = 'Searching clipboard for new ships ...'
    Nnew = 0
    constructRLE = False
    errormsg = 'Error: failed to recognise rle pattern. Current pattern string:\n'
    shiprle = ''
    global newShipsList
    for line in newshiptxt.splitlines():
        line = line.strip()
        if constructRLE == False:
            # Try to import sss format ship
            newship = sss.parseshipstr(line)
            if not newship:
                # Try to import rle format ship
                if(line[0:4] == 'x = '):
                    # Found beginning of rle formatted pattern
                    if constructRLE == True:
                        g.note(errormsg + rule + shiprle + line)
                    constructRLE = True
                    parts = line.split('=')
                    if len(parts)==4:
                        rulestr = parts[3].strip()
                    elif len(parts)==3:
                        rulestr = 'B3/S23'
                    else:
                        constructRLE = False
                        g.note(errormsg + line)
                    shiprle = ''
        else:
            # Try to import sss format ship (just in case rle recognizer is confused)
            newship = sss.parseshipstr(line)
            if newship:
                g.note(errormsg + rule + shiprle + line)
            # Continue constructing rle pattern string
            shiprle += line
            if '!' in line:
                constructRLE = False
                newship = (0, rulestr, 0, 0, 0, shiprle)
        # If ship is in canonical sss format, then analysing it is unnecessary
        # However, it is worthwhile because not all search scripts analysed
        # ships consistently.
        # Need to analyse new ships anyway if importing them from rle.
        # Only need to canonise if ship is going to be added to collection
        # For the initial test only need to know minimum population and speed
        if newship:
            try:
                # Ignore ship if rule string does not have Birth and Survival elements
                # XXX This may miss some ships where the rule string is non-standard and
                #     doesn't reject undesired rules like Generations
                rulestr = newship[1]
                if not (rulestr[0] == 'B' and ('/S' in rulestr or '_S' in rulestr)):
                    g.note('Ignoring ship in non-isotropic rule.\n%s' % (newship,))
                    continue
                # Ignore B0 ships
                if "B0" in rulestr:
                    continue
                minpop, speed, _ = sss.testShip(newship[5], rulestr, MAXGEN)
                if not speed:
                    g.note('Ship analysis error: speed is empty.\n%s, %s, %s' % (minpop, speed, newship))
                    continue
                newShipsList.append( (minpop, rulestr)+speed+(sss.giveRLE(g.getcells(g.getrect())),) )
                newship = ()
                Nnew += 1
                if (Nnew % 500 == 0):
                    g.show('%s %d ships found.' % (status, Nnew))
            except RuntimeError:
                g.note("Error processing newship, check rule validity:\n" + str(newship))
            except:
                g.note("Error processing newship:\n" + str(newship))
                raise
    status = 'New ships imported, %d ships found. Testing new ships ...' % Nnew
    g.show(status)
    # g.note(str(newShipsList))

collectionNames = {'o': 'orthogonal', 'd': 'diagonal', 'k':'oblique'}

def update5StoSSS(rleFile, collection):
    sssFile = rleFile.replace('.txt', '.sss.txt')
    if sssFile == rleFile:
        g.exit('Error: failed to create new file name.')
    updateFile = sssFile.replace('.sss.txt', '.ss2.txt')
    shipDict = {}
    newSpeeds, updateSpeeds = set(), set()
    global updateShips
    global newShipsList
    header = ''
    status = 'Importing 5S %s collection from file: %s ...' % \
            (collectionNames[collection], rleFile)
    N = 0
    with open(sssFile) as fIn:
        for line in fIn:
            # Trust the data in the sss file, no need to test ships
            ship = sss.parseshipstr(line)
            if not ship:
                # Should only get here if the line was empty, or is a comment
                if (line and (not line[0] == '#')):
                    g.note('Ignoring line:\n\n' + line)
                header += line
                continue
            speed = ship[2:5]
            shipDict[speed] = ship
            N += 1
            if (N % 500 == 0):
                g.show('%s %d ships found.' % (status, N))
    status = '5S %s collection imported, %d ships found. Testing %d new ships ...' % \
            (collectionNames[collection], N, len(newShipsList))
    g.show(status)
    
    N = 0 # New ship counter
    NN = 0 # New ship of current type counter
    for newship in newShipsList:
        minpop, rulestr, dx, dy, period, shiprle = newship
        dy, dx = sss.minmaxofabs((dx, dy))
        if dx == 0: continue # oscillator
        if dy == 0: shiptype = 'o'
        elif dy == dx: shiptype = 'd'
        else: shiptype = 'k'
        # g.note(str((minpop, rulestr, dx, dy, period, shiprle, shiptype, newship)))
        if shiptype == collection:
            bUpdate = True
            speed = (dx, dy, period)
            # Replace current ship in collection if minimum population is reduced
            # or add the smallest (by minpop and bbox) ship for each new speed
            if speed in shipDict:
                if minpop < shipDict[speed][0]:
                    if speed not in newSpeeds:
                        updateSpeeds.add(speed)
                elif minpop == shipDict[speed][0]:
                    # If the speed is not yet in the collection then make sure
                    # to update with the ship that has the smallest bounding box
                    # as well as the lowest minpop
                    if speed in newSpeeds:
                        # Check bounding box areas
                        g.select([-1, -1, 1, 1])
                        g.clear(1)
                        g.putcells(g.parse(shipDict[speed][5]))
                        r = g.getrect()
                        bbox = r[2] * r[3]
                        g.select([-1, -1, 1, 1])
                        g.clear(1)
                        g.putcells(g.parse(shiprle))
                        r = g.getrect()
                        if bbox <= (r[2] * r[3]):
                            bUpdate = False
                    else:
                        bUpdate = False
                else:
                    bUpdate = False
            else:
                # New speed
                newSpeeds.add(speed)
            if bUpdate:
                # Canonise ship and update collection
                shipDict[speed] = sss.canon5Sship(newship)
            NN += 1
        N += 1
        if (N % 100 == 0):
            found = len(newSpeeds) + len(updateSpeeds)
            g.show('%s %d record ships found of %d/%d ships tested.' % (status, found, NN, N))
    
    # Convert to list and sort
    # ship format: (minpop, 'rulestr', dx, dy, period, 'shiprle')
    # For orthogonal and diagonal: sort order is first by period, then decreasing displacement
    # For oblique: sort order is first by slope, then period - specifically first dx, then dy, then period
    # if collection == 'k':
        # shipList = sorted(shipDict.values(), key=lambda x: (x[2], x[3], x[4]))
        # newSpeeds = sorted(newSpeeds, key=lambda x: (x[0], x[1], x[2]))
        # updateSpeeds = sorted(updateSpeeds, key=lambda x: (x[0], x[1], x[2]))
    # else:
        # shipList = sorted(shipDict.values(), key=lambda x: (x[4], -x[2]))
        # newSpeeds = sorted(newSpeeds, key=lambda x: (x[2], -x[0]))
        # updateSpeeds = sorted(updateSpeeds, key=lambda x: (x[2], -x[0]))
    # Sort order now consistent for all three collections:
    # First by period, then decreasing X displacement, then decreasing Y displacement
    shipList = sorted(shipDict.values(), key=lambda x: (x[4], -x[2], -x[3]))
    newSpeeds = sorted(newSpeeds, key=lambda x: (x[2], -x[0], -x[1]))
    updateSpeeds = sorted(updateSpeeds, key=lambda x: (x[2], -x[0], -x[1]))
    
    # Write ships to file
    if (newSpeeds or updateSpeeds):
        g.show('Writing to SSS file: ' + updateFile)
        with open(updateFile, 'w') as fOut:
            fOut.write(header)
            for ship in shipList:
                fOut.write(', '.join(map(str, ship))+'\n')
        if UPDATE:
            try:
                # Update the current project file
                os.remove(sssFile)
                os.rename(updateFile, sssFile)
            except:
                g.exit('Error updating SSS file: ' + sssFile)
    
    # Return list of new and updated speeds and update list of ships added to database
    updateShips += [shipDict[speed] for speed in itertools.chain(newSpeeds, updateSpeeds)]
    return (newSpeeds, updateSpeeds)

g.new('Update 5S')
newShipsList = []
importNewShips()

# Timing info
time0 = timer()

updateShips = []
results = ''

updateOrtho = update5StoSSS(orthoFile, 'o')
if updateOrtho[0] or updateOrtho[1]:
    results += '# Orthogonal speeds updated:\n# %s\n# %s\n' % updateOrtho
updateDiag = update5StoSSS(diagFile, 'd')
if updateDiag[0] or updateDiag[1]:
    results += '# Diagonal speeds updated:\n# %s\n# %s\n' % updateDiag
updateOblique = update5StoSSS(obliqueFile, 'k')
if updateOblique[0] or updateOblique[1]:
    results += '# Oblique speeds updated:\n# %s\n# %s\n' % updateOblique

duration = timer()-time0

updated = ( len(updateOrtho[0]) + len(updateDiag[0]) + len(updateOblique[0]), \
            len(updateOrtho[1]) + len(updateDiag[1]) + len(updateOblique[1]), \
            len(newShipsList) )

g.new('')
updateString = '5S collection updated - %d new and %d improved speeds out of %d ships.' % updated
if results:
    with open(updatedFile, 'a') as fOut:
        fOut.write('# %s\n' % updateString)
        fOut.write(results)
        for ship in updateShips:
            fOut.write(', '.join(map(str, ship))+'\n')
    g.show('Lists of updated speeds and ships written to %s, elapsed time: %g s' % (updatedFile, duration))
else:
    g.show('')
g.note(updateString)
