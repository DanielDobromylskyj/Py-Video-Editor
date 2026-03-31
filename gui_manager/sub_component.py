import pygame, random


class SubComponent:
    def __init__(self):
        self.surface = None # pygame.Surface(size)
        #self.surface.fill((random.randint(10,255), random.randint(10,255), random.randint(10,255)))

        self.pos = None #location
        self.size = None #size

        self.old_pos = (0, 0)
        self.old_size = (0, 0)

        self.required_redraw = True
        self.active = False

    def calculate_new_surface_size(self, screen_width, screen_height) -> tuple[int, int]:
        raise NotImplementedError

    def calculate_new_surface_position(self, screen_width, screen_height) -> tuple[int, int]:
        raise NotImplementedError

    def on_resize(self, width, height):
        self.size = self.calculate_new_surface_size(width, height)
        self.pos = self.calculate_new_surface_position(width, height)

        new_surface = pygame.Surface(self.size)

        if self.surface:
            new_surface.blit(self.surface, (0, 0))

        self.surface = new_surface
        self.required_redraw = True

    def draw_boarder(self, colour):
        pygame.draw.rect(self.surface, colour, (0, 0, *self.size), width=2, border_radius=2)

    def on_draw(self):
        raise NotImplementedError

    def on_event(self, event):
        raise NotImplementedError

    def on_update(self, deltaTime):
        pass

