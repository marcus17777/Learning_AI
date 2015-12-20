import pygame
import sys
import math
import random
import variables
import copy


class Main(variables.Variables):
    def __init__(self):
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.init()
        pygame.font.init()

        self.screen.fill((80, 80, 80))
        self.font = pygame.font.Font(None, 36)
        self.clock = pygame.time.Clock()
        self.ms = self.clock.tick(60)

    def fps_counter(self):
        """
            Just a fps_counter to debug how good the game is running.
            Not working atm.

        :param screen: Surface, where fps_counter is blited to.
        :param ms: Needed for fps calculation.
        """
        return 'FPS: ' + str(1 // (self.ms))

    def run(self):

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            self.ms = self.clock.tick(100) / 1000  # Time between two frames in seconds
            self.screen.fill((80, 80, 80))
            pygame.display.set_caption("Learning AI; FPS: %s; Time elapsed: %s; Epoch: %s" % (1 // self.ms, round(pygame.time.get_ticks() / 1000, 1), ML.epoch))

            npc_group.update(self.ms)
            particle_group.update(self.ms)
            npc_group.draw(self.screen)
            particle_group.draw(self.screen)

            if (pygame.time.get_ticks() - ML.current_learn_tick) >= 5000:
                ML.learn()

            pygame.display.flip()


class Character(variables.Variables):
    move_commands = {
        'forward': (1, -1),
        'backward': (1, 1),
        'right': (0, 1),
        'left': (0, -1),
        'stop_y': (1, 0),
        'stop_x': (0, 0)
    }

    def __init__(self, pos=None):
        self.pos = pos if pos != None else self.spawn_randomly()
        self.real_pos = self.pos
        self.size = None
        self.move_direction = [0, 0]
        self.desired_direction = [0, 0]

    def move(self, direction):
        modifier = self.move_commands[direction]
        self.desired_direction[modifier[0]] = modifier[1]

    def spawn_randomly(self):
        return [random.randrange(0, self.screen_width // self.world_block_size),
                random.randrange(0, self.screen_width // self.world_block_size)]


class ML(variables.Variables):
    epoch = 1
    learn_start_tick = pygame.time.get_ticks()
    current_learn_tick = learn_start_tick

    def __init__(self, number_of_inputs, number_of_outputs):
        self.number_of_inputs = number_of_inputs
        self.number_of_outputs = number_of_outputs
        self.init_weight = math.sqrt(6 / (self.number_of_inputs + self.number_of_outputs))
        self.input = []
        self.good = 0
        self.bad = 0

        self.nodes_structure = [[random.uniform(-self.init_weight, self.init_weight) for input in range(self.number_of_inputs)] for outputs in range(self.number_of_outputs)]

    def __str__(self):
        return str(self.good) + " " + str(self.bad) + ": " + str(self.good-self.bad)

    def hypothesis(self):
        return [math.atan(sum(self.input[i] * self.nodes_structure[output][i] for i in range(self.number_of_inputs))) for output in range(self.number_of_outputs)]

    def mutate(self, mutation_coefficient):
        for i in range(len(self.nodes_structure)):
            for j in range(len(self.nodes_structure[i])):
                self.nodes_structure[i][j] += random.gauss(0, 1) / 3 * mutation_coefficient

    @staticmethod
    def learn():
        temp = sorted(list(npc_group), key=lambda x: (x.ml_algorithm.good - x.ml_algorithm.bad))
        temp = temp[0:round(len(temp) * 0.5)]
        npc_group.empty()
        for i in temp:
            npc_group.add(i)
            mutable_algorithm = copy.deepcopy(i.ml_algorithm)
            mutable_algorithm.mutate(0.3)
            asd = NPC(mutable_algorithm, 35)
            npc_group.add(asd)

        ML.epoch += 1
        ML.current_learn_tick = pygame.time.get_ticks()


class NPC(Character, pygame.sprite.Sprite):
    def __init__(self, ml, vision_radius, pos=None, color=None):
        pygame.sprite.Sprite.__init__(self)
        Character.__init__(self, pos)

        self.ml_algorithm = ml
        self.vision_radius = vision_radius
        self.vision_sectors_number = self.ml_algorithm.number_of_inputs
        self.vision_sector_angle = 360 / self.ml_algorithm.number_of_inputs


        self.weapon = Weapon(self)

        self.size = self.world_block_size * 2, self.world_block_size * 2
        self.color = color if color != None else tuple(random.randrange(0, 256) for i in range(3))
        self.image = pygame.Surface(self.size)
        self.image.fill(self.color)
        self.real_speed = 4
        self.rect = self.image.get_rect()
        self.rect.x = self.real_pos[0]
        self.rect.y = self.real_pos[1]

    def __str__(self):
        return str(self.ml_algorithm)

    def calc_distance(self, other):
        return math.sqrt((other[0] - self.pos[0])**2 + (other[1] - self.pos[1])**2)

    def get_vision(self):
        temp = [-1 for i in range(self.vision_sectors_number)]
        for other in npc_group:
            if other != self and self.calc_distance(other.pos) <= self.vision_radius:
                temp[int(math.atan2(other.pos[1] - self.pos[1], other.pos[0] - self.pos[0]) //self.vision_sector_angle)] = 1
        return temp

    def take_action(self, ms):
        self.ml_algorithm.input = self.get_vision()
        hypothesis = self.ml_algorithm.hypothesis()
        # print(hypothesis)


        self.real_pos[0] = max(0, min((self.screen_width - self.rect.width) /self.world_block_size, self.real_pos[0] + hypothesis[0] * self.real_speed * ms))
        self.real_pos[1] = max(0, min((self.screen_height - self.rect.height) / self.world_block_size, self.real_pos[1] + hypothesis[1] * self.real_speed * ms))

        self.pos = list(map(round, self.real_pos))

        if hypothesis[2] > 0:
            self.weapon.shoot(math.atan2(hypothesis[1], hypothesis[0]))

    def update(self, ms):
        # print(self.ml_algorithm.good, self.ml_algorithm.bad)
        self.take_action(ms)
        self.rect.x = self.real_pos[0] * self.world_block_size
        self.rect.y = self.real_pos[1] * self.world_block_size


class Projectile(variables.Variables, pygame.sprite.Sprite):
    def __init__(self, parent, angle, lifetime, color=(255, 255, 255)):
        pygame.sprite.Sprite.__init__(self, particle_group)
        self.parent = parent
        self.image = pygame.Surface((self.world_block_size // 2, self.world_block_size // 2))
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.pos = self.parent.owner.pos[:]
        self.rect.x = self.pos[0]
        self.rect.y = self.pos[1]
        self.starttick = pygame.time.get_ticks()

        self.lifetime = lifetime
        self.real_speed = 20

        self.speed_x = self.real_speed * math.cos(angle)
        self.speed_y = self.real_speed * math.sin(angle)

    def update(self, ms):
        self.pos[0] += self.speed_x * ms
        self.pos[1] += self.speed_y * ms
        self.rect.x = self.pos[0] * self.world_block_size
        self.rect.y = self.pos[1] * self.world_block_size
        self.collision_detect()
        self.delete_on_time()

    def collision_detect(self):
        a = pygame.sprite.spritecollideany(self, npc_group)
        if a != None and a != self.parent.owner:
            a.ml_algorithm.bad += 1
            self.parent.owner.ml_algorithm.good += 1
            self.kill()

    def delete_on_time(self):
        if pygame.time.get_ticks() - self.starttick >= self.lifetime:
            self.kill()


class Ammo(variables.Variables):
    def __init__(self, owner, amount):
        self.owner = owner
        self.amount = amount

    def __call__(self, angle):
        if self.amount > 0 or self.amount == -1:
            self.amount -= 1 if self.amount != -1 else 0
            Projectile(self.owner, angle, 2500, color=(255, 255, 255))


class Weapon(variables.Variables):
    def __init__(self, owner):
        self.owner = owner
        self.ammo = Ammo(self, -1)
        self.shot_delay = 500

        self.last_shot_tick = 0

    def shoot(self, angle):
        if pygame.time.get_ticks() - self.last_shot_tick > self.shot_delay:
            self.last_shot_tick = pygame.time.get_ticks()
            self.ammo(angle)








if __name__ == '__main__':
    particle_group = pygame.sprite.Group()
    npc_group = pygame.sprite.Group()



    g = Main()
    for i in range(10):
        npc_group.add(NPC(ML(30, 3), 35)) #, pos=[variables.Variables.screen_width // 2 // variables.Variables.world_block_size,
                        # variables.Variables.screen_height // 2 // variables.Variables.world_block_size])
    g.run()
