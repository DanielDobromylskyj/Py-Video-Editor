import cv2
import pygame

from editor.media import Video
from editor.timeline import VideoSegment
from .sub_component import SubComponent


class PreView(SubComponent):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.playing = False


    def calculate_new_surface_size(self, screen_width, screen_height) -> tuple[int, int]:
        return min(screen_width * (2/3), 800), screen_height - 50 - 200

    def calculate_new_surface_position(self, screen_width, screen_height) -> tuple[int, int]:
        w, h = self.calculate_new_surface_size(screen_width, screen_height)
        return screen_width - w, self.app.widget_lookup["topbar"].size[1]

    def on_event(self, event):
        pass

    def on_draw(self):
        self.surface.fill(self.app.BACKGROUND_COLOR)
        self.draw_boarder((100, 100, 100))

        timeline_manager = self.app.widget_lookup["timelines"]
        playhead_frame = timeline_manager.playhead_frame

        preview_size = (self.size[0] - 4, self.size[1] - 4)

        for timeline in timeline_manager.timelines:
            frame = timeline.get_frame(playhead_frame, preview_size=preview_size)

            if frame is not None:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                surface = pygame.image.frombuffer(
                    frame.tobytes(),  # unavoidable copy here. my poor performance
                    frame.shape[1::-1],  # (width, height)
                    "RGB"
                )



                self.surface.blit(surface, (
                    (self.surface.get_width() - surface.get_width()) / 2,
                    (self.surface.get_height() - surface.get_height()) / 2
                ))


    def on_update(self, deltaTime):
        if self.playing:
            self.required_redraw = True
