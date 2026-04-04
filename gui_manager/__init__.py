import pygame

from .topbar import Topbar
from .pre_viewer import PreView
from .timeline import Timelines
from .media_manager import MediaManager

pygame.init()

class App:
    BACKGROUND_COLOR = (14, 14, 14)

    def __init__(self, title, size=None):
        if size is None:
            size = pygame.display.get_desktop_sizes()[0]

        self.screen = pygame.display.set_mode(size, flags=pygame.RESIZABLE)
        self.blit_loading()

        self.clock = pygame.time.Clock()

        pygame.display.set_caption(title)

        self.debug_font = pygame.font.SysFont("Monospace", 14)
        self.debug = True

        self.__widgets = []
        self.__full_redraw = True
        self.running = True
        self.active_widget = None

        self.loading_assets = {}

        self.widget_lookup = {
            "topbar": Topbar(self),
            "preview": PreView(self),
            "timelines": Timelines(self),
            "media": MediaManager(self)
        }

        self.load()

        self.dragging = False
        self.dragging_surface = None
        self.dragging_type = None
        self.dragging_data = None
        self.dragging_pos = (0, 0)

    def load_assets(self):
        for name, path in self.loading_assets.items():
            print(f"[Loading] Asset: '{name}' @ '{path}'")
            img = pygame.image.load(path).convert_alpha()
            setattr(self, f"asset_{name}", img)

    def blit_loading(self):
        font = pygame.font.SysFont("Monospace", 24)
        text = font.render("Starting Editor", True, (255, 255, 255))

        self.screen.blit(text, ((self.screen.get_width()  - text.get_width())  / 2,
                                     (self.screen.get_height() - text.get_height()) / 2))
        pygame.display.flip()

    def start_dragging(self, drag_type: str, surface, dragging_data=None):
        self.dragging = True
        self.dragging_surface = surface
        self.dragging_type = drag_type
        self.dragging_data = dragging_data
        self.dragging_pos = pygame.mouse.get_pos()

    def stop_dragging(self):
        if self.dragging_type == "media":
            timelines: Timelines = self.widget_lookup["timelines"]

            mx, my = pygame.mouse.get_pos()
            dx, dy = mx - timelines.pos[0], my - timelines.pos[1]
            if 0 <= dx < timelines.size[0] and 0 <= dy < timelines.size[1]:
                timelines.drop_media(self.dragging_data, dx, dy)

        # Reset
        self.dragging = False
        self.dragging_surface = None
        self.dragging_type = None
        self.dragging_pos = (0, 0)

    def load(self):
        screen_dims = self.screen.get_size()
        for key, widget in self.widget_lookup.items():
            widget.on_resize(*screen_dims)
            self.add_widget(widget)
            print(f"[Loading] Initialized '{key}' widget")

    def touch_widget(self, widget):
        """ Moves the widget to the top of the screen. """
        self.__widgets.remove(widget)
        self.__widgets.append(widget)

    def on_resize(self, width, height):
        pygame.display.set_mode((width, height), flags=pygame.RESIZABLE)

        for widget in self.__widgets:
            widget.on_resize(width, height)

    def add_widget(self, widget):
        self.__widgets.append(widget)

        if not self.active_widget:
            self.active_widget = widget

    def on_draw(self):
        reset_cursor = True
        for i, widget in enumerate(self.__widgets):
            widget.on_draw()  # Updates widgets internal surface
            self.screen.blit(widget.surface, widget.pos)

        if self.dragging:
            x, y = self.dragging_pos
            self.screen.blit(self.dragging_surface, (x, y))

            if self.dragging_type == "media":
                timelines: Timelines = self.widget_lookup["timelines"]

                dx, dy = x - timelines.pos[0], y - timelines.pos[1]
                if 0 <= dy < timelines.size[1]:
                    result = timelines.preview_drop(self.dragging_data, dx, dy)

                    if result is False:
                        reset_cursor = False
                        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_NO)

        if reset_cursor and pygame.mouse.get_cursor() != pygame.SYSTEM_CURSOR_ARROW:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

        self.__full_redraw = False

    def set_active(self, target):
        for widget in self.__widgets:
            if widget == target:
                widget.active = True
                self.active_widget = widget
            else:
                widget.active = False

    def on_event(self, event):
        # Global (Pre-Widgets)
        if self.dragging:
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self.stop_dragging()
                return

            if event.type == pygame.MOUSEMOTION and event.buttons[0] == 1:
                self.dragging_pos = event.pos

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p:
                previewer = self.widget_lookup["preview"]

                if previewer.playing:
                    previewer.playing = False

                elif previewer:
                    previewer.playing = True

        # Widgets
        if hasattr(event, 'pos') and type(event.pos) is tuple:
            for widget in self.__widgets:
                if ((widget.pos[0] < event.pos[0] < widget.pos[0] + widget.size[0]) and
                    (widget.pos[1] < event.pos[1] < widget.pos[1] + widget.size[1])):
                    self.set_active(widget)

            if self.active_widget:
                event.pos = (event.pos[0] - self.active_widget.pos[0], event.pos[1] - self.active_widget.pos[1])

        if self.active_widget:
            self.active_widget.on_event(event)

        return

    def on_update(self, dT):
        for widget in self.__widgets:
            widget.on_update(dT)

    def start(self):
        while self.running:
            dT = self.clock.get_time() / 1000

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                elif event.type == pygame.WINDOWRESIZED:
                    self.on_resize(event.x, event.y)

                else:
                    self.on_event(event)

            self.on_update(dT)
            self.on_draw()

            if self.debug:
                lines = (
                    f"FPS: {self.clock.get_fps():.1f}",
                    f"deltaTime: {dT:.3f}",
                )

                y = 2
                for line in lines:
                    rect = self.debug_font.render(line, True, (255, 0, 0))
                    self.screen.blit(rect, (2, y))
                    y += rect.get_height() + 1

            self.clock.tick(30)
            pygame.display.flip()


