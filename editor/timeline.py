import math

from .media import Video, Audio, Photo

class VideoSegment:
    def __init__(self, source: Video, source_start: int, source_duration: int, timeline_start: int):
        """ All Starts / Durations are in Frames"""
        self.source: Video = source
        self.source_start: int = source_start
        self.source_end: int = source_start + source_duration
        self.duration = source_duration
        self.timeline_start: int = timeline_start
        self.fps = source.fps()

class AudioSegment:
    def __init__(self, source: Audio, source_start: int, source_duration: int, timeline_start: int):
        """ All Starts / Durations are in Frames"""
        self.source: Audio = source
        self.source_start: int = source_start
        self.source_end: int = source_start + source_duration
        self.duration = source_duration
        self.timeline_start: int = timeline_start
        self.fps = 60

class PhotoSegment:
    def __init__(self, source: Photo, source_duration: int, timeline_start: int):
        """ All Starts / Durations are in Frames"""
        self.source: Photo = source
        self.duration = source_duration
        self.timeline_start: int = timeline_start
        self.fps = 60



class Timeline:
    def __init__(self):
        self.segments: list[VideoSegment] = []
        self.next_frame = 0
        self.current_segment = None
        self.last_frame = None


    def add_segment(self, segment: VideoSegment):
        self.segments.append(segment)

    def get_segment(self, frame_index: int) -> VideoSegment | None:
        for segment in self.segments:
            if segment.timeline_start <= frame_index < segment.timeline_start + segment.duration:
                return segment
        return None

    def get_frame(self, playhead_frame, preview_size):
        segment: VideoSegment = self.get_segment(playhead_frame)

        if segment != self.current_segment:
            self.next_frame = 0

        if segment:
            source: Video = segment.source
            speed = segment.fps / 30

            source_offset = math.floor((playhead_frame - segment.timeline_start) * speed)
            source_frame = source_offset + segment.source_start

            if source_frame == source.frame - 1:
                return self.last_frame

            if source_frame != source.frame:
                source.seek(source_frame)

            frame = source.next_frame(preview=preview_size)

            self.current_segment = segment

            self.last_frame = frame
            return frame

        self.current_segment = None
        return None



class TimelineVideo(Timeline):
    def __init__(self):
        super().__init__()


class TimelineAudio(Timeline):
    def __init__(self):
        super().__init__()