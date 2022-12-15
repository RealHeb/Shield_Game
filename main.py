import pygame
import math
import random as rad
import time


class Entity(pygame.sprite.Sprite):
    def __init__(self, camera, x, y, x_indent, y_indent, hp, speed, image):
        '''x_intent means what indent x/y intent hitbox will have (from both sides)'''
        super().__init__(camera)
        self.image = pygame.image.load(image).convert_alpha()
        self.rect = self.image.get_rect(center=(x, y))
        self.hitbox_x1, self.hitbox_y1 = self.rect.topleft
        self.hitbox_x1, self.hitbox_y1 = self.hitbox_x1 + x_indent, self.hitbox_y1 + y_indent
        self.hitbox_width = self.rect.w - x_indent * 2
        self.hitbox_height = self.rect.h - y_indent * 2
        self.hitbox = pygame.Rect(self.hitbox_x1, self.hitbox_y1, self.hitbox_width, self.hitbox_height)
        self.x_indent = x_indent
        self.y_indent = y_indent
        self.hp = hp
        self.speed = speed
        self.last_moved = time.time()
        self.direction = pygame.math.Vector2()
        self.dead = False

    def get_damage(self, amount):
        self.hp -= amount
        if self.hp <= 0:
            self.dead = True


class StaticObject(Entity):
    def __init__(self, camera, x, y, hp, image, x_indent=0, y_indent=0, direction=-1):
        self.direction = direction
        '''-2 = left, -1 = up, 0 = none, 1 = right, 2 = down'''
        if direction != 0:
            if direction % 2 == 0:
                pass
        super().__init__(camera, x, y, x_indent, y_indent, hp, 0, image)



'''Можно оставить создание пуль оружию, которое будет добавлять им скорость, разброс и урон'''
pygame.init()
window = pygame.display.set_mode((500, 500))
clock = pygame.time.Clock()

movement_delay = 0.02


class CameraGroup(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        self.colliding_objects = []
        self.surface1 = pygame.display.get_surface()
        self.ground_surf = pygame.image.load('background.png').convert_alpha()
        self.ground_rect = self.ground_surf.get_rect(topleft=(0, 0))
        self.offset = pygame.math.Vector2()
        self.half_w = self.surface1.get_size()[0] // 2
        self.half_h = self.surface1.get_size()[1] // 2
        self.dead = False

    def center_target_camera(self, target):
        self.offset.x = target.rect.centerx - self.half_w
        self.offset.y = target.rect.centery - self.half_h

    def camera_draw(self, player):
        self.center_target_camera(player)
        ground_offset = self.ground_rect.topleft - self.offset
        self.surface1.blit(self.ground_surf, ground_offset)
        sorted_sprites = sorted(self.sprites(), key=lambda x: x.rect.bottomleft[1])
        for sprite in sorted_sprites:
            if sprite.dead == True:
                self.remove(sprite)
                if sprite in self.colliding_objects:
                    self.colliding_objects.remove(sprite)
                continue
            if type(sprite) == StaticObject:
                if sprite not in self.colliding_objects:
                    self.colliding_objects.append(sprite)
                for bullet in gun.bullets:
                    if sprite.rect.colliderect(bullet.rect):
                        sprite.get_damage(bullet.damage)
                        bullet.dead = True

            offset_pos = sprite.rect.topleft - self.offset
            self.surface1.blit(sprite.image, offset_pos)


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, dir1, angle, damage, speed, surf, range1=1000, bullet_image='bullet.jpg'):
        self.surf = surf
        self.pos = (x, y)
        self.start_pos = (x, y)
        self.render_priority = 1
        global camera
        super().__init__(surf)
        dir1 = (dir1[0] + rad.uniform(-0.15, 0.15), dir1[1] + rad.uniform(-0.15, 0.15))
        self.dir = dir1
        self.range = range1 + rad.randint(-25, 100)
        self.damage = damage
        self.speed = speed
        self.image = pygame.image.load(bullet_image)
        self.rect = self.image.get_rect(center=(x, y))
        self.base_image = pygame.image.load(bullet_image)
        self.base_rect = self.base_image.get_rect(center=(x, y))
        self.dead = False
        self.image, nothing = rot_center(self.base_image, self.base_rect, angle)

    def update(self):
        self.pos = (self.pos[0] + self.dir[0] * self.speed,
                    self.pos[1] + self.dir[1] * self.speed)
        self.rect = self.base_image.get_rect(center=(self.pos[0], self.pos[1]))

    def check(self):
        x1, y1 = self.start_pos
        x2, y2 = self.pos
        len_of_line = ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5
        if len_of_line > self.range:
            self.dead = True


class Player(Entity):
    def __init__(self, camera, image, x_indent=0, y_indent=0, x=250, y=250, hp=100, speed=5):
        super().__init__(camera, x, y, x_indent, y_indent, hp, speed, image)

    def move(self):
        global movement_delay
        self.analyze_input()
        if time.time() - self.last_moved > movement_delay:
            self.hitbox.center += self.direction * self.speed
            for object1 in camera.colliding_objects:
                if object1.rect.colliderect(self.hitbox):
                    self.hitbox.center -= self.direction * self.speed
                    print(object1.hitbox, '  |||||  ', object1.rect)
                    return
            self.rect.center += self.direction * self.speed

    def analyze_input(self):
        key = pygame.key.get_pressed()
        if key[pygame.K_w]:
            self.direction.y = -1
        elif key[pygame.K_s]:
            self.direction.y = 1
        else:
            self.direction.y = 0

        if key[pygame.K_a]:
            self.direction.x = -1
        elif key[pygame.K_d]:
            self.direction.x = 1
        else:
            self.direction.x = 0


class Gun(pygame.sprite.Sprite):
    def __init__(self, who_is_holding, shot_delay, bullets_per_shot, damage, speed, drop, surf, range1=1000,
                 gun_image='pixel_minigun.png', bullet_image='bullet.jpg'):
        ''' adj_x/y_1 is cosmetic stat, for proper display of weapon, adj_x/y_2 is a cosmetic stat for
        proper positioningof a bullet spawning place '''
        super().__init__(surf)
        x, y = who_is_holding.rect.center
        self.who_is_holding = who_is_holding
        self.bullet_image = bullet_image
        self.reversed = False
        self.base_image = pygame.image.load(gun_image).convert_alpha()
        self.base_rect = self.base_image.get_rect(center=(x, y))
        self.shoot = False
        self.range1 = range1
        self.bullets_per_shot = bullets_per_shot
        self.shot_delay = shot_delay
        self.last_shot = time.time()
        self.drop = drop
        self.range1 = range1
        self.damage = damage
        self.speed = speed
        self.surf = surf
        self.bullets = []
        self.image = pygame.image.load(gun_image).convert_alpha()
        self.rect = self.image.get_rect(center=(x, y))
        self.dead = False

    def create_bullet(self, x, y):
        global camera
        camerax, cameray = camera.offset[0], camera.offset[1]
        mx, my = pygame.mouse.get_pos()
        x += 20
        mx, my = mx + camerax, my + cameray
        self.dir1 = (mx - x, my - y)
        length = math.hypot(*self.dir1)
        if length == 0.0:
            self.dir1 = 0, -1
        else:
            self.dir1 = (self.dir1[0] / length, self.dir1[1] / length)
        bullet_dir = (self.dir1[0] + rad.uniform(-self.drop, self.drop), self.dir1[1] + rad.uniform(-self.drop, self.drop))
        bullet = Bullet(x, y, bullet_dir, self.angle, self.damage, self.speed, self.surf, self.range1, self.bullet_image)
        self.bullets.append(bullet)

    def update(self):
        global camera
        camerax, cameray = camera.offset[0], camera.offset[1]
        x, y = self.who_is_holding.rect.center
        mx, my = pygame.mouse.get_pos()
        mx, my = mx + camerax, my + cameray
        self.dir1 = (mx - x, my - y)
        length = math.hypot(*self.dir1)
        if length == 0.0:
            self.dir1 = 0, -1
        else:
            self.dir1 = (self.dir1[0] / length, self.dir1[1] / length)
        self.angle = math.degrees(math.atan2(-self.dir1[1], self.dir1[0]))
        x, y = self.who_is_holding.rect.center
        if self.shoot:
            if time.time() - self.last_shot > self.shot_delay:
                x2 = x + self.dir1[0] * 20 - 20
                y2 = y + self.dir1[1] * 25 - 3
                for i in range(self.bullets_per_shot):
                    self.create_bullet(x2, y2)
                    self.last_shot = time.time()
        for bullet in self.bullets[:]:
            bullet.check()
            if bullet.dead:
                self.bullets.remove(bullet)
        if self.angle < -90.0 or self.angle > 90.0:
            self.reversed = True
        else:
            self.reversed = False
        self.image, self.rect = rot_center(self.base_image, self.base_rect, self.angle, self.reversed)
        self.rect = self.image.get_rect(center=(x, y + 1))


    def if_shooting(self):
        if time.time() - self.last_shot > self.shot_delay:
            if pygame.mouse.get_pressed()[0]:
                self.shoot = True
            else:
                self.shoot = False


class Particle(pygame.sprite.Sprite):
    def __init__(self, x, y, image='boom-boom.png', lifetime=20):
        global camera
        super().__init__(camera)
        self.base_image = pygame.image.load(image).convert_alpha()
        self.base_rect = self.base_image.get_rect(center=(x, y))
        self.lifetime = lifetime
        self.dead = False

    def update(self):
        self.lifetime -= 1
        if self.lifetime < 0:
            self.dead = True


def rot_center(image, rect, angle, flip=False):
    rot_image = pygame.transform.rotate(image, angle)
    if flip:
        rot_image = pygame.transform.rotate(image, 180 - angle)
        rot_image = pygame.transform.flip(rot_image, 180, 0)
    rot_rect = rot_image.get_rect(center=rect.center)
    return rot_image, rot_rect


''' Team - Отвечает за то, в кого будут стрелять, потом на этом параметре будут строиться приоритеты стрельбы, также
отвечает за то, какие пули 'дружелюбны'.'''
run = True
bullets = []
shot_delay = 0.5
camera = CameraGroup()
gun_image = 'Flamethrower.png'
bullet_image = 'Flamethrower_particle.png'
images = ['Barrel.jpg', 'Barrels.png']
player_image = 'pixilart-drawing.png'
player = Player(camera, player_image, y_indent=20)
bullets_per_shot = 7
damage = 1000
speed = 7
'''drop - acceptable numbers <= 0.3, anything more is questionable, more than 1 is straight up wrong'''
drop = 0.1
range1 = 500

for i in range(20):
    random_x = rad.randint(0, 1000)
    random_y = rad.randint(0, 1000)
    StaticObject(camera, random_x, random_y, 300, images[i % 2], y_indent=20)
shotgun = Gun(player, 0.5, 6, 50, 7, 0.1, camera, 100, 'shotgun.png', 'shotgun_bullet.png')
gun_list = [shotgun]
gun = gun_list[rad.randint(0, len(gun_list) - 1)]


while run:
    clock.tick(60)
    player.move()
    gun.if_shooting()
    gun.update()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

    window.fill(0)
    camera.update()

    camera.camera_draw(player)
    pygame.display.flip()
