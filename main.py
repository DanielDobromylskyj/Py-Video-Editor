from gui_manager import App
from editor.media import Video
from editor.timeline import VideoSegment


class VideoEditor(App):
    def __init__(self):
        super().__init__("Video Editor", (800, 800))


if __name__ == "__main__":
    app = VideoEditor()

    test_media = Video("data.mkv")
    timeline = app.widget_lookup["timelines"].timelines[0]

    test_segment = VideoSegment(test_media, 0, test_media.length(), 20)
    timeline.add_segment(test_segment)

    app.start()