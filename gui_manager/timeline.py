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

    def create_segment(self, media, x):  # todo - use the offset position too
        frame = self.coord_to_frame(max(0, x))
        segment = self.make_segment_for(media, start_frame=frame)

        if isinstance(media, Audio) and self.type != "audio":
            return None

        return segment

    def place_media(self, media, x):
        segment = self.create_segment(media, x)

        if segment:
            self.add_segment(segment)

    def preview_media(self, media, x):
        self.preview_segment = self.create_segment(media, x)

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

    def calculate_new_surface_size(self, screen_width, screen_height) -> tuple[int, int]:
        return screen_width, 200

    def calculate_new_surface_position(self, screen_width, screen_height) -> tuple[int, int]:
        w, h = self.calculate_new_surface_size(screen_width, screen_height)
        return 0, screen_height - h

    def on_event(self, event):
        if event.type == pygame.MOUSEWHEEL:
            if self.scroll_offset is None:
                self.scroll_offset = 0  # todo - get current playhead location

            sens = self.scroll_sens_fast if pygame.key.get_mods() & pygame.KMOD_SHIFT else self.scroll_sens
            delta = event.y * sens


            if (self.scroll_offset + delta) >= 0:
                self.scroll_offset += delta



    def on_update(self, deltaTime):
        if self.app.widget_lookup["preview"].playing:
            self.playhead_frame += deltaTime * 30
            self.scroll_offset = None

    def preview_drop(self, media, x, y):
        timeline = self.get_timeline(media, x, y)

        if timeline:
            timeline.preview_media(media, x-4)

    def drop_media(self, media, x, y):
        timeline = self.get_timeline(media, x, y)

        if timeline:
            timeline.place_media(media, x-4)


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

        if self.scroll_offset is not None and self.playhead_frame > half_point:
            timeline_frame_offset = self.playhead_frame - half_point
            playhead_hover_frame = half_point

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

        self.draw_boarder((100, 100, 100))