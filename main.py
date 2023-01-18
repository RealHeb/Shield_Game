import math
import os
import pygame
import random as rad
import sys
import time


class Entity(pygame.sprite.Sprite):
    def __init__(self, camera, x, y, x_indent=0, y_indent=0, hp=100, speed=7, image=''):
        '''x_intent means what indent x/y hitbox will have (from both sides)'''
        super().__init__(camera)
        self.image = load_image(image)
        self.rect = self.image.get_rect(topleft=(x, y))
        camera.colliding_objects.append(self)
        self.hitbox_x1, self.hitbox_y1 = self.rect.topleft
        self.hitbox_x1, self.hitbox_y1 = self.hitbox_x1 + x_indent, self.hitbox_y1 + y_indent
        self.hitbox_width = self.rect.w - x_indent * 2
        self.hitbox_height = self.rect.h - y_indent * 2
        self.hitbox = pygame.Rect(self.hitbox_x1, self.hitbox_y1, self.hitbox_width, self.hitbox_height)
        self.x_indent = x_indent
        self.y_indent = y_indent
        if day_count != 0:
            self.hp = hp * day_count
        else:
            self.hp = hp
        self.speed = speed
        self.last_moved = time.time()
        self.direction = pygame.math.Vector2()
        self.dead = False

    def get_damage(self, amount):
        self.hp -= amount
        if self.hp <= 0:
            self.dead = True


class Tile(pygame.sprite.Sprite):
    def __init__(self, tile_type, pos_x, pos_y, custom_image=''):
        global camera, tiles
        if custom_image == '':
            self.image = tile_images[tile_type]
        else:
            self.image = load_image(custom_image)
        self.dead = False
        self.rect = self.image.get_rect(center=(tile_width * pos_x, tile_height * pos_y))
        if tile_type == 'wall':
            self.hitbox = self.rect
            self.hitbox_x1, self.hitbox_y1 = self.rect.topleft
            self.hitbox_x1, self.hitbox_y1 = self.hitbox_x1, self.hitbox_y1 + 15
            self.hitbox_width = self.rect.w
            self.hitbox_height = self.rect.h - 30
            self.hitbox = pygame.Rect(self.hitbox_x1, self.hitbox_y1, self.hitbox_width, self.hitbox_height)
            super().__init__(camera)
            camera.colliding_objects.append(self)
            self.team = 0
        else:
            super().__init__()
            camera.floor_tile_group.append(self)


class StaticObject(Entity):
    def __init__(self, camera, x, y, hp=100, image='Barrel.jpg', x_indent=0, y_indent=17, direction=-1):
        self.direction = direction
        self.team = 3
        super().__init__(camera, x, y, x_indent, y_indent, hp, 0, image)


pygame.init()
key_up = True
scale = (800, 600)
window = pygame.display.set_mode(scale)
clock = pygame.time.Clock()
day_count = 0
lvl_count = 0
movement_delay = 0.02


class CameraGroup(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        self.safe = True
        self.gun_group = []
        self.colliding_objects = []
        self.floor_tile_group = []
        self.surface1 = pygame.display.get_surface()
        self.ground_surf = load_image('background.png')
        self.ground_rect = self.ground_surf.get_rect(topleft=(0, 0))
        self.offset = pygame.math.Vector2()
        self.half_w = self.surface1.get_size()[0] // 2
        self.half_h = self.surface1.get_size()[1] // 2
        self.dead = False
        self.display_surface = pygame.display.get_surface()
        self.keyboard_speed = 5
        self.mouse_speed = 0.5

    def mouse_control(self, target):
        mouse = pygame.math.Vector2(pygame.mouse.get_pos())
        mouse_offset_vector = pygame.math.Vector2()
        self.offset.x = target.rect.centerx - self.half_w
        self.offset.y = target.rect.centery - self.half_h
        self.camera_borders = {'left': 401, 'right': 401, 'top': 301, 'bottom': 301}
        l = self.camera_borders['left']
        t = self.camera_borders['top']
        w = self.display_surface.get_size()[0] - (self.camera_borders['left'] + self.camera_borders['right'])
        h = self.display_surface.get_size()[1] - (self.camera_borders['top'] + self.camera_borders['bottom'])
        self.camera_rect = pygame.Rect(l, t, w, h)
        self.zoom_scale = 1
        self.internal_surf_size = (2500, 2500)
        self.internal_surf = pygame.Surface(self.internal_surf_size, pygame.SRCALPHA)
        self.internal_rect = self.internal_surf.get_rect(center=(self.half_w, self.half_h))
        self.internal_surface_size_vector = pygame.math.Vector2(self.internal_surf_size)
        self.internal_offset = pygame.math.Vector2()
        self.internal_offset.x = self.internal_surf_size[0] // 2 - self.half_w
        self.internal_offset.y = self.internal_surf_size[1] // 2 - self.half_h
        left_border = self.camera_borders['left']
        top_border = self.camera_borders['top']
        right_border = self.display_surface.get_size()[0] - self.camera_borders['right']
        bottom_border = self.display_surface.get_size()[1] - self.camera_borders['bottom']

        if mouse.y < top_border and not top_border < mouse.y < bottom_border:
            if mouse.x < left_border:
                mouse_offset_vector = mouse - pygame.math.Vector2(left_border, top_border)
            if mouse.x > right_border:
                mouse_offset_vector = mouse - pygame.math.Vector2(right_border, top_border)
        elif mouse.y > bottom_border:
            if mouse.x < left_border:
                mouse_offset_vector = mouse - pygame.math.Vector2(left_border, bottom_border)
            if mouse.x > right_border:
                mouse_offset_vector = mouse - pygame.math.Vector2(right_border, bottom_border)
        self.offset += mouse_offset_vector * self.mouse_speed

    def center_target_camera(self, target):
        self.offset.x = target.rect.centerx - self.half_w
        self.offset.y = target.rect.centery - self.half_h

    def camera_draw(self, player):
        global key_up

        self.mouse_control(player)
        for tile in self.floor_tile_group:
            offset_pos = tile.rect.topleft - self.offset
            self.surface1.blit(tile.image, offset_pos)

        sorted_sprites = sorted(self.sprites(), key=lambda x: x.rect.topleft[1])
        for sprite in sorted_sprites:
            if sprite.dead is True and type(sprite) != Gun and type(sprite) != Shield:
                self.remove(sprite)
                if sprite in self.gun_group:
                    self.gun_group.remove(sprite)
                if sprite in self.colliding_objects:
                    self.colliding_objects.remove(sprite)
                if sprite in ALL_bullets:
                    ALL_bullets.remove(sprite)
                continue
            if sprite in self.colliding_objects:
                for bullet in ALL_bullets:
                    if sprite.rect.colliderect(bullet.rect):
                        if bullet.team != sprite.team and sprite.team != -1 and bullet.team != 0:
                            if sprite.team != 0 and not (sprite == player and type(gun) == Shield):
                                sprite.get_damage(bullet.damage)
                            else:
                                if type(sprite) == Player:
                                    if rad.randint(0, 4) == 1:
                                        sprite.get_damage(bullet.damage)
                                create_reflection_bullets(sprite.rect.centerx, sprite.rect.centery, bullet)
                            bullet.dead = True
                            ALL_bullets.remove(bullet)

                if type(sprite) == Door:
                    if sprite.rect.colliderect(player.rect):

                        self.colliding_objects.clear()
                        self.floor_tile_group.clear()
                        self.gun_group.clear()
                        labels.clear()
                        ALL_bullets.clear()
                        for i in self:
                            i.dead = True
                        global day_count, lvl_count, safe
                        if self.safe:
                            day_count += 1
                        else:
                            lvl_count += 1
                        self.offset.x, self.offset.y = 0, 0
                        global player1
                        if sprite.safe:
                            lvl_count -= 2
                            self.safe = True
                            if day_count == 0:
                                player1 = generate_level(load_level('safe_base.txt'))
                            elif day_count == 1:
                                player1 = generate_level(load_level('safe_base1.txt'))
                            elif day_count == 2:
                                player1 = generate_level(load_level('safe_base2.txt'))
                            elif day_count == 3:
                                player1 = generate_level(load_level('safe_base3.txt'))
                            elif day_count >= 4:
                                player1 = generate_level(load_level('safe_base4.txt'))

                            gun.who_is_holding = player1
                        else:
                            key_up = False
                            self.safe = False
                            player1 = generate_level(generate_random_lvl_layout())
                            gun.who_is_holding = player1
            offset_pos = sprite.rect.topleft - self.offset
            self.surface1.blit(sprite.image, offset_pos)
        for gun1 in self.gun_group:
            offset_pos = gun1.rect.topleft - self.offset
            self.surface1.blit(gun1.image, offset_pos)
        offset_pos = EPICSHIELD.rect.topleft - self.offset
        self.surface1.blit(EPICSHIELD.image, offset_pos)


class Enemy(Entity):
    def __init__(self, x, y, gun):
        super().__init__(camera, x, y, image='enemy.png')
        self.team = 2
        self.gun = gun
        self.x, self.y = x, y
        self.dead = False
        self.speed = 2

    def update(self):
        global player
        global movement_delay

        if time.time() - self.last_moved > movement_delay:
            pass
        move = [0, 0]
        social_distance = 400
        Px, Py = player1.rect.center
        if ((Px - self.x) ** 2 + (Py - self.y) ** 2) ** 0.5 < 100:

            len_by_x = abs(Px - self.x) < 100
            len_by_y = abs(Py - self.y) < 100
            if Px <= self.x and len_by_x:
                move[0] = self.speed
            elif Px >= self.x and len_by_x:
                move[0] = -self.speed

            if Py <= self.y and len_by_y:
                move[1] = self.speed
                self.gun.shoot = False
            elif Py >= self.y and len_by_y:
                self.gun.shoot = False
                move[1] = -self.speed
            hitbox_x_y = self.image.get_rect(center=(self.x + move[0], self.y + move[1]))
            hitbox_x = self.image.get_rect(center=(self.x + move[0], self.y))
            hitbox_y = self.image.get_rect(center=(self.x, self.y + move[1]))
            x_y, just_x, just_y = True, True, True
            for object1 in camera.colliding_objects:
                if object1.hitbox.colliderect(hitbox_x_y):
                    if object1 != self and type(object1) != PickableObject:
                        x_y = False
                    if object1.hitbox.colliderect(hitbox_x):
                        if object1 != self:
                            just_x = False
                    if object1.hitbox.colliderect(hitbox_y):
                        if object1 != self and type(object1) != PickableObject:
                            just_y = False
            if x_y:
                self.hitbox = hitbox_x_y
            else:
                if just_x and just_y:
                    if len_by_y < len_by_x:
                        self.hitbox = hitbox_y
                    else:
                        self.hitbox = hitbox_x
                if just_x:
                    self.hitbox = hitbox_x
                if just_y:
                    self.hitbox = hitbox_y
            self.rect = self.hitbox
            self.x, self.y = self.rect.center
        elif ((Px - self.x) ** 2 + (Py - self.y) ** 2) ** 0.5 > social_distance:
            len_by_x = abs(Px - self.x) > social_distance // 2
            len_by_y = abs(Py - self.y) < social_distance // 2
            if Px <= self.x and len_by_x:
                move[0] = -self.speed
            elif Px >= self.x and len_by_x:
                move[0] = self.speed

            if Py <= self.y and len_by_y:
                move[1] = -self.speed

            elif Py >= self.y and len_by_y:
                move[1] = self.speed
            hitbox_x_y = self.image.get_rect(center=(self.x + move[0], self.y + move[1]))
            hitbox_x = self.image.get_rect(center=(self.x + move[0], self.y))
            hitbox_y = self.image.get_rect(center=(self.x, self.y + move[1]))
            x_y, just_x, just_y = True, True, True
            for object1 in camera.colliding_objects:
                if object1.hitbox.colliderect(hitbox_x_y):
                    if object1 != self:
                        x_y = False
                    if object1.hitbox.colliderect(hitbox_x):
                        if object1 != self and type(object1) != PickableObject:
                            just_x = False
                    if object1.hitbox.colliderect(hitbox_y):
                        if object1 != self and type(object1) != PickableObject:
                            just_y = False
            if x_y:
                self.hitbox = hitbox_x_y
            else:
                if just_x and just_y:
                    if len_by_y > len_by_x:
                        self.hitbox = hitbox_y
                    else:
                        self.hitbox = hitbox_x
                if just_x:
                    self.hitbox = hitbox_x
                if just_y:
                    self.hitbox = hitbox_y
            self.rect = self.hitbox
            self.x, self.y = self.rect.center
        else:
            self.gun.shoot = True


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, dir1, angle, damage, speed, surf, team=-1,
                 range1=1000, bullet_image='bullet.jpg', drop=0.15):
        self.surf = surf
        self.team = team
        self.pos = (x, y)
        self.start_pos = (x, y)
        global camera
        super().__init__(surf)
        dir1 = (dir1[0] + rad.uniform(drop, drop), dir1[1] + rad.uniform(-drop, drop))
        self.dir = dir1
        self.range = range1 + rad.randint(-25, 100)
        self.damage = damage
        self.speed = speed
        self.image = load_image(bullet_image)
        self.rect = self.image.get_rect(center=(x, y))
        self.base_image = load_image(bullet_image)
        self.base_rect = self.base_image.get_rect(center=(x, y))
        self.dead = False
        self.image, nothing = rot_center(self.base_image, self.base_rect, angle)

    def update(self):
        self.check()
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
    def __init__(self, x_indent=0, y_indent=0, x=250, y=250, speed=8):
        global camera, health
        self.team = 1
        self.sprite_id = 0
        self.images = ['player_still.png', 'player_down.png', 'player_up.png']
        image = self.images[0]
        self.hp = health
        self.last_sprite_update = time.time()
        super().__init__(camera, x, y, x_indent, y_indent, health, speed, image)

    def move(self):
        global movement_delay, player
        self.analyze_input()

        if time.time() - self.last_moved > movement_delay:
            if (self.direction.x != 0 or self.direction.y != 0) and time.time() - self.last_sprite_update > 0.3:
                self.image = load_image(self.images[self.sprite_id])
                self.last_sprite_update = time.time()
                self.sprite_id = (self.sprite_id + 1) % 3
            elif time.time() - self.last_moved > 0.4:
                self.image = load_image(self.images[0])
                self.sprite_id = 0
            self.hitbox.center += self.direction * self.speed
            for object1 in camera.colliding_objects:
                if object1.hitbox.colliderect(self.hitbox):
                    if type(object1) == Player:
                        continue
                    if type(object1) == PickableObject:
                        object1.activate()
                        camera.remove(object1)
                        camera.colliding_objects.remove(object1)
                    if type(object1) == Door:
                        continue
                    if type(object1) == Label:
                        continue
                    if type(object1) == Shield:
                        continue
                    self.hitbox.center -= self.direction * self.speed
                    return
            self.rect.center += self.direction * self.speed
            self.last_moved = time.time()

    def get_damage(self, amount):
        global health
        health -= amount

    def analyze_input(self):
        global gun
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
        if type(gun) == Gun:
            gun.if_shooting()
        if key[pygame.K_1]:
            gun.who_is_holding = uselul
            gun = weapons[0]
            gun.who_is_holding = self
            gun.team = self.team
        if key[pygame.K_2] and len(weapons) >= 2:
            gun.who_is_holding = uselul
            gun = weapons[1]
            gun.who_is_holding = self
            gun.team = self.team
        if key[pygame.K_3] and len(weapons) == 3:
            gun.who_is_holding = uselul
            gun = weapons[2]
            gun.who_is_holding = self
            gun.team = self.team
        if key[pygame.K_4]:
            gun.who_is_holding = uselul
            gun = EPICSHIELD
            EPICSHIELD.who_is_holding = self

    def health_and_ammo(self):
        global health
        text = ['',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                f'           Здоровье: {health}',
                f'           Патроны: {gun.ammo}',
                f'           Запчасти {scrap}']
        text_coord = 310
        for line in text:
            string_rendered = pygame.font.Font(None, 30).render(line, True, pygame.Color('green'))
            rect = string_rendered.get_rect()
            rect.top = text_coord
            rect.x = 10
            text_coord += rect.height
            window.blit(string_rendered, rect)


class Gun(pygame.sprite.Sprite):
    def __init__(self, who_is_holding, shot_delay, bullets_per_shot, damage, speed, drop, surf, range1=1000,
                 gun_image='pixel_minigun.png', bullet_image='bullet.jpg',
                 reloadtime=0, per_burst=1, ammo=80, x_indent=0):
        super().__init__(camera)
        self.ammo = ammo
        x, y = who_is_holding.rect.center

        x -= x_indent
        y -= 1
        camera.gun_group.append(self)
        self.who_is_holding = who_is_holding
        self.bullet_image = bullet_image
        self.team = who_is_holding.team
        self.reversed = False
        self.reload_time = reloadtime
        self.per_burst = per_burst
        self.base_image = load_image(gun_image).convert_alpha()
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
        self.x_indent = x_indent
        self.image = load_image(gun_image).convert_alpha()
        self.rect = self.image.get_rect(center=(x, y))
        self.dead = False
        self.bullets_shot = 0
        self.last_burst = time.time()

    def create_bullet(self, x, y):
        global camera
        camerax, cameray = camera.offset[0], camera.offset[1]
        mx, my = pygame.mouse.get_pos()
        x += 20 - self.x_indent
        mx, my = mx + camerax, my + cameray
        self.dir1 = (mx - x, my - y)
        length = math.hypot(*self.dir1)
        if length == 0.0:
            self.dir1 = 0, -1
        else:
            self.dir1 = (self.dir1[0] / length, self.dir1[1] / length)
        bullet_dir = (self.dir1[0] + rad.uniform(-self.drop, self.drop),
                      self.dir1[1] + rad.uniform(-self.drop, self.drop))
        bullet = Bullet(x, y, bullet_dir, self.angle, self.damage, self.speed, self.surf, self.team, self.range1,
                        self.bullet_image, self.drop)
        ALL_bullets.append(bullet)

    def update(self):
        global camera
        self.who_is_holding.speed = 7
        if self not in camera.gun_group:
            camera.gun_group.append(self)
        self.dead = self.who_is_holding.dead
        camerax, cameray = camera.offset[0], camera.offset[1]
        x, y = self.who_is_holding.rect.center
        x -= self.x_indent
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
        x -= self.x_indent
        if self.shoot:
            if time.time() - self.last_shot > self.shot_delay:
                if time.time() - self.reload_time >= self.last_burst:
                    self.bullets_shot += 1
                    x2 = x + self.dir1[0] * 20 - 20
                    y2 = y + self.dir1[1] * 25
                    if self.ammo > 0:
                        self.ammo -= 1
                        for i in range(self.bullets_per_shot):
                            self.create_bullet(x2, y2)
                            self.last_shot = time.time()
                    if self.bullets_shot % self.per_burst == 0:
                        self.last_burst = time.time()
        if self.angle < -90.0 or self.angle > 90.0:
            self.reversed = True
        else:
            self.reversed = False
        self.image, self.rect = rot_center(self.base_image, self.base_rect, self.angle, self.reversed)
        self.rect = self.image.get_rect(center=(self.who_is_holding.rect.centerx - self.x_indent,
                                                self.who_is_holding.rect.centery))

    def if_shooting(self):
        if time.time() - self.last_shot > self.shot_delay:
            if pygame.mouse.get_pressed()[0]:
                self.shoot = True
            else:
                self.shoot = False


class EnemyGun(Gun):
    def __init__(self, who_is_holding, shot_delay, bullets_per_shot, damage, speed, drop, surf, range1=1000,
                 gun_image='pixel_minigun.png', bullet_image='bullet.jpg', per_burst=3, reloadtime=1):
        super().__init__(who_is_holding, shot_delay, bullets_per_shot, damage, speed, drop, surf, range1,
                         gun_image, bullet_image, reloadtime, per_burst)

    def update(self):
        global camera
        self.dead = self.who_is_holding.dead
        x, y = self.who_is_holding.rect.center
        if self not in camera.gun_group:
            camera.gun_group.append(self)
        mx, my = player1.hitbox.center
        mx, my = mx, my
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
                if time.time() - self.reload_time >= self.last_burst:
                    self.bullets_shot += 1
                    x2 = x + self.dir1[0] * 20 - 20
                    y2 = y + self.dir1[1] * 25
                    if self.ammo > 0:
                        for i in range(self.bullets_per_shot):
                            self.create_bullet(x2, y2)
                            self.last_shot = time.time()
                    if self.bullets_shot % self.per_burst == 0:
                        self.last_burst = time.time()
        if self.angle < -90.0 or self.angle > 90.0:
            self.reversed = True
        else:
            self.reversed = False
        self.image, self.rect = rot_center(self.base_image, self.base_rect, self.angle, self.reversed)
        self.rect = self.image.get_rect(center=(self.who_is_holding.rect.centerx, self.who_is_holding.rect.centery))

    def create_bullet(self, x, y):
        global camera
        mx, my = player1.rect.center
        x += 20
        mx, my = mx, my
        self.dir1 = (mx - x, my - y)
        length = math.hypot(*self.dir1)
        if length == 0.0:
            self.dir1 = 0, -1
        else:
            self.dir1 = (self.dir1[0] / length, self.dir1[1] / length)
        bullet_dir = (self.dir1[0] + rad.uniform(-self.drop, self.drop),
                      self.dir1[1] + rad.uniform(-self.drop, self.drop))
        bullet = Bullet(x, y, bullet_dir, self.angle, self.damage, self.speed, self.surf, 2, self.range1,
                        self.bullet_image, self.drop)
        ALL_bullets.append(bullet)


class Label(pygame.sprite.Sprite):
    def __init__(self, x, y, shop_id=-1):
        super().__init__(camera)
        if shop_id == 1:
            self.image = load_image('workbench.png')
        else:
            self.image = load_image('Label.png')
        self.rect = self.image.get_rect(center=(x, y))
        self.team = -1
        camera.colliding_objects.append(self)
        self.hitbox_x1, self.hitbox_y1 = self.rect.topleft
        self.hitbox_x1, self.hitbox_y1 = self.hitbox_x1 + 50, self.hitbox_y1 + 50
        self.hitbox_width = self.rect.w - 100
        self.hitbox_height = self.rect.h - 100
        self.hitbox = pygame.Rect(self.hitbox_x1, self.hitbox_y1, self.hitbox_width, self.hitbox_height)
        self.dead = False
        self.shop_id = shop_id
        self.display1 = False

    def update(self):
        self.display1 = self.hitbox.colliderect(player1.hitbox)

    def display_text(self):
        global window, scrap
        text = ''
        e = pygame.key.get_pressed()
        e = e[pygame.K_e]
        if self.shop_id == 3:
            text = ['            Press E to buy shotgun',
                    '                      10 Scrap           ']
            if e:
                if self.shop_id not in more_useful and scrap >= 10:
                    shotgun = Gun(uselul, 0.55, 15, 6, 5, 0.15, camera, 400, 'shotgun.png', 'shotgun_bullet.png',
                                  per_burst=5, reloadtime=1)
                    weapons.append(shotgun)
                    more_useful.append(self.shop_id)
                    scrap -= 10
        elif self.shop_id == 2:
            text = ['            Press E to buy AK47',
                    '                      10 Scrap           ']
            if e:
                if self.shop_id not in more_useful and scrap >= 10:
                    ak = Gun(uselul, 0.08, 1, 25, 5, 0.08, camera, 400, 'pixel_ak_47.png', 'shotgun_bullet.png',
                             reloadtime=1, per_burst=20)
                    weapons.append(ak)
                    more_useful.append(self.shop_id)
                    scrap -= 10
        elif self.shop_id == 1:
            text = ['            Press E to upgrade your drawn gun',
                    '                      5 Scrap           ']
            if e:
                if scrap >= 5:
                    gun.damage *= 2
                    scrap -= 5
        text_coord = 200
        for line in text:
            string_rendered = pygame.font.Font(None, 30).render(line, True, pygame.Color('Blue'))
            rect = string_rendered.get_rect()
            rect.top = text_coord
            rect.x = 200
            text_coord += rect.height
            window.blit(string_rendered, rect)


class Door(pygame.sprite.Sprite):
    def __init__(self, x, y):
        global lvl_count, day_count

        super().__init__(camera)
        self.team = 0
        camera.colliding_objects.append(self)
        print(day_count, lvl_count, 'indoors')
        if day_count < lvl_count:
            self.safe = True
            self.image = load_image("safe_door.png")
        else:
            self.safe = False
            self.image = load_image('door.png')
        self.rect = self.image.get_rect(center=(x, y))
        self.hitbox = self.rect
        self.dead = False


class Shield(pygame.sprite.Sprite):
    def __init__(self, who_is_holding):
        super().__init__(camera)
        camera.colliding_objects.append(self)
        self.image = load_image('shield.png')
        self.base_image = load_image('shield.png')
        self.rect = self.image.get_rect(center=who_is_holding.rect.center)
        self.base_rect = self.base_image.get_rect(center=who_is_holding.rect.center)
        self.who_is_holding = who_is_holding
        self.hitbox = self.rect
        self.ammo = 'N/A'
        self.team = 0
        self.dead = False

    def update(self):
        global camera
        if type(self.who_is_holding) == Player:
            self.who_is_holding.speed = 1
        self.dead = self.who_is_holding.dead
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
        if self.angle < -90.0 or self.angle > 90.0:
            self.reversed = True
        else:
            self.reversed = False
        self.image, self.rect = rot_center(self.base_image, self.base_rect, self.angle, self.reversed)
        self.rect = self.image.get_rect(center=(self.who_is_holding.rect.centerx, self.who_is_holding.rect.centery))
        self.hitbox = self.rect


class PickableObject(pygame.sprite.Sprite):
    def __init__(self, type1='Medkit', x=0, y=0, power=30):
        super().__init__(camera)
        objects = {'Medkit': load_image('medkit.png'),
                   'Ammo_pack': load_image('ammo-pack.png'),
                   'Scrap': load_image('scrap.png'),
                   'key': load_image('key.png')
                   }
        camera.colliding_objects.append(self)
        self.power = power
        self.x = x
        self.dead = False
        self.y = y
        self.image = objects[type1]
        self.rect = self.image.get_rect(topleft=(x, y))
        self.hitbox = self.rect
        self.team = -1
        self.type = type1

    def activate(self):
        global health, scrap, key_up
        if self.type == 'Medkit':
            health += self.power
        elif self.type == 'Ammo_pack' and type(gun) != Shield:
            gun.ammo += self.power
        elif self.type == 'scrap':
            scrap += 1
        else:
            key_up = True


def rot_center(image, rect, angle, flip=False):
    rot_image = pygame.transform.rotate(image, angle)
    if flip:
        rot_image = pygame.transform.rotate(image, 180 - angle)
        rot_image = pygame.transform.flip(rot_image, True, False)
    rot_rect = rot_image.get_rect(center=rect.center)
    return rot_image, rot_rect


def start_screen():
    global window, scale
    intro_text = ['',
                  '',
                  '                                                                          Game:',
                  '                                                                     -Nuclear Ice-',
                  '',
                  '',
                  '',
                  '',
                  '',
                  '',
                  '',
                  '',
                  '',
                  '                            Press any key to continue']
    font = pygame.font.Font(None, 40)
    fon = pygame.transform.scale(load_image('background.png'), (scale[0], scale[1]))
    window.blit(fon, (0, 0))
    text_coord = 50
    for line in intro_text:
        string_rendered = font.render(line, True, pygame.Color('white'))
        intro_rect = string_rendered.get_rect()
        text_coord += 10
        intro_rect.top = text_coord
        intro_rect.x = 10
        text_coord += intro_rect.height
        window.blit(string_rendered, intro_rect)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                return
        pygame.display.flip()
        clock.tick(30)


def load_level(filename):
    filename = "data/" + filename
    with open(filename, 'r') as mapFile:
        level_map = [line.strip() for line in mapFile]
    max_width = max(map(len, level_map))
    return list(map(lambda x: x.ljust(max_width, '.'), level_map))


def generate_random_lvl_layout():
    c = []
    k = []
    len_x = rad.randint(7, 15)
    len_y = rad.randint(7, 15)
    for i in range(len_x):
        k.append('o')
        for z in range(len_y):
            if z == len_y // 2 + len_y % 2 - 1 and (i == 0 or i == 1):
                k.append('.')
                continue
            if rad.randint(0, 20) == 1:
                k.append('#')
            elif rad.randint(0, 10) == 1:
                k.append('*')
            elif rad.randint(0, 12) == 1 and i >= 6:
                k.append('&')
            else:
                k.append('.')
        k.append('o')
        c.append(k.copy())
        k.clear()
    c.insert(0, ['o'] * (len_y // 2 + len_y % 2) + ['F'] + ['o'] * (len_y // 2 + 1))
    c.append(['o'] * (len_y // 2 + len_y % 2) + ['N'] + ['o'] * (len_y // 2 + 1))
    return c


def load_image(name):
    fullname = os.path.join('data', name)
    if not os.path.isfile(fullname):
        print(f"Файл с изображением '{fullname}' не найден")
        sys.exit()
    image = pygame.image.load(fullname).convert_alpha()
    return image


def create_reflection_bullets(x, y, bullet_class):
    dir1 = (bullet_class.rect.centerx - x, bullet_class.rect.centery - y)
    length = math.hypot(*dir1)
    print('exist')
    if length == 0.0:
        dir1 = 0, -1
    else:
        dir1 = (dir1[0] / length, dir1[1] / length)
    angle = math.degrees(math.atan2(-dir1[1], dir1[0]))
    for i in range(rad.randint(3, 6)):
        k = Bullet(bullet_class.rect.centerx, bullet_class.rect.centery, dir1, angle, 0, 9, camera,
                   team=0, bullet_image='particle.png', range1=50)
        ALL_bullets.append(k)


def generate_level(level):
    new_player, x, y = None, None, None
    id1 = 0
    print('hello')
    for y in range(len(level)):
        for x in range(len(level[y])):
            if level[y][x] == '.':
                Tile('empty', x, y)
            elif level[y][x] == 'o':
                Tile('wall', x, y)
            elif level[y][x] == 'F':
                if camera.safe:
                    Tile('empty', x, y)
                    Tile('wall', x, y, custom_image='safe_door.png')
                else:
                    Tile('empty', x, y)
                    Tile('wall', x, y, custom_image='door.png')
            elif level[y][x] == 'V':
                Tile('empty', x, y)
                Tile('wall', x, y, custom_image='tv2.png')
            elif level[y][x] == 'v':
                Tile('empty', x, y)
                Tile('wall', x, y, custom_image='tv1.png')
            elif level[y][x] == 'D':
                Tile('empty', x, y)
                Tile('wall', x, y, custom_image='YES1.png')
            elif level[y][x] == 'd':
                Tile('empty', x, y)
                Tile('wall', x, y, custom_image='YES2.png')
            elif level[y][x] == 'P':
                Tile('empty', x, y)
                Tile('wall', x, y, custom_image='tree.png')
            elif level[y][x] == 'T':
                Tile('empty', x, y)
                Tile('wall', x, y, custom_image='tumba.png')
            elif level[y][x] == 'b':
                Tile('empty', x, y)
                Tile('wall', x, y, custom_image='B2.png')
            elif level[y][x] == 'B':
                Tile('empty', x, y)
                Tile('wall', x, y, custom_image='B1.png')
            elif level[y][x] == 'U':
                Tile('empty', x, y)
                Tile('wall', x, y, custom_image='fridge.png')
            elif level[y][x] == 'K':
                Tile('empty', x, y)
                Tile('wall', x, y, custom_image='crate.png')
            elif level[y][x] == '@':
                Tile('empty', x, y)
                new_player = Player(x=x * 50, y=y * 50)
            elif level[y][x] == 'M':
                Tile('empty', x, y)
            elif level[y][x] == '*':
                Tile('empty', x, y)
                StaticObject(camera, x=x * 50, y=y * 50, hp=200)
            elif level[y][x] == ',':
                print('snow')
                Tile('snow', x, y)
            elif level[y][x] == '&':
                Tile('empty', x, y)
                if rad.randint(0, 2) == 0:
                    rifle = EnemyGun(uselul, 0.07, 1, 3, 3, 0.12, camera, 400,
                                     'assault_rifle.png', 'shotgun_bullet.png', per_burst=3, reloadtime=1)
                elif rad.randint(0, 2) == 1:
                    rifle = EnemyGun(uselul, 0.12, 1, 3, 3, 0.23, camera, 350, 'pixel_ak_47.png', 'shotgun_bullet.png',
                                     reloadtime=3, per_burst=30)
                else:
                    rifle = EnemyGun(uselul, 0.5, 5, 1, 3, 0.3, camera, 350,
                                     'shotgun.png', 'shotgun_bullet.png', per_burst=1, reloadtime=0)
                k = Enemy(x * 50, y * 50, rifle)
                rifle.who_is_holding = k
                rifle.team = k.team
            elif level[y][x] == 'N':
                Door(x * 50, y * 50)
            elif level[y][x] == 'L':
                id1 += 1
                Tile('empty', x, y)
                if id1 in more_useful and id1 == 2:
                    Tile('wall', x, y, custom_image='plant.png')
                elif id1 in more_useful and id1 == 3:
                    Tile('wall', x, y, custom_image='table.png')
                else:
                    labels.append(Label(x * 50, y * 50, shop_id=id1))
            elif level[y][x] == '#':
                Tile('empty', x, y)
                if rad.randint(0, 10) == 1:
                    PickableObject('Medkit', x * 50, y * 50)
                elif rad.randint(0, 2) == 1:
                    PickableObject('Ammo_pack', x * 50, y * 50)
                else:
                    PickableObject('Scrap', x * 50, y * 50)
    if new_player is None:
        new_player = Player
        return new_player(x=((len(level[0]) // 2 + len(level[0]) % 2 - 1) * 50), y=60)
    return new_player


def game_over():
    global window, scales
    intro_text = ['',
                  '',
                  '                                                                          Game:   ',
                  '                                                                     -Nuclear Ice-',
                  '                                                                                  ',
                  '                                                                                  ',
                  '                                       You died.',
                  '                              ',
                  '                                                                                  ',
                  '                                                                                  ',
                  f'                                 Days survived {day_count}                            ',
                  '                                                                                  ',
                  '                                                                                  ',
                  '                                                                                  ']

    font = pygame.font.Font(None, 40)
    fon = pygame.transform.scale(load_image('end_screen.jpg'), (scale[0], scale[1]))
    window.blit(fon, (0, 0))
    clock = pygame.time.Clock()

    text_coord = 50
    for line in intro_text:
        string_rendered = font.render(line, True, pygame.Color('white'))
        intro_rect = string_rendered.get_rect()
        text_coord += 10
        intro_rect.top = text_coord
        intro_rect.x = 10
        text_coord += intro_rect.height
        window.blit(string_rendered, intro_rect)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        pygame.display.flip()
        clock.tick(30)


run = True

more_useful = []
bullets = []
camera = CameraGroup()
gun_image = 'Flamethrower.png'
bullet_image = 'Flamethrower_particle.png'
images = ['Barrel.jpg', 'Barrels.png']

tiles = pygame.sprite.Group()
scrap = 0
health = 100
labels = []

tile_images = {
    'void': load_image('ground_tile.png'),
    'empty': load_image('ground_tile.png'),
    'snow_var3': load_image('Barrel.jpg'),
    'wall': load_image('wall_tile.png'),
    'snow': load_image('snow.png')
}

tile_width = tile_height = 50
uselul = StaticObject(y=-10000, x=-10000, camera=camera)
ALL_bullets = []
player1 = generate_level(load_level('safe_base.txt'))
assault_rifle = Gun(uselul, 0.05, 1, 25, 7, 0.03, camera, 400, 'assault_rifle.png', 'shotgun_bullet.png',
                    per_burst=3, reloadtime=0.5)

weapons = [assault_rifle]
gun = weapons[0]
'''drop - acceptable numbers <= 0.3, anything more is questionable, more than 1 is straight up wrong'''
gun.who_is_holding = player1
gun.team = player1.team
start_screen()
safe = True
EPICSHIELD = Shield(uselul)

while run:
    clock.tick(100)
    player1.move()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        if event.type == pygame.MOUSEWHEEL:
            if (event.y == -1 and camera.zoom_scale > 1) or (event.y == 1 and camera.zoom_scale <= 1.1):
                camera.zoom_scale += event.y * 0.1
    if health <= 0 or player1.dead:
        game_over()
    window.fill(0)
    camera.update()
    camera.camera_draw(player1)
    player1.health_and_ammo()
    for i in range(len(labels)):
        if labels[i].display1:
            labels[i].display_text()
    pygame.display.flip()
