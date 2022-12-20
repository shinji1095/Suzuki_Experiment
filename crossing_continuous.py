import socket
from config import HOST_IP, HOST_PORT
import pyrealsense2 as rs

from kivy.app import App
from kivy.properties import StringProperty
from kivy.uix.widget import Widget
from kivy.clock import Clock

from kivy.app import App
from kivy.uix.label import Label
from kivy.config import Config
from kivy.core.audio import SoundLoader

import math as m

# -------------------------- 変数 --------------------------
YAW_THRESH_INNER = 10
YAW_THRESH_OUTER = 20
PLAYER_INTERVAL = 3 # 音声通知の間隔[s]
FEEDBACK_INTERVAL = 0.1# フィードバックの間隔[s]


# -------------------------- GUI設定 --------------------------
Config.set('graphics', 'width', 600)
Config.set('graphics', 'height', 500)
Config.set('graphics', 'resizable', 1)



# -------------------------- Realsense初期設定 --------------------------
pipe = rs.pipeline()
cfg = rs.config()
cfg.enable_stream(rs.stream.pose)
pipe.start(cfg)



# -------------------------- Socket通信設定 --------------------------
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST_IP, HOST_PORT))



# -------------------------- 音声設定 --------------------------
sound_right = "./mp3/watch_out_right.mp3"
sound_left  = "./mp3/watch_out_left.mp3"
player_right = SoundLoader.load(sound_right)
player_left  = SoundLoader.load(sound_left)




max_walk = 2

class Widget(Widget):
    socket_command = b"none"

class RealsenseWidget(Label):
    text = StringProperty("")

    def __init__(self, **kwargs):
        super(RealsenseWidget, self).__init__(**kwargs)
        Clock.schedule_interval(self.update, FEEDBACK_INTERVAL)
        self.player_play_count = PLAYER_INTERVAL


    def update(self, dt):

        frames = pipe.wait_for_frames()
        pose = frames.get_pose_frame()
        data = pose.get_pose_data()
        w = data.rotation.w
        x = -data.rotation.z
        y = data.rotation.x
        z = -data.rotation.y
        yaw   =  m.atan2(2.0 * (w*z + x*y), w*w + x*x - y*y - z*z) * 180.0 / m.pi
        yaw_out_of_range = False if abs(yaw) <= YAW_THRESH_INNER else True

        if pose:
            self.text = str(yaw)
        else:
            self.text = "wait second..."
        
        if Widget.socket_command == b"none":
            pass    
        elif Widget.socket_command == b"off":
            s.send(Widget.socket_command)
            Widget.socket_command = b"none"
        
        elif Widget.socket_command == b"on" and yaw_out_of_range:
            command = b"on 100" if abs(yaw) >= YAW_THRESH_OUTER else b"on 50" 
            s.send(command)
            if self.player_play_count >= PLAYER_INTERVAL:
                self.player_play_count = 0
                if yaw >= 0: 
                    player_right.play()
                else: 
                    player_left.play()
            else:
                self.player_play_count += FEEDBACK_INTERVAL
                
        elif Widget.socket_command == b"on" and not yaw_out_of_range:
            # s.send(b"off")
            pass

        elif Widget.socket_command == b"finish": 
            s.send(Widget.socket_command)
            s.close()
            Widget.socket_command == b"none"
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

