import numpy as np
import cv2 as cv
import pygame
from PIL import Image
import random


class Media:
    def __init__(self, path):
        self.path = path
        self.cache = None
        self.colour = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))


    def get_colour(self):
        return self.colour

    def get_thumbnail(self):
        """ Returns a pygame surface representing the thumbnail of the media (100x100 pixels)"""
        raise NotImplementedError()

    def length(self):
        raise NotImplementedError()


class Video(Media):
    def __init__(self, path):
        super().__init__(path)
        self.__is_ready = False
        self.cap: cv.VideoCapture | None = None
        self.frame = 0

    def is_ready(self):
        return self.__is_ready

    def ready(self):
        self.cap = cv.VideoCapture(self.path)
        self.__is_ready = True

    def unload(self):
        self.cap.release()
        self.__is_ready = False

    def frame_count(self):
        if not self.is_ready():
            self.ready()

        return int(self.cap.get(cv.CAP_PROP_FRAME_COUNT))

    def length(self):
        if not self.is_ready():
            self.ready()

        return self.frame_count() / (self.fps() / 30)

    def fps(self):
        if not self.is_ready():
            self.ready()

        return self.cap.get(cv.CAP_PROP_FPS)

    def _get_thumbnail(self):
        frame_idx = int(self.cap.get(cv.CAP_PROP_POS_FRAMES))

        self.seek(self.frame_count() // 2)
        frame = self.next_frame(preview=(100, 100))
        self.seek(frame_idx)  # Reset Pointer

        if frame is not None:
            frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)

            surface = pygame.image.frombuffer(
                frame.tobytes(),
                frame.shape[1::-1],  # (width, height)
                "RGB"
            )

            return surface.convert()

        else:
            return pygame.image.load("data/src/images/video.png").convert()



    def get_thumbnail(self):
        if self.is_ready():
            return self._get_thumbnail()
        else:
            self.ready()
            thumbnail = self._get_thumbnail()
            self.unload()
            return thumbnail

    def seek(self, frame_index):
        if not self.is_ready():
            self.ready()

        self.cap.set(cv.CAP_PROP_POS_FRAMES, frame_index)
        self.frame = frame_index

    def next_frame(self, preview):
        if not self.is_ready():
            self.ready()

        ret, frame = self.cap.read()

        if not ret:
            return None

        if preview is not None:
            w, h = self.cap.get(cv.CAP_PROP_FRAME_WIDTH), self.cap.get(cv.CAP_PROP_FRAME_HEIGHT)
            scale_x = preview[0] / w
            scale_y = preview[1] / h
            scale = min(scale_x, scale_y)


            frame = cv.resize(frame, (round(w * scale), round(h * scale)), interpolation=cv.INTER_AREA)

        self.frame += 1
        return frame


class Photo(Media):
    def __init__(self, path):
        super().__init__(path)

        self.img = Image.open(path).convert("RGBA")

    def get_thumbnail(self):
        pil_img = self.img.copy()
        pil_img.thumbnail((100, 100))

        return pygame.image.frombuffer(
            pil_img.tobytes(),
            pil_img.size,
            pil_img.mode
        )

    def length(self):
        """ Returns the length of the time the photo is visible for """
        return 1



class Audio(Media):
    def __init__(self, path):
        super().__init__(path)

    def get_thumbnail(self):
        return pygame.image.load("data/src/images/audio.png").convert()

    def length(self):  # todo
        """ Returns the length of the time the photo is visible for """
        return 5