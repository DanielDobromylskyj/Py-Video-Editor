import math
import pygame

import tkinter as tk
from tkinter import filedialog

from .sub_component import SubComponent
from editor.media import Video, Photo, Audio

root = tk.Tk()
root.withdraw()  # hide the main window


class MediaManager(SubComponent):
    def __init__(self, app):
        super().__init__()
        self.app = app

        self.media = []
        self.required_redraw = True
        self.scroll = 0

        self.font = pygame.font.SysFont("Monospace", 18, bold=True)

        self.extensions = {
            "mp4": Video,
            "avi": Video,
            "webm": Video,
            "mkv": Video,
            "flv": Video,
            "mov": Video,
            "mpeg": Video,
            "mpg": Video,
            "wmv": Video,

            "png": Photo,
            "jpeg": Photo,
            "jpg": Photo,
            "webp": Photo,
            "bmp": Photo,
            "gif": Photo,
            "tiff": Photo,
            "tif": Photo,

            "wav": Audio,
            "mp3": Audio,
            "m4a": Audio,
            "flac": Audio,
            "ogg": Audio
        }

    def request_file(self):
        return filedialog.askopenfilename(
            filetypes=[
                ("Video files", "*.mp4 *.avi *.mkv *.webm *.flv *.mov *.mpeg *.mpg *.wmv"),
                ("Images", "*.png *.jpg *.jpeg *.bmp *.webp *.tif *.tiff"),
                ("Audio", "*.wav *.mp3 *.flac *.ogg *.m4a"),
                ("All files", "*.*")
            ]
        )

    def calculate_new_surface_size(self, screen_width, screen_height) -> tuple[int, int]:
        return min(max(screen_width * (1/3), 110), 320), screen_height - 50 - 200

    def calculate_new_surface_position(self, screen_width, screen_height) -> tuple[int, int]:
        return 0, self.app.widget_lookup["topbar"].size[1]

    def new_media(self, path) -> bool:
        """ Attempts to create a new media object, returns a boolean success value """
        extension = path.split(".")[-1]

        if extension not in self.extensions:
            return False

        media_type = self.extensions[extension]
        media = media_type(path)
        self.media.append(media)
        self.required_redraw = True
        return True

    def on_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.pos[1] < 24:
                path = self.request_file()
                if path:
                    self.new_media(path)

            else:
                x, y = event.pos

                per_row = self.surface.get_width() // 105
                media_x_count = ((x - 5) // 105)
                media_y_count = ((y - 25) // 105)

                media_index = media_y_count * per_row + media_x_count

                if 0 <= media_index < len(self.media):
                    media = self.media[media_index]
                    thumbnail = media.get_thumbnail()
                    self.app.start_dragging("media", thumbnail, dragging_data=media)

    def on_draw(self):
        if self.required_redraw:
            self.surface.fill(self.app.BACKGROUND_COLOR)

            text = self.font.render("New Media", True, (255, 255, 255))

            pygame.draw.rect(
                self.surface,
                (0, 184, 255),
                (5, 4, self.surface.get_width() - 10, 20),
                border_radius=2
            )

            self.surface.blit(text, ((self.surface.get_width() - text.get_width()) / 2, 4))

            # Render Thumbnails - todo: Add boarder boxes?
            per_row = self.surface.get_width() // 105

            media_offset = self.scroll * per_row

            media_x_count = 0
            media_y_count = 0
            for i in range(media_offset, len(self.media)):
                media = self.media[i]

                thumbnail = media.get_thumbnail()

                self.surface.blit(thumbnail, (5 + media_x_count * 105, 25 + media_y_count * 105))

                media_x_count += 1
                if media_x_count >= per_row:
                    media_x_count = 0
                    media_y_count += 1


            self.draw_boarder((100, 100, 100))

