#!/usr/bin/env python
# -*- coding: utf-8 -*-
#=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~==~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=#
#
#                              cookery.py
#                           Serve Beer Faster
#                       an experiment by tassaron
#                   created 2017/01/19, modified 02/05
#
#=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~==~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=#
import pyglet
import os
import random

#=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~==~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=#
#   Constants
#=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~==~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=#
Window = pyglet.window.Window(796, 596, caption='Cookery')
Mouse = pyglet.window.mouse
Key = pyglet.window.key
Batch = pyglet.graphics.Batch()
Layer1 = pyglet.graphics.OrderedGroup(0)
Layer2 = pyglet.graphics.OrderedGroup(1)
Layer3 = pyglet.graphics.OrderedGroup(2)
Layer4 = pyglet.graphics.OrderedGroup(3)

# put all .png files in SrcPath in a dictionary with filename as key
SrcPath = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'img')
Image = { os.path.splitext(f)[0] : pyglet.image.load(os.path.join(SrcPath, f)) \
   for f in os.listdir(SrcPath) if os.path.splitext(f)[1] == '.png' }

#=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~==~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=#
#  Main Game Object
#=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~==~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=#
class Game(object):
    def __init__(self):
        # no keys or mouse buttons are being held down...
        self.mouseRelease()
        self.keyRelease()
        # game logic/instance handling variables
        self.instances = {} # instances in existence
        self.instanceIDs = [] # unique ints representing each instance
        self.updateEveryTick = [] # instances that update every tick

        # all instances have 1 or no hotspot, so the keys are instanceIDs
        self.hotspots = {}
        # but instances can have >1 hotkey so instanceIDs are values instead
        self.hotkeys = {}

        # create object for dealing with in-game variables
        self.memory = Memory()

        # start in the menu
        self.room = 'menu'

    def __repr__(self):
        # TODO: tidy this up
        def prettyNum(num):
            return str(num).zfill(4)
        # string representation of game state used for debugging
        dingbat = '~='*4
        string = dingbat*4+'\n'+dingbat+'INSTANCES:'+dingbat+'\n'
        for instanceID, instanceObj in self.instances.iteritems():
            string += prettyNum(instanceID) +' - '+ str(instanceObj) +'\n'
        if len(self.updateEveryTick)>0:
            string += dingbat+ 'updateEveryTick:'+dingbat+'\n'+\
                      str(self.updateEveryTick) +'\n'
        string += dingbat+'HOTSPOTS:'+dingbat+'\n'
        for instanceID, hotspot in self.hotspots.iteritems():
            string += prettyNum(instanceID)+' - '+self.instances[instanceID].__class__.__name__+' -'+str(hotspot)+'\n'
        string += dingbat*4
        return string

    ''' instance handling'''
    def newInstance(self,instance,hotspot):
        # register a new instance of a class so Game can manage it
        # hotspot is tuple of tuples of x,y -- if no hotspot then is -1
        instanceID = self.getEmptyID()
        self.instances[instanceID] = instance
        self.hotspots[instanceID] = hotspot
        return instanceID

    def getEmptyID(self):
        choice = 1
        # generate IDs until finding one that is not in use
        while choice in self.instanceIDs:
            choice = random.randint(1, 10000)
        # put newly generated ID in instanceIDs list
        self.instanceIDs.append(choice)
        return choice

    def deleteInstance(self, instanceID):
        # remove room references to instance
        self.hotspots.pop(instanceID)
        self.instanceIDs.remove(instanceID)
        if instanceID in self.updateEveryTick:
            self.updateEveryTick.remove(instanceID)
        if instanceID in self.hotkeys:
            # remove any hotkey that points to this instance
            self.hotkeys = { key:iID for key, iID in self.hotkeys.items() if iID!=instanceID }
        instance = self.instances.pop(instanceID)
        instance.delete()

    def deleteAllInstances(self):
        copyOfIDList = list(self.instanceIDs)
        # we need a copy since the list indexes will change
        for instanceID in copyOfIDList:
            try:
                self.deleteInstance(instanceID)
            except KeyError:
                # because some instances delete others in their delete()
                # so the KeyErrors are not ideal but also not important
                pass

    ''' other methods '''
    def mousePress(self, x, y, button, modifiers):
        # a mouse and key press cannot both be activated in one tick
        if self.currentKeyPress==None:
            self.currentMousePress = (x, y, button, modifiers)
            if button == Mouse.LEFT:
                for instanceID in self.hotspots.keys():
                    # don't test the hotspot if there is none
                    if self.hotspots[instanceID] != -1:
                        coords = self.hotspots[instanceID]
                        bottomCorner, topCorner = coords
                        if x >= bottomCorner[0] and x <= topCorner[0]:
                            if y >= bottomCorner[1] and y <= topCorner[1]:
                                self.instances[instanceID].activate()

    def mouseRelease(self):
        # this triggers when the mouse button is released or
        # if the mouse is moved. used to allow button to be held down
        self.currentMousePress = None

    def keyPress(self, key, modifiers):
        # a mouse and key press cannot both be activated in one tick
        # this stops player from holding down mouse & key for doubled effects
        if self.currentMousePress==None:
            if key==Key.F3:
                debug()
            self.currentKeyPress = (key, modifiers)
            if key in self.hotkeys.keys() and self.hotkeys[key] != None:
                instanceID = self.hotkeys[key]
                self.instances[instanceID].activate()

    def keyRelease(self):
        self.currentKeyPress = None

    def tick(self, dt):
        self.dt = dt # time since last frame
        # first check if the room has changed
        if type(self.room)==str:
            # if it has, delete all instances
            self.deleteAllInstances()
            # create new room & new instances
            self.room = Room(self.room)
        for instanceID in self.updateEveryTick:
            self.instances[instanceID].tick()
        # If a mouse button or key is held down, send event every tick
        if self.currentMousePress:
            x, y, button, modifiers = self.currentMousePress
            self.mousePress(x, y, button, modifiers)
        if self.currentKeyPress:
            key, modifiers = self.currentKeyPress
            self.keyPress(key, modifiers)

    def draw(self):
        Window.clear()
        Batch.draw()

class Memory(object):
    # used to load/save games & store visible stats like playerMoney
    def __init__(self):
        self.gameStarted = False
        self.playerMoney = 10000
        self.popularity = 50 # out of 100
        self.customerPatience = 6 # when tickets start to despawn, in seconds
        self.perfectOrders=0
        self.averageOrders=0
        self.badOrders=0

#=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~==~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=#
#  Rooms
#=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~==~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=#
class Room(object):
    def __init__(self, roomtype):
        if roomtype=='menu':
            # main menu seen between each in-game day
            startButton = Hyperlink()
            quitButton = Hyperlink()
            startButton.destination = 'working'
            quitButton.destination = 'quitroom'
            if Game.memory.gameStarted==False:
                startButton.setLabel('Start Game')
            else:
                startButton.setLabel('Continue >')
            quitButton.setLabel('Quit')
            menuStartY = Window.height/2 + (startButton.height*2)
            startButton.position(y=menuStartY)
            quitButton.position(y=menuStartY-quitButton.height-16)
            box = Rectangle(color=(0,104,0), width=startButton.width+16, \
                            height=startButton.height*2+32)
            box.position(x=quitButton.x-8,y=quitButton.y-8)
            Game.memory.gameStarted=True
        elif roomtype=='working':
            # working room
            backButton = Hyperlink()
            backButton.position(x=Window.width-(Window.width/4),y=16)
            backButton.setLabel('Back to Menu')
            backButton.destination = 'menu'
            ticketspawner = Spawner()
            moneyPrinter = ScoreDisplay()
            moneyPrinter.position(x=Window.width-((Window.width/4)*2)-Ticket.padding,y=16)
        elif roomtype=='quitroom':
            # quit the game
            raise SystemExit

#=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~==~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=#
#  Entity Parents
#=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~==~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=#
class Entity(pyglet.sprite.Sprite):
    def __init__(self, *args, **kwargs):
        super(Entity, self).__init__(*args, **kwargs)
        self.label=None
        # register this instance with the Game object
        self.instanceID = Game.newInstance(self, self.getHotspot())

    def getHotspot(self):
        return ( (self.x, self.y), (self.x+self.width, self.y+self.height) )

    def setLabel(self, string):
        if self.label:
            # delete old Label object, which would otherwise leave a ghost
            self.label.delete()
        self.label = pyglet.text.Label(string, font_size=18, font_name='Arial',
                          y=self.y+(self.height/2), anchor_y='center', \
                          x=self.x+(self.width/2), anchor_x='center',\
                          color=((0, 0, 0, 255)), batch=Batch, group=Layer4)

    def position(self, x=False, y=False):
        # update hotspot & label, optionally move to new x and/or y
        if x:
            self.x = x
            if self.label:
                self.label.x = x+(self.width/2)
        if y:
            self.y = y
            if self.label:
                self.label.y = y+(self.height/2)
        if not x and not y and self.label:
            # update the label if we haven't yet & there is one
            self.label.x = self.x+(self.width/2)
            self.label.y = self.y+(self.height/2)
        Game.hotspots[self.instanceID] = self.getHotspot()

    def __repr__(self):
        return self.__class__.__name__

    def delete(self):
        if self.label:
            self.label.delete()

class NonclickableEntity(Entity):
    def __init__(self, *args, **kwargs):
        # skip our parent's init, but call our grandpa's init
        super(Entity, self).__init__(*args, **kwargs)

        # register this instance with no hotspot
        self.instanceID = Game.newInstance(self,-1)
        Game.updateEveryTick.append(self.instanceID)
        self.label = None

    def getHotspot(self):
        return -1

class InvisibleEntity(object):
    # invisible entities automatically update every tick, no maintenance needed
    def __init__(self):
        # register this instance with no hotspot
        self.instanceID = Game.newInstance(self, -1)
        # it will update every tick
        Game.updateEveryTick.append(self.instanceID)

    def __repr__(self):
        return self.__class__.__name__

    def delete(self):
        # I ain't care
        pass

#=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~==~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=#
#   Entities
#=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~==~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=#
class Ticket(Entity):
    ticketHeight = 48
    padding = 8 # px separating ticket from other sprites & left edge of window
    movementSpeed = 80
    # this variable prevents opening more than one ticket minigame at a time
    activationLocked = False
    ticketTypes = ['Beer']

    @classmethod
    def createPrepTables(class_):
        # create list of available prep tables
        origin = Window.height-Ticket.padding-Ticket.ticketHeight
        yDistance = Ticket.ticketHeight+Ticket.padding
        Ticket.prepTables = { i+1 : origin-yDistance*i for i in range(6) }
        Ticket.freeTables = list(Ticket.prepTables.keys())

    @classmethod
    def getTicketType(class_):
        return random.choice(Ticket.ticketTypes)

    def __init__(self):
        super(Ticket, self).__init__(Image['ticket'], batch=Batch, group=Layer2)
        Ticket.ticketHeight = self.height
        Ticket.ticketWidth = self.width
        self.ticketType = Ticket.getTicketType()
        # for organization some attributes are stored in tickettype's class
        string = 'self.color = %s.ticketcolor; self.profit = %s.profit'\
                % (self.ticketType, self.ticketType)
        exec(string)
        self.activation = 0

    def spawn(self, despawnTime):
        self.age = 0
        self.despawnTime = despawnTime
        # choose y-level & remove it from the list of free y-levels
        mytable = random.choice(Ticket.freeTables)
        self.y = Ticket.prepTables[mytable]
        Ticket.freeTables.remove(mytable)
        # get hotkey & create ticketalert which displays it
        string = 'self.hotkey = Key._%s' % str(mytable)
        exec(string)
        self.prepTable=mytable
        Game.hotkeys[self.hotkey] = self.instanceID
        self.alert = ticketAlert(str(mytable))
        self.alert.position(x=self.x, y=self.y)
        # position ticket outside window
        self.position(x=0-self.width)
        # label it and start moving right
        self.isMovingRight = True
        self.isMovingLeft = False
        self.setLabel(self.ticketType)
        Game.updateEveryTick.append(self.instanceID)


    def moveRight(self):
        if self.x <= Ticket.padding:
            self.position(x = self.x + Ticket.movementSpeed * Game.dt)
        else:
            # stop when fully on-screen
            self.position(x=Ticket.padding)
            self.isMovingRight = False

    def moveLeft(self):
        if self.x <= 0-self.width:
            # if entire ticket is off-screen, suicide
            Game.memory.playerMoney -= self.profit
            Game.deleteInstance(self.instanceID)
        else:
            self.position(x = self.x - Ticket.movementSpeed * Game.dt)
            self.alert.isMovingLeft = True

    def tick(self):
        if self.isMovingRight:
            # ticket is sliding on-screen
            self.moveRight()
        elif self.isMovingLeft:
            # the ticket is leaving!
            self.moveLeft()
        else:
            # new ticket is sitting idle waiting for action
            self.age+=1
            if self.age/60 > self.despawnTime:
                self.isMovingLeft=True

    def activate(self):
        if self.activation==0:
            # can't activate first time if another ticket is activated
            if Ticket.activationLocked == False:
                Ticket.activationLocked=True
                # make a new minigame controller object, whose class is this Type
                minigameController = '%s(source=%s)' % (self.ticketType, self.instanceID)
                exec(minigameController)
                # freeze the ticket in place during minigame
                self.isMovingLeft = False
                self.isMovingRight = False
                self.position(x=Ticket.padding)
                self.alert.position(x=Ticket.padding+self.width)
                # don't update this ticket again until the minigame finishes
                Game.updateEveryTick.remove(self.instanceID)
                self.activation+=1

    def delete(self):
        super(Ticket,self).delete()
        # free up this ticket's prep table
        Ticket.freeTables.append(self.prepTable)
        # clear the hotkey, stop updates
        Game.hotkeys[self.hotkey]=None
        if self.instanceID in Game.updateEveryTick:
            Game.updateEveryTick.remove(self.instanceID)
        # delete this ticket's alert
        Game.deleteInstance(self.alert.instanceID)

class Hyperlink(Entity):
    def __init__(self):
        super(Hyperlink, self).__init__(Image['ticket'], batch=Batch, group=Layer3)
        self.destination = None
        # x-center hyperlinks by default
        self.position(x=(Window.width/2)-(self.width/2))

    def activate(self):
        if self.destination != None:
            Game.room = self.destination

#=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~==~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=#
#   Nonclickable Entities
#=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~==~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=#
class ScoreDisplay(NonclickableEntity):
    def __init__(self):
        super(ScoreDisplay, self).__init__(Image['ticket'], batch=Batch, group=Layer2)
        self.prevScore = Game.memory.playerMoney
        string = ScoreDisplay.formatMoney(Game.memory.playerMoney)
        self.setLabel(string)

    def tick(self):
        scoreDifference = Game.memory.playerMoney-self.prevScore
        if scoreDifference != 0:
            # if the score changed, create a notice
            notice = scoreChange(scoreDifference)
            notice.position(x=self.x+self.width/2-40, y=self.y+self.height)
            string = ScoreDisplay.formatMoney(Game.memory.playerMoney)
            self.setLabel(string)
        self.prevScore = Game.memory.playerMoney

    @staticmethod
    def formatMoney(number):
        # add commas
        string = '{:2,.0f}'.format(number)
        # add dollar sign
        return '$%s' % string

class scoreChange(NonclickableEntity):
    def __init__(self, scoreDifference):
        super(scoreChange, self).__init__(Image['circleGradient'],batch=Batch,group=Layer4)
        self.opacity = 128
        if scoreDifference>0:
            # green for positive
            self.setLabel('+%s' % str(scoreDifference))
            self.color = (0,153,0)
            self.label.color = (0,204,0,255)
        else:
            # red for negative
            self.setLabel(str(scoreDifference))
            self.color = (180,0,0)
            self.label.color = (248,0,0,255)
        self.age=0

    def tick(self):
        self.age += 1
        self.position(y=self.y+100*Game.dt)
        if self.age > 50:
            Game.deleteInstance(self.instanceID)

class Rectangle(NonclickableEntity):
    def __init__(self, color, width, height):
        r, g, b = color
        image =  pyglet.image.SolidColorImagePattern(color=(r,g,b,255))
        image = image.create_image(width, height)
        super(Rectangle, self).__init__(image,batch=Batch,group=Layer2)
        Game.updateEveryTick.remove(self.instanceID)

class ticketAlert(NonclickableEntity):
    def __init__(self, text):
        super(ticketAlert,self).__init__(Image['alert'],batch=Batch,group=Layer3)
        self.setLabel(text)
        self.isMovingRight = True
        self.isMovingLeft = False

    def tick(self):
        if self.isMovingRight:
            self.moveRight()
        elif self.isMovingLeft:
            self.moveLeft()

    def moveRight(self):
        if self.x <= Ticket.padding + Ticket.ticketWidth:
            self.position(x = self.x + Ticket.movementSpeed * Game.dt)
        else:
            # stop when fully on-screen
            self.position(x=Ticket.padding+Ticket.ticketWidth)
            self.isMovingRight = False

    def moveLeft(self):
        if self.x > 0-self.width:
            self.position(x = self.x - Ticket.movementSpeed * Game.dt)


#=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~==~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=#
#   Invisible Entities
#=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~==~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=#
class Spawner(InvisibleEntity):
    # creates tickets
    def __init__(self):
        super(Spawner,self).__init__()
        # make internal references to base stats from Memory
        # this spawner may change stats based on situation
        self.ticketSpawnRate = Game.memory.popularity
        self.ticketDespawnRate = Game.memory.customerPatience
        self.frame = 0
        # create new list of prep tables for tickets
        Ticket.createPrepTables()
        # unlock the Ticket class's creation of minigame objects
        Ticket.activationLocked=False
        '''for debug purposes, spawn a ticket right away'''
        self.spawnTicket(justdoit=True)

    def tick(self):
        if self.frame >= 59:
            self.frame = 0
            #print 'tick'
            self.spawnTicket()
        else:
            self.frame+=1

    def spawnTicket(self, justdoit=False):
        def doit():
            newTicket = Ticket()
            newTicket.spawn(self.ticketDespawnRate)
        # try to spawn a ticket if there is a free 'prep table'
        if len(Ticket.freeTables)>0:
            if not justdoit:
                ch = random.randint(1, self.ticketSpawnRate)
                if ch > 40:
                    # attempt to spawn a new ticket
                    doit()
                #print 'tock'+str(ch)
            else:
                # just fuckin do it mang
                doit()

class MinigameController(InvisibleEntity):
    def __init__(self):
        super(MinigameController,self).__init__()
        Game.hotkeys[Key.ENTER] = self.instanceID

    def donePerfect(self):
        Game.memory.perfectOrders += 1
        Game.memory.playerMoney += self.profit

    def doneAverage(self):
        Game.memory.averageOrders += 1
        Game.memory.playerMoney += self.profit//2

    def doneBad(self):
        Game.memory.badOrders += 1
        Game.memory.playerMoney -= self.profit//2

#=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~==~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=#
#   Beer Minigame
#=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~==~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=#
class Beer(MinigameController):
    profit = 8
    ticketcolor = (255,215,0)

    def __init__(self, source):
        super(Beer,self).__init__()
        beermug = beerMug()
        beertap = beerTap(destination=beermug.y)
        beerfull = beerFull(x=beermug.x, y=beermug.y)
        foam = beerOverflow(); beerOverflow.isvisible=False
        foam.position(x=beerfull.x, y=beerfull.y)
        self.myinstances = [source, beermug.instanceID, beertap.instanceID, beerfull.instanceID, foam.instanceID]
        self.profit = Beer.profit
        self.source = Game.instances[source]

    def tick(self):
        pass

    def activate(self):
        # called when the player presses ENTER
        if beerFull.amount <= 60:
            self.doneBad()
        elif beerFull.amount > 70 and beerFull.amount < 85:
            self.doneAverage()
        elif beerFull.amount > 100:
            self.doneBad()
        else:
            self.donePerfect()
        Game.deleteInstance(self.instanceID)

    def delete(self):
        super(Beer, self).delete()
        # delete everything related to this minigame
        for instanceID in self.myinstances:
            Game.deleteInstance(instanceID)
        Ticket.activationLocked = False # unlock Tickets' creation of minigames
        Game.hotkeys[Key.ENTER] = None
        Game.hotkeys[Key.DOWN] = None
        Game.hotkeys[self.source.hotkey] = None
        beerFull.height=-600 # let beer drops go off-screen

class beerMug(NonclickableEntity):
    def __init__(self):
        super(beerMug,self).__init__(Image['beerMug'], batch=Batch, group=Layer3)
        Game.updateEveryTick.remove(self.instanceID)
        self.position( x=(Window.width/2)-25, y=40+Window.height-((Window.height/3)*2) )

class beerFull(NonclickableEntity):
    # list of animation frames
    anim = [Image['beerFull'].get_region(0, 0, Image['beerFull'].width,i*40) for i in range(6)]

    def __init__(self, x, y):
        super(beerFull,self).__init__(Image['beerFull'], batch=Batch, group=Layer2)
        self.position(x=x, y=y)
        self.opacity=0
        # class variable editable by other entities to represent how full the mug is
        beerFull.amount = 0
        beerFull.height = 18
        self.tick()

    def tick(self):
        if beerFull.amount >= 1 and beerFull.amount < 20:
            self.opacity=255
            self.image = beerFull.anim[1]
            beerFull.height = beerFull.anim[1].height
        elif beerFull.amount >= 20 and beerFull.amount < 50:
            self.image = beerFull.anim[2]
            beerFull.height = beerFull.anim[2].height
        elif beerFull.amount >= 50 and beerFull.amount < 90:
            self.image = beerFull.anim[3]
            beerFull.height = beerFull.anim[3].height
        elif beerFull.amount >= 85 and beerFull.amount <= 100:
            self.image = beerFull.anim[4]
            beerFull.height = beerFull.anim[4].height
        elif beerFull.amount > 100:
            beerOverflow.isvisible=True

class beerOverflow(NonclickableEntity):
    isvisible=False
    def __init__(self):
        super(beerOverflow,self).__init__(Image['beerOverflow'], batch=Batch, group=Layer3)
        self.tick()

    def tick(self):
        if beerOverflow.isvisible==True:
            self.opacity=255
        else:
            self.opacity=0

class beerTap(Entity):
    def __init__(self, destination):
        super(beerTap,self).__init__(Image['beerTap'], batch=Batch, group=Layer3)
        self.position( x=Window.width/2, y=destination+70+self.height )
        # 7-frame delay between beer drops
        self.timeout=3
        self.beerDispensed = 0
        Game.hotkeys[Key.DOWN] = self.instanceID
        self.destination = destination

    def activate(self):
        if self.timeout > 2:
            self.timeout=0
            # dispense some beer!
            beerDrop(destination=self.destination, origin=(self.x+8,self.y))
        else:
            self.timeout+=1

class beerDrop(NonclickableEntity):
    def __init__(self, destination, origin):
        super(beerDrop,self).__init__(Image['circleGradient'], batch=Batch, group=Layer2)
        self.color = Beer.ticketcolor
        self.position( x=origin[0], y=origin[1] )
        self.destination = destination

    def tick(self):
        # beer drops down towards the mug ...
        self.y -= 280*Game.dt
        if self.y < self.destination + beerFull.height - 6:
            # when reaching the beerFull sprite, add to it
            beerFull.amount += 5
        if self.y < self.destination + beerFull.height - 6 or self.y < 0:
            # disappear at beerFull sprite or off-screen
            Game.deleteInstance(self.instanceID)

#=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~==~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=#
#   Crap At The Bottom
#=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~==~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=#
def debug():
    print Game

def tick(dt):
    Game.tick(dt)

def initGame():
    global Game
    Game = Game()
    # pass window events thru to Game
    @Window.event
    def on_mouse_press(x, y, button, modifiers):
        Game.mousePress(x, y, button, modifiers)
    @Window.event
    def on_mouse_release(x, y, button, modifiers):
        Game.mouseRelease()
    @Window.event
    def on_mouse_motion(x, y, dx, dy):
        Game.mouseRelease()
    @Window.event
    def on_key_press(symbol, modifiers):
        Game.keyPress(symbol, modifiers)
    @Window.event
    def on_key_release(symbol, modifiers):
        Game.keyRelease()
    @Window.event
    def on_draw():
        Game.draw()

if __name__=='__main__':
    # set purple default background colour
    pyglet.gl.glClearColor(.4, .1, .5, 1)
    # create global Game object
    initGame()
    # start event loop
    pyglet.clock.schedule_interval(tick, 1/60.0) # tick 60 times per second
    pyglet.app.run()
