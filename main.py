# Author : Sk Sahil 
# https://github.com/Sahil-pixel
# Date : (22/Aug/2025)
import kivy
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import Rectangle, Line, Color, PushMatrix, PopMatrix, Scale, Rotate
from kivy.graphics.texture import Texture
from kivy.clock import Clock, mainthread
from kivy.properties import BooleanProperty, StringProperty, NumericProperty, ListProperty
from kivy.uix.togglebutton import ToggleButton
from kivy.event import EventDispatcher
from kivy.core.camera import Camera as CoreCamera
from kivy.utils import platform
from kivy.uix.image import Image
from kivy.metrics import dp, sp
import numpy as np
import dlib
# Numpy Version <=1.26 is required
print("Numpy version  ", np.__version__)


class CameraWidget(RelativeLayout):
    play = BooleanProperty(False)
    index = NumericProperty(-1)
    resolution = ListProperty([-1, -1])
    _camera = None

    def __init__(self, **kwargs):
        super(CameraWidget, self).__init__(**kwargs)
        if self.index == -1:
            self.index = 0
        on_index = self._on_index
        fbind = self.fbind
        fbind('index', on_index)
        fbind('resolution', on_index)
        on_index()
        self.register_event_type('on_update')

        with self.canvas.before:
            self.rect = Rectangle(size=self.size, pos=(0, 0))

        self.bind(pos=self.update_rect, size=self.update_rect)

    def on_update(self, texture): pass
    # print(texture)

    def update_load(self, *args): pass
    # print(args)

    def update_texture(self, cam):
        #self.rect.texture = cam.texture
        # self.canvas.ask_update()
        self.dispatch('on_update', cam.texture)

    def update_rect(self, *args):
        self.rect.pos = (0, 0)
        self.rect.size = self.size

    def _on_index(self, *largs):
        self._camera = None
        if self.index < 0:
            return
        if self.resolution[0] < 0 or self.resolution[1] < 0:
            self._camera = CoreCamera(index=self.index, stopped=True)
        else:
            self._camera = CoreCamera(index=self.index,
                                      resolution=self.resolution, stopped=True)
        if self.play:
            self._camera.start()

        self._camera.bind(on_texture=self.update_texture)

    def on_play(self, obj, value):
        if not self._camera:
            return
        if value:
            self._camera.start()
        else:
            # setting texture none to clear display
            self.rect.texture = None
            self.canvas.ask_update()
            self._camera.stop()


class CameraApp(App):
    f_n = ''
    camera_index = 0

    def build(self):

        if platform == 'android':
            from android.permissions import request_permissions, Permission

            def callback(permissions, results):
                if all([res for res in results]):
                    print("callback. All permissions granted.")
                else:
                    print("callback. Some permissions refused.")

            request_permissions([Permission.CAMERA], callback)

        self.count = 0
        layout = BoxLayout(orientation='vertical',
                           spacing=dp(5), padding=dp(2))

        self.camera_widget = CameraWidget(play=False, size_hint=(1, 0.9))
        self.camera_widget.bind(on_update=self.update)
        capture_button = Button(text="P/S", size_hint=(1, 1))
        capture_button.bind(on_release=self.play_pause)
        title = Label(text="Dlib Python Face Detection on Kivy Android ",
                      font_size=sp(18), bold=True, size_hint_y=None, height=dp(50))
        self.num_faces = Label(text=self.f_n,
                               font_size=sp(17), bold=True, size_hint_y=None, height=dp(20))
        change_camera = ToggleButton(text="Change Camera")
        change_camera.bind(state=self.change_camera)
        box = BoxLayout(size_hint_y=0.1)
        box.add_widget(capture_button)
        box.add_widget(change_camera)
        layout.add_widget(title)
        layout.add_widget(self.num_faces)
        layout.add_widget(self.camera_widget)
        layout.add_widget(box)

        # Dlib detetector
        self.detector = dlib.get_frontal_face_detector()

        return layout

    def update(self, obj, texture):
        # print(texture)
        gray, rgba = self.texture_to_numpy(texture)
        # print(gray.shape)
        gray = gray.copy()

        # I use gray as it will be faster.
        # dlib collect faces from gray image comes (from kivy and numpy)

        faces = self.detector(gray, 0)

        self.f_n = f"Detected  faces : {len(faces)}"

        cords = []
        for i in range(len(faces)):
            face = faces[i]
            x, y, w, h = face.left(), face.top(), face.width(), face.height()

            cord = (x, y, w, h)
            cords.append(cord)

        if len(faces) == 0:
            cords = []

        self._texture_update(rgba)
        self._texture_update2(gray, cords)

    # You can use for further image process
    # But for this case it is not required

    @mainthread
    def _texture_update(self, frame,):
        h, w, _ = frame.shape
        # print(h,w,_)
        tex = Texture.create(size=(w, h), colorfmt='rgba')
        tex.blit_buffer(frame.tobytes(), colorfmt='rgba', bufferfmt='ubyte')
        # android  front camera it is recuired
        tex.flip_vertical()  # Optional if you want to flip vertically
        # tex.flip_horizontal()
        self.camera_widget.rect.texture = tex

        self.camera_widget.canvas.ask_update()

    @mainthread
    def _texture_update2(self, gray, cords):

        if cords:
            self.camera_widget.canvas.clear()
            for cord in cords:
                # print(cord)
                x, y, w, h = cord

                img_h, img_w = gray.shape[:2]   # numpy image size
                widget_w, widget_h = self.camera_widget.size

                # Scale factor between image and widget
                scale_x = widget_w / img_w
                scale_y = widget_h / img_h

                # Convert NumPy (x, y, w, h) → Kivy coords
                # Co-ordinate Transformation using maths
                kx = x * scale_x
                kh = h * scale_y
                kw = w * scale_x
                ky = (img_h - (y + int(h))) * scale_y   # flip y for kivy

                with self.camera_widget.canvas:
                    Color(0, 0, 1, 0.2)

                    Rectangle(pos=(kx, ky),
                              size=(kw, kh))
                    Color(0, 1, 0, 1)  # Green color
                    Line(rectangle=(kx, ky, kw, kh), width=dp(2))

        else:
            self.camera_widget.canvas.clear()

        # Update text of label in UI thread
        self.num_faces.text = self.f_n

        # self.camera_widget.canvas.ask_update()

        # do opencv stuff

    def texture_to_numpy(self, tex):
        """Convert Kivy texture to grayscale + RGBA (for display)"""
        # No need opencv or this numpy is enough to convert kivy texture to
        # RGBA or Gray for dlib
        pixels = tex.pixels
        width, height = tex.size

        # Convert bytes to NumPy RGBA array
        frame = np.frombuffer(pixels, dtype=np.uint8)
        frame = frame.reshape((height, width, 4))  # RGBA #widthxheightx4

        # Drop alpha, keep RGB
        rgb = frame[:, :, :3] #widthxheightx3

        # For android we need to rotate

        if platform == 'android':
            # Rotate 90 degrees counterclockwise

            if self.camera_index == 0:

                # rotate + mirror horizontally for back camera
                rgb = np.rot90(rgb, k=3) #k=3 if upside down
                rgb = np.fliplr(rgb)
                frame = np.rot90(frame, k=3)
                frame = np.fliplr(frame)

            elif self.camera_index == 1:
                # For front camera
                rgb = np.rot90(rgb, k=1)  # Adjust k=1 or k=3 if upside down
                frame = np.rot90(frame, k=1)

        # Convert to grayscale for dlib
        gray = (0.299 * rgb[:, :, 0] +
                0.587 * rgb[:, :, 1] +
                0.114 * rgb[:, :, 2]).astype(np.uint8)

        return gray, frame

    def change_camera(self, btn, state):
        if state == 'normal':
            # make camera off for safety
            self.camera_widget.play = False
            self.camera_index = 0
            self.camera_widget.index = self.camera_index
            btn.text = f"Camera Index {self.camera_index}"
            # camera start again
            self.camera_widget.play = True
        else:
            # make front camera
            self.camera_widget.play = False
            self.camera_index = 1
            self.camera_widget.index = self.camera_index
            # camera start again
            btn.text = f"Camera Index {self.camera_index}"
            self.camera_widget.play = True

    def play_pause(self, btn,):
        if self.camera_widget.play == False:
            self.camera_widget.play = True
        else:
            self.camera_widget.play = False
            self.count = 0
            self.camera_widget.canvas.clear()
            self.camera_widget.rect.texture = None
            self.camera_widget.canvas.ask_update()


if __name__ == '__main__':
    CameraApp().run()
