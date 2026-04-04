import pygame

from .sub_component import SubComponent
from editor.timeline import *



class Timeline:
    def __init__(self, editor_timeline):
        self.__timeline = editor_timeline
        self.__last_render_start_frame = None
        self.__last_render_dims = (0, 0)
        self.__last_render_surface = None
        self.required_redraw = False
        self.pixels_per_second = 100
        self.fps = 30

        self.preview_segment = None

    def add_segment(self, segment):
        self.__timeline.add_segment(segment)

    def get_segment(self, frame_index):
        return self.__timeline.get_segment(frame_index)

    def get_frame(self, frame_index, preview_size):
        return self.__timeline.get_frame(frame_index, preview_size)

    @property
    def type(self):
        return "video" if isinstance(self.__timeline, TimelineVideo) else "audio"

    def _redraw(self, surface, start_frame):
        self.__last_render_start_frame = start_frame
        self.__last_render_dims = surface.get_size()
        self.__last_render_surface = surface

        pygame.draw.rect(
            surface, (50, 50, 50),
            (0, 0, *surface.get_size()),
            border_radius = 2
        )

        # Draw
        if self.type == "video":
            self._redraw_video(surface, start_frame)

        elif self.type == "audio":
            pass

        else:
            raise NotImplementedError

        pygame.draw.rect(
            surface, (25, 25, 25),
            (0, 0, *surface.get_size()),
            border_radius=2,
            width=2
        )

        self.preview_segment = None


    def _redraw_video(self, surface, start_frame):
        view_frame_count = (surface.get_width() / self.pixels_per_second) * self.fps

        def render_segment(segment: VideoSegment | AudioSegment | PhotoSegment):
            segment_end = segment.timeline_start + segment.duration

            if segment.timeline_start < start_frame + view_frame_count and segment_end > start_frame:
                media = segment.source
                colour = media.get_colour()

                width = (segment.duration / self.fps) * self.pixels_per_second
                start_x = ((segment.timeline_start - start_frame) / self.fps) * self.pixels_per_second

                pygame.draw.rect(
                    surface, colour,
                    (start_x + 2, 2, width - 4, surface.get_height() - 4),
                    border_radius=4
                )


        for segment in self.__timeline.segments:
            render_segment(segment)

        if self.preview_segment:
            render_segment(self.preview_segment)
            self.required_redraw = True

    def get_latest(self):
        return max([
            segment.timeline_start + segment.duration
            for segment in self.__timeline.segments
        ]) if len(self.__timeline.segments) > 0 else 0

    def coord_to_frame(self, x):
        return (x / self.pixels_per_second) * self.fps

    def make_segment_for(self, media, start_frame):
        if isinstance(media, Video):
            return VideoSegment(media, 0, media.length(), start_frame)
        if isinstance(media, Audio):
            return AudioSegment(media, 0, media.length(), start_frame)
        if isinstance(media, Photo):
            return PhotoSegment(media, media.length(), start_frame)

        raise NotImplementedError("Unknown media type: " + str(media))

    def create_segment(self, media, x):  # todo - make it snap / not overlay
        frame = self.coord_to_frame(max(0, x))
        segment = self.make_segment_for(media, start_frame=frame)

        if isinstance(media, Audio) and self.type != "audio":
            return None

        if not isinstance(media, Audio) and self.type == "audio":
            return None

        return segment

    def place_media(self, media, x):
        segment = self.create_segment(media, x)

        if segment:
            self.add_segment(segment)
            return True
        return False

    def preview_media(self, media, x):
        segment = self.create_segment(media, x)

        if segment is not None:
            self.preview_segment = self.create_segment(media, x)
            return True
        else:
            self.preview_segment = None
            return False

    def render(self, surface, start_frame):
        if self.required_redraw or self.preview_segment is not None:
            self._redraw(surface, start_frame)

        elif self.__last_render_start_frame != start_frame:
            self._redraw(surface, start_frame)

        elif self.__last_render_dims != surface.get_size():
            self._redraw(surface, start_frame)

        elif self.__last_render_surface is None:
            self._redraw(surface, start_frame)

        else:
            surface.blit(self.__last_render_surface, (0, 0))



class Timelines(SubComponent):
    def __init__(self, app):
        super().__init__()
        self.app = app

        self.playhead_frame = 0

        self.scroll_sens = 5  # ~167ms (1/6s)
        self.scroll_sens_fast = 60  # 2s
        self.scroll_offset = None

        self.timelines = [
            Timeline(TimelineVideo()),
            Timeline(TimelineVideo()),
            Timeline(TimelineVideo()),
            Timeline(TimelineAudio()),
            Timeline(TimelineAudio()),
            Timeline(TimelineAudio())
        ]

        self.__playhead_dragging = False
        self.__playhead_start_x = None

    def get_total_length(self):
        return max([
            timeline.get_latest()
            for timeline in self.timelines
        ])

    def calculate_new_surface_size(self, screen_width, screen_height) -> tuple[int, int]:
        return screen_width, 200

    def calculate_new_surface_position(self, screen_width, screen_height) -> tuple[int, int]:
        w, h = self.calculate_new_surface_size(screen_width, screen_height)
        return 0, screen_height - h

    def on_event(self, event):
        if event.type == pygame.MOUSEWHEEL:
            if self.scroll_offset is None:
                timeline = self.timelines[0]
                view_frame_count = ((self.surface.get_width() - 8) / timeline.pixels_per_second) * timeline.fps
                half_point = view_frame_count / 2

                if self.playhead_frame > half_point:
                    self.scroll_offset = self.playhead_frame - half_point
                else:
                    self.scroll_offset = 0

            sens = self.scroll_sens_fast if pygame.key.get_mods() & pygame.KMOD_SHIFT else self.scroll_sens
            delta = event.y * sens


            if (self.scroll_offset + delta) >= 0:
                self.scroll_offset += delta

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                mx, my = event.pos

                if my < 10:
                    offset = 0
                    timeline = self.timelines[0]
                    view_frame_count = ((self.surface.get_width() - 8) / timeline.pixels_per_second) * timeline.fps
                    half_point = view_frame_count / 2

                    if self.scroll_offset is None and self.playhead_frame > half_point:
                        offset = self.playhead_frame - half_point

                    if self.scroll_offset is not None:
                        offset = self.scroll_offset


                    playhead_x = self.get_playhead_location(-offset)

                    if playhead_x - 6 < mx < playhead_x + 7:
                        self.__playhead_dragging = True
                        self.__playhead_start_x = playhead_x

        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                if self.__playhead_dragging:
                    self.__playhead_dragging = False

        if event.type == pygame.MOUSEMOTION:
            if self.__playhead_dragging:
                offset = 0
                timeline = self.timelines[0]
                view_frame_count = ((self.surface.get_width() - 8) / timeline.pixels_per_second) * timeline.fps
                half_point = view_frame_count / 2

                if self.scroll_offset is None and self.playhead_frame > half_point:
                    offset = self.playhead_frame - half_point

                    if self.playhead_frame > half_point:
                        self.scroll_offset = self.playhead_frame - half_point
                    else:
                        self.scroll_offset = 0

                if self.scroll_offset is not None:
                    offset = self.scroll_offset

                #  (x / self.pixels_per_second) * self.fps
                frame_delta = timeline.coord_to_frame(event.pos[0])
                self.playhead_frame = frame_delta + offset


    def on_update(self, deltaTime):
        if self.app.widget_lookup["preview"].playing:
            self.playhead_frame += deltaTime * 30
            self.scroll_offset = None

        if self.get_total_length() < self.playhead_frame:
            self.app.widget_lookup["preview"].playing = False

    def get_playhead_location(self, frame_offset=0):
        """ Returns pixel x coord"""
        timeline = self.timelines[0]
        frame = self.playhead_frame + frame_offset
        return (frame * timeline.pixels_per_second) / timeline.fps

    def frame_to_cord(self, index):
        timeline = self.timelines[0]
        return (index / timeline.fps) * timeline.pixels_per_second

    def get_virtual_screen_x_offset(self):
        if self.scroll_offset is None:
            timeline = self.timelines[0]
            view_frame_count = ((self.surface.get_width() - 8) / timeline.pixels_per_second) * timeline.fps
            half_point = view_frame_count / 2

            if self.playhead_frame > half_point:
                return self.frame_to_cord(self.playhead_frame - half_point)
            return 0
        else:
            return self.frame_to_cord(self.scroll_offset)

    def preview_drop(self, media, x, y):
        timeline = self.get_timeline(media, x, y)

        if timeline:
            return timeline.preview_media(media, x + self.get_virtual_screen_x_offset()-4)
        return None

    def drop_media(self, media, x, y):
        timeline = self.get_timeline(media, x, y)

        if timeline:
            return  timeline.place_media(media, x + self.get_virtual_screen_x_offset()-4)
        return None

    def get_timeline(self, media, x, y):
        height_delta = self.surface.get_height() / len(self.timelines)
        timeline_index = int((y - 3) // height_delta)

        if 0 <= timeline_index < len(self.timelines):
            return self.timelines[timeline_index]
        return None


    def on_draw(self):
        self.surface.fill(self.app.BACKGROUND_COLOR)
        height_delta = self.surface.get_height() / len(self.timelines)

        timeline = self.timelines[0]
        view_frame_count = ((self.surface.get_width() - 8) / timeline.pixels_per_second) * timeline.fps
        half_point = view_frame_count / 2
        timeline_frame_offset = self.scroll_offset if self.scroll_offset is not None else 0
        playhead_hover_frame = self.playhead_frame

        if self.scroll_offset is None and self.playhead_frame > half_point:
            timeline_frame_offset = self.playhead_frame - half_point
            playhead_hover_frame = half_point

        if self.scroll_offset is not None:
            playhead_hover_frame = self.playhead_frame - self.scroll_offset

        for i, timeline in enumerate(self.timelines):
            surface = pygame.Surface((self.surface.get_width() - 8, height_delta - 6))
            surface.fill(self.app.BACKGROUND_COLOR)
            timeline.render(surface, timeline_frame_offset)

            self.surface.blit(surface, (4, 3 + height_delta * i))

        playhead_location = ((playhead_hover_frame / timeline.fps) * timeline.pixels_per_second) + 4
        pygame.draw.line(
            self.surface,
            (255, 10, 10),
            (playhead_location, 4), (playhead_location, self.surface.get_height() - 4),
            width=1
        )

        pygame.draw.polygon(
            self.surface,
            (255, 10, 10),
            [
                (playhead_location, 10), (playhead_location-6, 1), (playhead_location+7, 1)
            ]
        )

        self.draw_boarder((100, 100, 100))