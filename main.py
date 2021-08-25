import pygame, sys, os, time, math

# Width screen. Pixels
screenWidth = 800
# Height screen
screenHeight = 600
#
squareSize = 50
# Original upscaled (Frames per second)
fps = 30

enemyList = []
towerList = []
bulletList = []
iconList = []
senderList = []
# initalize empty arrays of items on new map

colors = { # R,G,B
    'yellow':   (255,255,0),
    'lime':     (0,255,0),
    'darkblue': (0,0,255),
    'aqua':     (0,255,255),
    'magenta':  (255,0,255),
    'purple':   (128,0,128),
    'green':    (97,144,0),
    'purple':   (197,125,190),
    'brown':    (110,73,32),}

# Optional music
def play_music(file, volume=0.65, loop=-1):
    pygame.mixer.music.load(file)
    # load music from file mp3
    pygame.mixer.music.set_volume(volume)
    pygame.mixer.music.play(loop)
# comment out if you don't want music

def stop_music(): pygame.mixer.music.stop()
#
def imgLoad(file,size=None):
    image = pygame.image.load(file).convert_alpha()
    return pygame.transform.scale(image,size) if size else image

class Player:
    towers = [ # Name of monkey tower
        'Dart Monkey',
        'Tack Shooter',
        'Sniper Monkey',
        'Boomerang Thrower',
        'Ninja Monkey',
        'Bomb Tower',
        'Ice Tower',
        'Glue Gunner',
        'Monkey Buccaneer',
        'Super Monkey',
        'Monkey Apprentice',
        'Spike Factory',
        'Road Spikes',
        'Exploding Pineapple',]

    def __init__(self):
        self.health = 100
        self.money = 650

player = Player()


# store images using a dictionary 
EnemyImageArray = dict()
TowerImageArray = dict()
def loadImages():
    for tower in player.towers: TowerImageArray[tower] = imgLoad('towers/'+tower+'.png')
    # load selected tower

    bloon = imgLoad('enemies/bloonImg.png')
    EnemyImageArray['red'] = bloon
    width,height = bloon.get_size()
    for name in colors:
        image = bloon.copy()
        for x in range(width):
            for y in range(height):
                p = image.get_at((x,y))[:-1]
                if p not in ((0,0,0),(255,255,255)):
                    # check if in rgb colour bounds
                    c = colors[name]
                    r,g,b = p[0]*c[0]/255, p[0]*c[1]/255, p[0]*c[2]/255
                    image.set_at((x,y),(min(int(r),255),min(int(g),255),min(int(b),255)))
        EnemyImageArray[name] = image

def get_angle(a,b):
    return 180-(math.atan2(b[0]-a[0],b[1]-a[1]))/(math.pi/180)

class Map:
    # setup map
    def __init__(self):
        self.map = 'monkey lane'
        self.loadmap()

    def loadmap(self):
        self.targets = eval(open('maps/%s/targets.txt' % self.map,'r').read())
        self.waves = eval(open('maps/%s/waves.txt' % self.map,'r').read())

    def getmovelist(self):
        self.pathpoints = []
        for i in range(len(self.targets)-1):
            a,b = self.targets[i:i+2]
            self.pathpoints+=[0]

    def get_background(self):
        # load from background png
        background = imgLoad('maps/%s/image.png' % self.map)
        background2 = imgLoad('maps/%s/image2.png' % self.map).convert_alpha()
        background3 = imgLoad('maps/%s/image3.png' % self.map).convert_alpha()
        for i in range(len(self.targets)-1):
            pygame.draw.line(background,(0,0,0),self.targets[i],self.targets[i+1])

        return background,background2,background3

mapvar = Map()



class Enemy:
    layers = [ # Name Health Speed CashReward
        ('red',      1, 1.0, 0),
        # ('Name'   Health, Speed, CashReward),
        ('darkblue', 1, 1.0, 0),
        ('green',    1, 1.2, 0),
        ('yellow',   1, 2.0, 0),]

    # initalize enemy
    def __init__(self,layer):
        self.layer = layer
        self.setLayer()
        self.targets = mapvar.targets
        self.pos = list(self.targets[0])
        self.target = 0
        self.next_target()
        self.rect = self.image.get_rect(center=self.pos)
        self.distance = 0
        enemyList.append(self)

    def setLayer(self): self.name,self.health,self.speed,self.cashprize = self.layers[self.layer]; self.image = EnemyImageArray[self.name]
    def nextLayer(self): self.layer-=1; self.setLayer()

    def next_target(self):
        # check if bloons reached the ending
        if self.target<len(self.targets)-1:
            self.target+=1; t=self.targets[self.target]; self.angle = 180-(math.atan2(t[0]-self.pos[0],t[1]-self.pos[1]))/(math.pi/180)
            self.vx,self.vy = math.sin(math.radians(self.angle)),-math.cos(math.radians(self.angle))
        # end game / player if so (no health)
        else: self.kill(); player.health -= (self.layer+1)

    def hit(self,damage):
        player.money+=1
        self.health -= damage
        if self.health<=0:
            player.money+=self.cashprize
            self.nextLayer() if self.layer>0 else self.kill()

    def kill(self): enemyList.remove(self)

    def move(self,frametime):
        speed = frametime*fps*self.speed
        a,b = self.pos,self.targets[self.target]
        
        a[0] += self.vx*speed
        #
        a[1] += self.vy*speed
        
        if (b[0]-a[0])**2+(b[1]-a[1])**2<=speed**2: self.next_target()
        self.rect.center = self.pos
        self.distance+=speed

class Tower:
    def __init__(self,pos):
        self.targetTimer = 0
        self.rect = self.image.get_rect(center=pos)
        towerList.append(self)

    def takeTurn(self,frametime,screen):
        self.startTargetTimer = self.firerate
        self.targetTimer -= frametime
        if self.targetTimer<=0:
            enemypoint = self.target()
            if enemypoint:
                pygame.draw.line(screen,(255,255,255),self.rect.center,enemypoint)
                self.targetTimer=self.startTargetTimer
    def target(self):
        # for each enemy loop
        for enemy in sorted(enemyList,key=lambda i: i.distance,reverse=True):
            if (self.rect.centerx-enemy.rect.centerx)**2+(self.rect.centery-enemy.rect.centery)**2<=self.rangesq:
                self.angle = int(get_angle(self.rect.center,enemy.rect.center))
                self.image = pygame.transform.rotate(self.imagecopy,-self.angle)
                self.rect = self.image.get_rect(center=self.rect.center)
                enemy.hit(self.damage)
                return enemy.rect.center

class createTower(Tower):
    # generate the tower
    def __init__(self,tower,pos,info):
        self.tower = tower
        self.cost,self.firerate,self.range,self.damage = info
        self.rangesq = self.range**2

        # set properties (damage, firerate, range)
        
        self.image = TowerImageArray[tower]
        self.imagecopy = self.image.copy()
        self.angle = 0
        Tower.__init__(self,pos)

class Icon:
    # adjust icons of the towers here
    towers = { # Cost Fire Rate Range Damage
        'Dart Monkey'         : [ 215, 1.3, 100, 1],
        # [ Cost, Fire Rate, Range, Damage]
        'Tack Shooter'        : [ 390, 1.0, 70, 1],
        'Sniper Monkey'       : [ 430, 2.9, 300, 2],
        'Boomerang Thrower'   : [ 430, 1.0, 90, 1],
        'Ninja Monkey'        : [ 650, 1.0, 90, 1],
        'Bomb Tower'          : [ 700, 1, 90, 2],
        'Ice Tower'           : [ 410, 1.3, 90, 1],
        'Glue Gunner'         : [ 325, 1.1, 100, 1],
        'Monkey Buccaneer'    : [ 650, 0.99, 100, 1],
        'Super Monkey'        : [ 3000, 0.15, 200, 1],
        'Monkey Apprentice'   : [ 595, 1.0, 60, 1],
        'Spike Factory'       : [ 650, 2.0, 40, 1],
        'Road Spikes'         : [  30, 5.0, 40, 1],
        'Exploding Pineapple' : [  25, 2.0, 60, 1],}
    # based off the official 2011 Ninja Kiwi game

    def __init__(self,tower):
        # initalize tower and it's properties
        self.tower = tower
        self.cost,self.firerate,self.range,self.damage = self.towers[tower]
        iconList.append(self)
        self.img = pygame.transform.scale(TowerImageArray[tower],(41,41))
        i = player.towers.index(tower); x,y = i%2,i//2
        self.rect = self.img.get_rect(x=700+x*(41+6)+6,y=100+y*(41+6)+6)


def dispText(screen,wavenum):
    #font = pygame.font.Font('C:/Windows/Fonts/ARCHRISTY.ttf',18)
    font = pygame.font.SysFont('arial', 18)
    # Feel free to change the font here
    h = font.get_height()+2
    strings = [('Round: %d/%d' % (wavenum,len(mapvar.waves)),(200,20)),
               (str(player.money),(730,15)),
               # adjust player values here
               (str(max(player.health,0)),(730,45))]
               # set player health
    for string,pos in strings:
        text = font.render(string,2,(0,0,0))
        screen.blit(text,text.get_rect(midleft=pos))

# https://realpython.com/lessons/using-blit-and-flip/

# Block Transfer, and .blit() is how you copy the contents of one Surface to another
def drawTower(screen,tower,selected):
    screen.blit(tower.image,tower.rect)
    if tower == selected:
        rn = tower.range
        surface = pygame.Surface((2*rn,2*rn)).convert_alpha(); surface.fill((0,0,0,0))
        pygame.draw.circle(surface,(0,255,0,85),(rn,rn),rn)
        screen.blit(surface,tower.rect.move((-1*rn,-1*rn)).center)

    elif tower.rect.collidepoint(pygame.mouse.get_pos()):
        rn = tower.range
        surface = pygame.Surface((2*rn,2*rn)).convert_alpha(); surface.fill((0,0,0,0))
        pygame.draw.circle(surface,(255,255,255,85),(rn,rn),rn)
        screen.blit(surface,tower.rect.move((-1*rn,-1*rn)).center)

def selectedIcon(screen,selected):

    mpos = pygame.mouse.get_pos()
    # using active mouse position
    image = TowerImageArray[selected.tower]
    rect = image.get_rect(center=mpos)
    screen.blit(image,rect)

    collide = False
    rn = selected.range
    surface = pygame.Surface((2*rn,2*rn)).convert_alpha(); surface.fill((0,0,0,0))
    pygame.draw.circle(surface,(255,0,0,75) if collide else (0,0,255,75),(rn,rn),rn)
    screen.blit(surface,surface.get_rect(center=mpos))

def selectedTower(screen,selected,mousepos):

    selected.genButtons(screen)

    for img,rect,info,infopos,cb in selected.buttonlist:
        screen.blit(img,rect)
        if rect.collidepoint(mousepos): screen.blit(info,infopos)

def drawIcon(screen,icon,mpos,font):
    screen.blit(icon.img,icon.rect)

    if icon.rect.collidepoint(mpos):
        text = font.render("%s Tower (%d)" % (icon.tower,icon.cost),2,(0,0,0))
        textpos = text.get_rect(right=700-6,centery=icon.rect.centery)
        screen.blit(text,textpos)

class Sender:
    def __init__(self,wave):
        self.wave = wave; self.timer = 0; self.rate = 1
        self.enemies = []; enemies = mapvar.waves[wave-1].split(',')
        for enemy in enemies:
            amount,layer = enemy.split('*')
            self.enemies += [eval(layer)-1]*eval(amount)
        senderList.append(self)

    def update(self,frametime,wave):
        if not self.enemies:
            if not enemyList: senderList.remove(self); wave+=1; player.money+=99+self.wave
        elif self.timer > 0: self.timer -= frametime
        else: self.timer = self.rate; Enemy(self.enemies[0]); del self.enemies[0]
        return wave

def workEvents(selected,wave,speed):
    for event in pygame.event.get():
        if event.type == pygame.QUIT: pygame.quit(); sys.exit()
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 3: selected = None
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:

            if selected in towerList: selected = None
            elif selected in iconList:
                if player.money>=selected.cost:
                    rect = selected.img.get_rect(center=event.pos)
                    collide = False
                    if not collide: player.money-=selected.cost; selected = createTower(selected.tower,event.pos,selected.towers[selected.tower])

            for obj in iconList + (towerList if not selected else []):
                if obj.rect.collidepoint(event.pos): selected = obj; break

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and not enemyList:
                if wave<=len(mapvar.waves): Sender(wave)
                else: print('Congratulations!! You survived the swarm')

            if event.key == pygame.K_k and selected in towerList: player.money+=int(selected.cost*0.9); towerList.remove(selected); selected = None
            if event.key == pygame.K_w and speed<10: speed+=1
            if event.key == pygame.K_s and speed>1: speed-=1
    return selected,wave,speed

# main file
def main():
    pygame.init()
    # https://www.pygame.org/docs/ref/pygame.html

    os.environ['SDL_VIDEO_CENTERED'] = '1'
    pygame.display.set_caption('Bloons Tower Defence')
    screen = pygame.display.set_mode((screenWidth,screenHeight))
    clock = pygame.time.Clock()
    font = pygame.font.Font(None,20)

    mapvar.getmovelist()

    background = pygame.Surface((800,600)); background.set_colorkey((0,0,0))
    # load values of heart (lives), money (cash to spend), and plank interface
    heart,money,plank = imgLoad('images/hearts.png'),imgLoad('images/moneySign.png'),imgLoad('images/plankBlank.png')
    w,h = plank.get_size()
    for y in range(screenHeight//h): background.blit(plank,(screenWidth-w,y*h))
    for y in range(3):
        for x in range(screenWidth//w): background.blit(plank,(x*w,screenHeight-(y+1)*h))
    background.blit(money,(screenWidth-w+6,h//2-money.get_height()//2))
    background.blit(heart,(screenWidth-w+6,h+h//2-heart.get_height()//2))
    
    level_img,t1,t2 = mapvar.get_background()
    loadImages()
    for tower in player.towers: Icon(tower)
    selected = None
    speed = 3
    wave = 1
    # optional music
    play_music('music/maintheme.mp3')
    # application running
    while True:
        starttime = time.time()
        clock.tick(fps)
        frametime = (time.time()-starttime)*speed
        screen.blit(level_img,(0,0))
        mpos = pygame.mouse.get_pos()

        if senderList: wave = senderList[0].update(frametime,wave)

        z0,z1 = [],[]
        for enemy in enemyList:
            d = enemy.distance
            if d<580: z1+=[enemy]
            elif d<950: z0+=[enemy]
            elif d<2392: z1+=[enemy]
            elif d<2580: z0+=[enemy]
            else: z0+=[enemy]

        for enemy in z0: enemy.move(frametime); screen.blit(enemy.image,enemy.rect)
        screen.blit(t1,(0,0))
        screen.blit(t2,(0,0))
        for enemy in z1: enemy.move(frametime); screen.blit(enemy.image,enemy.rect)

        for tower in towerList: tower.takeTurn(frametime,screen); drawTower(screen,tower,selected)


        screen.blit(background,(0,0))

        for icon in iconList: drawIcon(screen,icon,mpos,font)
        selected,wave,speed = workEvents(selected,wave,speed)
        if selected and selected.__class__ == Icon: selectedIcon(screen,selected)
        dispText(screen,wave)

        pygame.display.flip()

if __name__ == '__main__':
    main()




