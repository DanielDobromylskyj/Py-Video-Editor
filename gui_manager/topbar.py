from .sub_component import SubComponent

class Topbar(SubComponent):
    def __init__(self, app):
        super().__init__()
        self.app = app

    def calculate_new_surface_size(self, screen_width, screen_height) -> tuple[int, int]:
        return screen_width, 50

    def calculate_new_surface_position(self, screen_width, screen_height) -> tuple[int, int]:
        return 0, 0

    def on_event(self, event):
        pass

    def on_draw(self):
        self.surface.fill(self.app.BACKGROUND_COLOR)
        self.draw_boarder((100, 100, 100))