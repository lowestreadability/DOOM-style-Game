import pygame
from random import choices,randrange,randint,random
from collections import deque
from functools import lru_cache
import os
import math
_=False
mini_map=[
[1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
[1,_,_,_,_,_,_,_,_,_,_,_,_,_,_,1],
[1,_,_,3,3,3,3,_,_,_,2,2,2,_,_,1],
[1,_,_,_,_,_,4,_,_,_,_,_,2,_,_,1],
[1,_,_,_,_,_,4,_,_,_,_,_,2,_,_,1],
[1,_,_,3,3,3,3,_,_,_,_,_,_,_,_,1],
[1,_,_,_,_,_,_,_,_,_,_,_,_,_,_,1],
[1,_,_,_,4,_,_,_,4,_,_,_,_,_,_,1],
[1,1,1,3,1,3,1,1,1,3,_,_,3,1,1,1],
[1,1,1,1,1,1,1,1,1,3,_,_,3,1,1,1],
[1,1,1,1,1,1,1,1,1,3,_,_,3,1,1,1],
[1,1,3,1,1,1,1,1,1,3,_,_,3,1,1,1],
[1,4,_,_,_,_,_,_,_,_,_,_,_,_,_,1],
[3,_,_,_,_,_,_,_,_,_,_,_,_,_,_,1],
[1,_,_,_,_,_,_,_,_,_,_,_,_,_,_,1],
[1,_,_,2,_,_,_,_,_,3,4,_,4,3,_,1],
[1,_,_,5,_,_,_,_,_,_,3,_,3,_,_,1],
[1,_,_,2,_,_,_,_,_,_,_,_,_,_,_,1],
[1,_,_,_,_,_,_,_,_,_,_,_,_,_,_,1],
[3,_,_,_,_,_,_,_,_,_,_,_,_,_,_,1],
[1,4,_,_,_,_,_,_,4,_,_,4,_,_,_,1],
[1,1,3,3,_,_,3,3,1,3,3,1,3,1,1,1],
[1,1,1,3,_,_,3,1,1,1,1,1,1,1,1,1],
[1,3,3,4,_,_,4,3,3,3,3,3,3,3,3,1],
[3,_,_,_,_,_,_,_,_,_,_,_,_,_,_,3],
[3,_,_,_,_,_,_,_,_,_,_,_,_,_,_,3],
[3,_,_,_,_,_,_,_,_,_,_,_,_,_,_,3],
[3,_,_,5,_,_,_,5,_,_,_,5,_,_,_,3],
[3,_,_,_,_,_,_,_,_,_,_,_,_,_,_,3],
[3,_,_,_,_,_,_,_,_,_,_,_,_,_,_,3],
[3,_,_,_,_,_,_,_,_,_,_,_,_,_,_,3],
[3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3]]
RES=WIDTH,HEIGHT=1600,900
HALF_WIDTH=WIDTH // 2
HALF_HEIGHT=HEIGHT // 2
FPS=0
PLAYER_POS=1.5,5
PLAYER_ANGLE=0
PLAYER_SPEED=0.004
PLAYER_ROT_SPEED=0.002
PLAYER_SIZE_SCALE=60
PLAYER_MAX_HEALTH=100
MOUSE_SENSITIVITY=0.0003
MOUSE_MAX_REL=40
MOUSE_BORDER_LEFT=100
MOUSE_BORDER_RIGHT=WIDTH - MOUSE_BORDER_LEFT
FLOOR_COLOR=(30,30,30)
FOV=math.pi / 3
HALF_FOV=FOV / 2
NUM_RAYS=WIDTH // 2
HALF_NUM_RAYS=NUM_RAYS // 2
DELTA_ANGLE=FOV / NUM_RAYS
MAX_DEPTH=20
SCREEN_DIST=HALF_WIDTH / math.tan(HALF_FOV)
SCALE=WIDTH // NUM_RAYS
TEXTURE_SIZE=256
HALF_TEXTURE_SIZE=TEXTURE_SIZE // 2
class Map:
    def __init__(self,game):
        self.game=game
        self.mini_map=mini_map
        self.world_map={}
        self.rows=len(self.mini_map)
        self.cols=len(self.mini_map[0])
        for j,row in enumerate(self.mini_map):
            for i,value in enumerate(row):
                if value:
                    self.world_map[(i,j)]=value
    def draw(self):
        [pygame.draw.rect(self.game.screen,'darkgray',(pos[0] * 100,pos[1] * 100,100,100),2)for pos in self.world_map]
class Player:
    def __init__(self,game):
        self.game=game
        self.x,self.y=PLAYER_POS
        self.angle=PLAYER_ANGLE
        self.shot=False
        self.health=PLAYER_MAX_HEALTH
        self.rel=0
        self.health_recovery_delay=700
        self.time_prev=pygame.time.get_ticks()
        self.diag_move_corr=1 / math.sqrt(2)
    def recover_health(self):
        if self.check_health_recovery_delay() and self.health < PLAYER_MAX_HEALTH:
            self.health+=1
    def check_health_recovery_delay(self):
        time_now=pygame.time.get_ticks()
        if time_now - self.time_prev > self.health_recovery_delay:
            self.time_prev=time_now
            return True
    def check_game_over(self):
        if self.health < 1:
            self.game.object_renderer.game_over()
            pygame.display.flip()
            pygame.time.delay(1500)
            self.game.new_game()
    def get_damage(self,damage):
        self.health-=damage
        self.game.object_renderer.player_damage()
        self.game.sound.player_pain.play()
        self.check_game_over()
    def single_fire_event(self,event):
        if event.type==pygame.MOUSEBUTTONDOWN:
            if event.button==1 and not self.shot and not self.game.weapon.reloading:
                self.game.sound.shotgun.play()
                self.shot=True
                self.game.weapon.reloading=True
    def movement(self):
        sin_a=math.sin(self.angle)
        cos_a=math.cos(self.angle)
        dx,dy=0,0
        speed=PLAYER_SPEED * self.game.delta_time
        speed_sin=speed * sin_a
        speed_cos=speed * cos_a
        keys=pygame.key.get_pressed()
        num_key_pressed=-1
        if keys[pygame.K_w]:
            num_key_pressed+=1
            dx+=speed_cos
            dy+=speed_sin
        if keys[pygame.K_s]:
            num_key_pressed+=1
            dx+=-speed_cos
            dy+=-speed_sin
        if keys[pygame.K_a]:
            num_key_pressed+=1
            dx+=speed_sin
            dy+=-speed_cos
        if keys[pygame.K_d]:
            num_key_pressed+=1
            dx+=-speed_sin
            dy+=speed_cos
        if num_key_pressed:
            dx *= self.diag_move_corr
            dy *= self.diag_move_corr
        self.check_wall_collision(dx,dy)
        self.angle %= math.tau
    def check_wall(self,x,y):
        return (x,y) not in self.game.map.world_map
    def check_wall_collision(self,dx,dy):
        scale=PLAYER_SIZE_SCALE / self.game.delta_time
        if self.check_wall(int(self.x + dx * scale),int(self.y)):
            self.x+=dx
        if self.check_wall(int(self.x),int(self.y + dy * scale)):
            self.y+=dy
    def draw(self):
        pygame.draw.line(self.game.screen,'yellow',(self.x * 100,self.y * 100),(self.x * 100 + WIDTH * math.cos(self.angle),self.y * 100 + WIDTH * math. sin(self.angle)),2)
        pygame.draw.circle(self.game.screen,'green',(self.x * 100,self.y * 100),15)
    def mouse_control(self):
        mx,my=pygame.mouse.get_pos()
        if mx < MOUSE_BORDER_LEFT or mx > MOUSE_BORDER_RIGHT:
            pygame.mouse.set_pos([HALF_WIDTH,HALF_HEIGHT])
        self.rel=pygame.mouse.get_rel()[0]
        self.rel=max(-MOUSE_MAX_REL,min(MOUSE_MAX_REL,self.rel))
        self.angle+=self.rel * MOUSE_SENSITIVITY * self.game.delta_time
    def update(self):
        self.movement()
        self.mouse_control()
        self.recover_health()
    @property
    def pos(self):
        return self.x,self.y
    @property
    def map_pos(self):
        return int(self.x),int(self.y)
class RayCasting:
    def __init__(self,game):
        self.game=game
        self.ray_casting_result=[]
        self.objects_to_render=[]
        self.textures=self.game.object_renderer.wall_textures
    def get_objects_to_render(self):
        self.objects_to_render=[]
        for ray,values in enumerate(self.ray_casting_result):
            depth,proj_height,texture,offset=values
            if proj_height < HEIGHT:
                wall_column=self.textures[texture].subsurface(offset * (TEXTURE_SIZE - SCALE),0,SCALE,TEXTURE_SIZE)
                wall_column=pygame.transform.scale(wall_column,(SCALE,proj_height))
                wall_pos=(ray * SCALE,HALF_HEIGHT - proj_height // 2)
            else:
                texture_height=TEXTURE_SIZE * HEIGHT / proj_height
                wall_column=self.textures[texture].subsurface(offset * (TEXTURE_SIZE - SCALE),HALF_TEXTURE_SIZE - texture_height // 2,SCALE,texture_height)
                wall_column=pygame.transform.scale(wall_column,(SCALE,HEIGHT))
                wall_pos=(ray * SCALE,0)
            self.objects_to_render.append((depth,wall_column,wall_pos))
    def ray_cast(self):
        self.ray_casting_result=[]
        texture_vert,texture_hor=1,1
        ox,oy=self.game.player.pos
        x_map,y_map=self.game.player.map_pos
        ray_angle=self.game.player.angle - HALF_FOV + 0.0001
        for ray in range(NUM_RAYS):
            sin_a=math.sin(ray_angle)
            cos_a=math.cos(ray_angle)
            y_hor,dy=(y_map + 1,1) if sin_a > 0 else (y_map - 1e-6,-1)
            depth_hor=(y_hor - oy) / sin_a
            x_hor=ox + depth_hor * cos_a
            delta_depth=dy / sin_a
            dx=delta_depth * cos_a
            for i in range(MAX_DEPTH):
                tile_hor=int(x_hor),int(y_hor)
                if tile_hor in self.game.map.world_map:
                    texture_hor=self.game.map.world_map[tile_hor]
                    break
                x_hor+=dx
                y_hor+=dy
                depth_hor+=delta_depth
            x_vert,dx=(x_map + 1,1) if cos_a > 0 else (x_map - 1e-6,-1)
            depth_vert=(x_vert - ox) / cos_a
            y_vert=oy + depth_vert * sin_a
            delta_depth=dx / cos_a
            dy=delta_depth * sin_a
            for i in range(MAX_DEPTH):
                tile_vert=int(x_vert),int(y_vert)
                if tile_vert in self.game.map.world_map:
                    texture_vert=self.game.map.world_map[tile_vert]
                    break
                x_vert+=dx
                y_vert+=dy
                depth_vert+=delta_depth
            if depth_vert < depth_hor:
                depth,texture=depth_vert,texture_vert
                y_vert %= 1
                offset=y_vert if cos_a > 0 else (1 - y_vert)
            else:
                depth,texture=depth_hor,texture_hor
                x_hor %= 1
                offset=(1 - x_hor) if sin_a > 0 else x_hor
            depth *= math.cos(self.game.player.angle - ray_angle)
            proj_height=SCREEN_DIST / (depth + 0.0001)
            self.ray_casting_result.append((depth,proj_height,texture,offset))
            ray_angle+=DELTA_ANGLE
    def update(self):
        self.ray_cast()
        self.get_objects_to_render()
class ObjectRenderer:
    def __init__(self,game):
        self.game=game
        self.screen=game.screen
        self.wall_textures=self.load_wall_textures()
        self.sky_image=self.get_texture('resources/textures/sky.png',(WIDTH,HALF_HEIGHT))
        self.sky_offset=0
        self.blood_screen=self.get_texture('resources/textures/blood_screen.png',RES)
        self.digit_size=90
        self.digit_images=[self.get_texture(f'resources/textures/digits/{i}.png',[self.digit_size] * 2)for i in range(11)]
        self.digits=dict(zip(map(str,range(11)),self.digit_images))
        self.game_over_image=self.get_texture('resources/textures/game_over.png',RES)
        self.win_image=self.get_texture('resources/textures/win.png',RES)
    def draw(self):
        self.draw_background()
        self.render_game_objects()
        self.draw_player_health()
    def win(self):
        self.screen.blit(self.win_image,(0,0))
    def game_over(self):
        self.screen.blit(self.game_over_image,(0,0))
    def draw_player_health(self):
        health=str(self.game.player.health)
        for i,char in enumerate(health):
            self.screen.blit(self.digits[char],(i * self.digit_size,0))
        self.screen.blit(self.digits['10'],((i + 1) * self.digit_size,0))
    def player_damage(self):
        self.screen.blit(self.blood_screen,(0,0))
    def draw_background(self):
        self.sky_offset=(self.sky_offset + 4.5 * self.game.player.rel) % WIDTH
        self.screen.blit(self.sky_image,(-self.sky_offset,0))
        self.screen.blit(self.sky_image,(-self.sky_offset + WIDTH,0))
        pygame.draw.rect(self.screen,FLOOR_COLOR,(0,HALF_HEIGHT,WIDTH,HEIGHT))
    def render_game_objects(self):
        list_objects=sorted(self.game.raycasting.objects_to_render,key=lambda t: t[0],reverse=True)
        for depth,image,pos in list_objects:
            self.screen.blit(image,pos)
    @staticmethod
    def get_texture(path,res=(TEXTURE_SIZE,TEXTURE_SIZE)):
        texture=pygame.image.load(path).convert_alpha()
        return pygame.transform.scale(texture,res)
    def load_wall_textures(self):
        return {1: self.get_texture('resources/textures/1.png'),2: self.get_texture('resources/textures/2.png'),3: self.get_texture('resources/textures/3.png'),4: self.get_texture('resources/textures/4.png'),5: self.get_texture('resources/textures/5.png'),}
class SpriteObject:
    def __init__(self,game,path='resources/sprites/static_sprites/candlebra.png',pos=(10.5,3.5),scale=0.7,shift=0.27):
        self.game=game
        self.player=game.player
        self.x,self.y=pos
        self.image=pygame.image.load(path).convert_alpha()
        self.IMAGE_WIDTH=self.image.get_width()
        self.IMAGE_HALF_WIDTH=self.image.get_width() // 2
        self.IMAGE_RATIO=self.IMAGE_WIDTH / self.image.get_height()
        self.dx,self.dy,self.theta,self.screen_x,self.dist,self.norm_dist=0,0,0,0,1,1
        self.sprite_half_width=0
        self.SPRITE_SCALE=scale
        self.SPRITE_HEIGHT_SHIFT=shift
    def get_sprite_projection(self):
        proj=SCREEN_DIST / self.norm_dist * self.SPRITE_SCALE
        proj_width,proj_height=proj * self.IMAGE_RATIO,proj
        image=pygame.transform.scale(self.image,(proj_width,proj_height))
        self.sprite_half_width=proj_width // 2
        height_shift=proj_height * self.SPRITE_HEIGHT_SHIFT
        pos=self.screen_x - self.sprite_half_width,HALF_HEIGHT - proj_height // 2 + height_shift
        self.game.raycasting.objects_to_render.append((self.norm_dist,image,pos))
    def get_sprite(self):
        dx=self.x - self.player.x
        dy=self.y - self.player.y
        self.dx,self.dy=dx,dy
        self.theta=math.atan2(dy,dx)
        delta=self.theta - self.player.angle
        if (dx > 0 and self.player.angle > math.pi) or (dx < 0 and dy < 0):
            delta+=math.tau
        delta_rays=delta / DELTA_ANGLE
        self.screen_x=(HALF_NUM_RAYS + delta_rays) * SCALE
        self.dist=math.hypot(dx,dy)
        self.norm_dist=self.dist * math.cos(delta)
        if -self.IMAGE_HALF_WIDTH < self.screen_x < (WIDTH + self.IMAGE_HALF_WIDTH) and self.norm_dist > 0.5:
            self.get_sprite_projection()
    def update(self):
        self.get_sprite()
class AnimatedSprite(SpriteObject):
    def __init__(self,game,path='resources/sprites/animated_sprites/green_light/0.png',pos=(11.5,3.5),scale=0.8,shift=0.16,animation_time=120):
        super().__init__(game,path,pos,scale,shift)
        self.animation_time=animation_time
        self.path=path.rsplit('/',1)[0]
        self.images=self.get_images(self.path)
        self.animation_time_prev=pygame.time.get_ticks()
        self.animation_trigger=False
    def update(self):
        super().update()
        self.check_animation_time()
        self.animate(self.images)
    def animate(self,images):
        if self.animation_trigger:
            images.rotate(-1)
            self.image=images[0]
    def check_animation_time(self):
        self.animation_trigger=False
        time_now=pygame.time.get_ticks()
        if time_now - self.animation_time_prev > self.animation_time:
            self.animation_time_prev=time_now
            self.animation_trigger=True
    def get_images(self,path):
        images=deque()
        for file_name in os.listdir(path):
            if os.path.isfile(os.path.join(path,file_name)):
                img=pygame.image.load(path + '/' + file_name).convert_alpha()
                images.append(img)
        return images
class NPC(AnimatedSprite):
    def __init__(self,game,path='resources/sprites/npc/soldier/0.png',pos=(10.5,5.5),scale=0.6,shift=0.38,animation_time=180):
        super().__init__(game,path,pos,scale,shift,animation_time)
        self.attack_images=self.get_images(self.path + '/attack')
        self.death_images=self.get_images(self.path + '/death')
        self.idle_images=self.get_images(self.path + '/idle')
        self.pain_images=self.get_images(self.path + '/pain')
        self.walk_images=self.get_images(self.path + '/walk')
        self.attack_dist=randint(3,6)
        self.speed=0.03
        self.size=20
        self.health=100
        self.attack_damage=10
        self.accuracy=0.15
        self.alive=True
        self.pain=False
        self.ray_cast_value=False
        self.frame_counter=0
        self.player_search_trigger=False
    def update(self):
        self.check_animation_time()
        self.get_sprite()
        self.run_logic()
    def check_wall(self,x,y):
        return (x,y) not in self.game.map.world_map
    def check_wall_collision(self,dx,dy):
        if self.check_wall(int(self.x + dx * self.size),int(self.y)):
            self.x+=dx
        if self.check_wall(int(self.x),int(self.y + dy * self.size)):
            self.y+=dy
    def movement(self):
        next_pos=self.game.pathfinding.get_path(self.map_pos,self.game.player.map_pos)
        next_x,next_y=next_pos
        if next_pos not in self.game.object_handler.npc_positions:
            angle=math.atan2(next_y + 0.5 - self.y,next_x + 0.5 - self.x)
            dx=math.cos(angle) * self.speed
            dy=math.sin(angle) * self.speed
            self.check_wall_collision(dx,dy)
    def attack(self):
        if self.animation_trigger:
            self.game.sound.npc_shot.play()
            if random() < self.accuracy:
                self.game.player.get_damage(self.attack_damage)
    def animate_death(self):
        if not self.alive:
            if self.game.global_trigger and self.frame_counter < len(self.death_images) - 1:
                self.death_images.rotate(-1)
                self.image=self.death_images[0]
                self.frame_counter+=1
    def animate_pain(self):
        self.animate(self.pain_images)
        if self.animation_trigger:
            self.pain=False
    def check_hit_in_npc(self):
        if self.ray_cast_value and self.game.player.shot:
            if HALF_WIDTH - self.sprite_half_width < self.screen_x < HALF_WIDTH + self.sprite_half_width:
                self.game.sound.npc_pain.play()
                self.game.player.shot=False
                self.pain=True
                self.health-=self.game.weapon.damage
                self.check_health()
    def check_health(self):
        if self.health < 1:
            self.alive=False
            self.game.sound.npc_death.play()
    def run_logic(self):
        if self.alive:
            self.ray_cast_value=self.ray_cast_player_npc()
            self.check_hit_in_npc()
            if self.pain:
                self.animate_pain()
            elif self.ray_cast_value:
                self.player_search_trigger=True
                if self.dist < self.attack_dist:
                    self.animate(self.attack_images)
                    self.attack()
                else:
                    self.animate(self.walk_images)
                    self.movement()
            elif self.player_search_trigger:
                self.animate(self.walk_images)
                self.movement()
            else:
                self.animate(self.idle_images)
        else:
            self.animate_death()
    @property
    def map_pos(self):
        return int(self.x),int(self.y)
    def ray_cast_player_npc(self):
        if self.game.player.map_pos==self.map_pos:
            return True
        wall_dist_v,wall_dist_h=0,0
        player_dist_v,player_dist_h=0,0
        ox,oy=self.game.player.pos
        x_map,y_map=self.game.player.map_pos
        ray_angle=self.theta
        sin_a=math.sin(ray_angle)
        cos_a=math.cos(ray_angle)
        y_hor,dy=(y_map + 1,1) if sin_a > 0 else (y_map - 1e-6,-1)
        depth_hor=(y_hor - oy) / sin_a
        x_hor=ox + depth_hor * cos_a
        delta_depth=dy / sin_a
        dx=delta_depth * cos_a
        for i in range(MAX_DEPTH):
            tile_hor=int(x_hor),int(y_hor)
            if tile_hor==self.map_pos:
                player_dist_h=depth_hor
                break
            if tile_hor in self.game.map.world_map:
                wall_dist_h=depth_hor
                break
            x_hor+=dx
            y_hor+=dy
            depth_hor+=delta_depth
        x_vert,dx=(x_map + 1,1) if cos_a > 0 else (x_map - 1e-6,-1)
        depth_vert=(x_vert - ox) / cos_a
        y_vert=oy + depth_vert * sin_a
        delta_depth=dx / cos_a
        dy=delta_depth * sin_a
        for i in range(MAX_DEPTH):
            tile_vert=int(x_vert),int(y_vert)
            if tile_vert==self.map_pos:
                player_dist_v=depth_vert
                break
            if tile_vert in self.game.map.world_map:
                wall_dist_v=depth_vert
                break
            x_vert+=dx
            y_vert+=dy
            depth_vert+=delta_depth
        player_dist=max(player_dist_v,player_dist_h)
        wall_dist=max(wall_dist_v,wall_dist_h)
        if 0 < player_dist < wall_dist or not wall_dist:
            return True
        return False
    def draw_ray_cast(self):
        pygame.draw.circle(self.game.screen,'red',(100 * self.x,100 * self.y),15)
        if self.ray_cast_player_npc():
            pygame.draw.line(self.game.screen,'orange',(100 * self.game.player.x,100 * self.game.player.y),(100 * self.x,100 * self.y),2)
class SoldierNPC(NPC):
    def __init__(self,game,path='resources/sprites/npc/soldier/0.png',pos=(10.5,5.5),scale=0.6,shift=0.38,animation_time=180):
        super().__init__(game,path,pos,scale,shift,animation_time)
class CacoDemonNPC(NPC):
    def __init__(self,game,path='resources/sprites/npc/caco_demon/0.png',pos=(10.5,6.5),scale=0.7,shift=0.27,animation_time=250):
        super().__init__(game,path,pos,scale,shift,animation_time)
        self.attack_dist=1.0
        self.health=150
        self.attack_damage=25
        self.speed=0.05
        self.accuracy=0.35
class CyberDemonNPC(NPC):
    def __init__(self,game,path='resources/sprites/npc/cyber_demon/0.png',pos=(11.5,6.0),scale=1.0,shift=0.04,animation_time=210):
        super().__init__(game,path,pos,scale,shift,animation_time)
        self.attack_dist=6
        self.health=350
        self.attack_damage=15
        self.speed=0.055
        self.accuracy=0.25
class ObjectHandler:
    def __init__(self,game):
        self.game=game
        self.sprite_list=[]
        self.npc_list=[]
        self.npc_sprite_path='resources/sprites/npc/'
        self.static_sprite_path='resources/sprites/static_sprites/'
        self.anim_sprite_path='resources/sprites/animated_sprites/'
        add_sprite=self.add_sprite
        add_npc=self.add_npc
        self.npc_positions={}
        self.enemies=20
        self.npc_types=[SoldierNPC,CacoDemonNPC,CyberDemonNPC]
        self.weights=[70,20,10]
        self.restricted_area={(i,j) for i in range(10) for j in range(10)}
        self.spawn_npc()
        add_sprite(AnimatedSprite(game))
        add_sprite(AnimatedSprite(game,pos=(1.5,1.5)))
        add_sprite(AnimatedSprite(game,pos=(1.5,7.5)))
        add_sprite(AnimatedSprite(game,pos=(5.5,3.25)))
        add_sprite(AnimatedSprite(game,pos=(5.5,4.75)))
        add_sprite(AnimatedSprite(game,pos=(7.5,2.5)))
        add_sprite(AnimatedSprite(game,pos=(7.5,5.5)))
        add_sprite(AnimatedSprite(game,pos=(14.5,1.5)))
        add_sprite(AnimatedSprite(game,pos=(14.5,4.5)))
        add_sprite(AnimatedSprite(game,path=self.anim_sprite_path + 'red_light/0.png',pos=(14.5,5.5)))
        add_sprite(AnimatedSprite(game,path=self.anim_sprite_path + 'red_light/0.png',pos=(14.5,7.5)))
        add_sprite(AnimatedSprite(game,path=self.anim_sprite_path + 'red_light/0.png',pos=(12.5,7.5)))
        add_sprite(AnimatedSprite(game,path=self.anim_sprite_path + 'red_light/0.png',pos=(9.5,7.5)))
        add_sprite(AnimatedSprite(game,path=self.anim_sprite_path + 'red_light/0.png',pos=(14.5,12.5)))
        add_sprite(AnimatedSprite(game,path=self.anim_sprite_path + 'red_light/0.png',pos=(9.5,20.5)))
        add_sprite(AnimatedSprite(game,path=self.anim_sprite_path + 'red_light/0.png',pos=(10.5,20.5)))
        add_sprite(AnimatedSprite(game,path=self.anim_sprite_path + 'red_light/0.png',pos=(3.5,14.5)))
        add_sprite(AnimatedSprite(game,path=self.anim_sprite_path + 'red_light/0.png',pos=(3.5,18.5)))
        add_sprite(AnimatedSprite(game,pos=(14.5,24.5)))
        add_sprite(AnimatedSprite(game,pos=(14.5,30.5)))
        add_sprite(AnimatedSprite(game,pos=(1.5,30.5)))
        add_sprite(AnimatedSprite(game,pos=(1.5,24.5)))
    def spawn_npc(self):
        for i in range(self.enemies):
                npc=choices(self.npc_types,self.weights)[0]
                pos=x,y=randrange(self.game.map.cols),randrange(self.game.map.rows)
                while (pos in self.game.map.world_map) or (pos in self.restricted_area):
                    pos=x,y=randrange(self.game.map.cols),randrange(self.game.map.rows)
                self.add_npc(npc(self.game,pos=(x + 0.5,y + 0.5)))
    def check_win(self):
        if not len(self.npc_positions):
            self.game.object_renderer.win()
            pygame.display.flip()
            pygame.time.delay(1500)
            self.game.new_game()
    def update(self):
        self.npc_positions={npc.map_pos for npc in self.npc_list if npc.alive}
        [sprite.update() for sprite in self.sprite_list]
        [npc.update() for npc in self.npc_list]
        self.check_win()
    def add_npc(self,npc):
        self.npc_list.append(npc)
    def add_sprite(self,sprite):
        self.sprite_list.append(sprite)
class Weapon(AnimatedSprite):
    def __init__(self,game,path='resources/sprites/weapon/shotgun/0.png',scale=0.4,animation_time=90):
        super().__init__(game=game,path=path,scale=scale,animation_time=animation_time)
        self.images=deque([pygame.transform.smoothscale(img,(self.image.get_width() * scale,self.image.get_height() * scale))for img in self.images])
        self.weapon_pos=(HALF_WIDTH - self.images[0].get_width() // 2,HEIGHT - self.images[0].get_height())
        self.reloading=False
        self.num_images=len(self.images)
        self.frame_counter=0
        self.damage=50
    def animate_shot(self):
        if self.reloading:
            self.game.player.shot=False
            if self.animation_trigger:
                self.images.rotate(-1)
                self.image=self.images[0]
                self.frame_counter+=1
                if self.frame_counter==self.num_images:
                    self.reloading=False
                    self.frame_counter=0
    def draw(self):
        self.game.screen.blit(self.images[0],self.weapon_pos)
    def update(self):
        self.check_animation_time()
        self.animate_shot()
class Sound:
    def __init__(self,game):
        self.game=game
        pygame.mixer.init()
        self.path='resources/sound/'
        self.shotgun=pygame.mixer.Sound(self.path + 'shotgun.wav')
        self.npc_pain=pygame.mixer.Sound(self.path + 'npc_pain.wav')
        self.npc_death=pygame.mixer.Sound(self.path + 'npc_death.wav')
        self.npc_shot=pygame.mixer.Sound(self.path + 'npc_attack.wav')
        self.npc_shot.set_volume(0.2)
        self.player_pain=pygame.mixer.Sound(self.path + 'player_pain.wav')
        self.theme=pygame.mixer.music.load(self.path + 'theme.mp3')
        pygame.mixer.music.set_volume(0.3)
class PathFinding:
    def __init__(self,game):
        self.game=game
        self.map=game.map.mini_map
        self.ways=[-1,0],[0,-1],[1,0],[0,1],[-1,-1],[1,-1],[1,1],[-1,1]
        self.graph={}
        self.get_graph()
    @lru_cache
    def get_path(self,start,goal):
        self.visited=self.bfs(start,goal,self.graph)
        path=[goal]
        step=self.visited.get(goal,start)
        while step and step != start:
            path.append(step)
            step=self.visited[step]
        return path[-1]
    def bfs(self,start,goal,graph):
        queue=deque([start])
        visited={start: None}
        while queue:
            cur_node=queue.popleft()
            if cur_node==goal:
                break
            next_nodes=graph[cur_node]
            for next_node in next_nodes:
                if next_node not in visited and next_node not in self.game.object_handler.npc_positions:
                    queue.append(next_node)
                    visited[next_node]=cur_node
        return visited
    def get_next_nodes(self,x,y):
        return [(x + dx,y + dy) for dx,dy in self.ways if (x + dx,y + dy) not in self.game.map.world_map]
    def get_graph(self):
        for y,row in enumerate(self.map):
            for x,col in enumerate(row):
                if not col:
                    self.graph[(x,y)]=self.graph.get((x,y),[]) + self.get_next_nodes(x,y)
class Game:
    def __init__(self):
        pygame.init()
        pygame.mouse.set_visible(False)
        self.screen=pygame.display.set_mode(RES)
        pygame.event.set_grab(True)
        self.clock=pygame.time.Clock()
        self.delta_time=1
        self.global_trigger=False
        self.global_event=pygame.USEREVENT + 0
        pygame.time.set_timer(self.global_event,40)
        self.map=Map(self)
        self.player=Player(self)
        self.object_renderer=ObjectRenderer(self)
        self.raycasting=RayCasting(self)
        self.object_handler=ObjectHandler(self)
        self.weapon=Weapon(self)
        self.sound=Sound(self)
        self.pathfinding=PathFinding(self)
        pygame.mixer.music.play(-1)
    def run(self):
        while True:
            self.global_trigger=False
            for event in pygame.event.get((pygame.QUIT,pygame.MOUSEBUTTONDOWN,pygame.MOUSEBUTTONUP)):
                match event.type:
                    case pygame.QUIT:
                        exit()
                    case pygame.MOUSEBUTTONDOWN:
                        self.global_trigger=True
                    case pygame.MOUSEBUTTONUP:
                        self.global_trigger=False
                self.player.single_fire_event(event)
            self.player.update()
            self.raycasting.update()
            self.object_handler.update()
            self.weapon.update()
            pygame.display.flip()
            self.delta_time=self.clock.tick(FPS)
            self.object_renderer.draw()
            self.weapon.draw()
Game().run()