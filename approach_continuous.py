import socket
import time
import traceback
from config import HOST_IP, HOST_PORT
import pyrealsense2 as rs
from multiprocessing import Process

from kivy.app import App
from kivy.properties import StringProperty
from kivy.uix.widget import Widget
from kivy.clock import Clock

from kivy.app import App
from kivy.uix.label import Label


#ライブラリのインポート
from kivy.app import App
from kivy.config import Config
from kivy.uix.widget import Widget
from kivy.lang import Builder
from kivy.properties import StringProperty

#ウインドウの幅と高さの設定
Config.set('graphics', 'width', 600)
Config.set('graphics', 'height', 500)
#1でサイズ変更可、0はサイズ変更不可
Config.set('graphics', 'resizable', 1)

# -------------------------- Realsense初期設定 --------------------------
pipe = rs.pipeline()
cfg = rs.config()
cfg.enable_stream(rs.stream.pose)
pipe.start(cfg)

# -------------------------- Socket通信設定 --------------------------
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST_IP, HOST_PORT))

max_walk = 2

class Widget(Widget):
    socket_command = b"none"

class RealsenseWidget(Label):
    text = StringProperty("")

    def __init__(self, **kwargs):
        super(RealsenseWidget, self).__init__(**kwargs)
        Clock.schedule_interval(self.update, 1)

    def update(self, dt):

        frames = pipe.wait_for_frames()
        pose = frames.get_pose_frame()
        data = pose.get_pose_data()
        walk_distance = data.translation.z
        if pose:
            self.text = str(walk_distance)
        else:
            self.text = "wait second..."
        
        if Widget.socket_command == b"none":
            pass
        elif  Widget.socket_command == b"off":
            s.send(Widget.socket_command)
            Widget.socket_command = b"none"

        elif Widget.socket_command == b"finish":
            s.send(Widget.socket_command)
            s.close() 
            Widget.socket_command = b"none"

        elif Widget.socket_command == b"on": 
            duty = abs(walk_distance) // (max_walk / 10) * 10
            duty = duty if duty <= 100 else 100
            duty = int(duty)
            print(f"Duty ratio : {duty}")
            command = f"on {duty}".encode()
            s.send(command)
        else:
            pass

class ButtonWidget(Widget):
    def __init__(self, **kwargs):
        super(ButtonWidget, self).__init__(**kwargs)

    def press1(self):
        Widget.socket_command = b"on"
        self.ids.rs_widget.text = "Vibrate turn on"

    def press2(self):
        Widget.socket_command = b"off"
        self.ids.rs_widget.text = "Vibrate turn off"

    def press3(self):
        Widget.socket_command = b"finish"
        self.ids.rs_widget.text = "Connection done"

class SuzukiApp(App):
    def build(self):
        self.title = "window"
        return ButtonWidget()

    def stop(self, *largs):
        pipe.stop()
        return super().stop(*largs)

if __name__ == '__main__':
    SuzukiApp().run()

