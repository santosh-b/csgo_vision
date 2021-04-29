import torch
import keyboard
from PIL import Image, ImageDraw, ImageTk
from tkinter import Tk, PhotoImage, Label
import win32gui, win32api, win32con
import numpy as np
import cv2
import d3dshot
import time
from threading import Thread

model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True).cuda()
model.classes = [0]
model.conf = .6
d = d3dshot.create(capture_output='numpy', frame_buffer_size=1)
d.display = d.displays[0]

pred = None
mid = None
region = None
aimbox = None
del_x = None
del_y = None
size = 600


def main():
    global mid, region
    hwnd = win32gui.FindWindow(None, 'Counter-Strike: Global Offensive')
    rect = win32gui.GetWindowRect(hwnd)
    mid = np.array([(rect[0]+rect[2])/2, (rect[1]+rect[3])/2])
    region = (int(mid[0]-size//2),int(mid[1]-size//2),int(mid[0]+size//2),int(mid[1]+size//2))
    
    Thread(target=capture, args=(region, ), daemon=True).start()
    #Thread(target=inference, daemon=True).start()
    Thread(target=aimbot, daemon=True).start()
    
    app = App()
    app.mainloop()
    
    
def aimbot():
    global pred, mid, region, aimbox, del_x, del_y
    while True:

        with torch.no_grad():
            x = d.get_latest_frame()
            if x is not None:
                #start = time.time()
                pred = model(x)
                #print(pred.xywh)
                #print('inference',time.time()-start)

        #print(pred)
        # find closest box to crosshair

        if pred is not None and pred.xywh[0].shape[0] > 0:
            max_dist = np.inf
            aim = np.inf
            aimbox = None
            for i, p in enumerate(pred.xywh):
                #print(p[0])
                x, y, w, h, _, _ = p[0]
                x = x.item() + region[0]
                y = y.item() + region[1]
                w, h = w.item(), h.item()
                box = np.array((x+w//2, y+h//2))
                if np.linalg.norm(box-mid) < max_dist:
                    aim = i
                    aimbox = box
            #print(aimbox, mid)
            del_x = int(1.7*(aimbox[0] - mid[0] - w // 2))
            del_y = int(1.7*(aimbox[1] - mid[1] - h // 2) - h*.9)
            print(del_x, del_y)
            win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, del_x, del_y, 0, 0)
            time.sleep(0.05)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, del_x, del_y, 0, 0)
            time.sleep(0.1)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, del_x, del_y, 0, 0)

            
def capture(region):
    d.capture(region=region, target_fps=120)

    
# def inference():
#     global pred
#     model.eval()
#     while True:
#         with torch.no_grad():
#             x = d.get_latest_frame()
#             if x is not None and keyboard.is_pressed('shift'):
                #start = time.time()
#                pred = model(x)
                #print(pred.xywh)
                #print('inference',time.time()-start)
            #time.sleep(.01)

            
class App(Tk):
    def __init__(self):
        Tk.__init__(self)
        self.img = None
        self.label = Label(image=self.img)
        self.label.pack()
        self._update_loop()
        
    def _update_loop(self, event=None):
        #start = time.time()
        x = d.get_latest_frame()
        if x is not None and pred is not None:
            x_im = Image.fromarray(x)
            x_draw = ImageDraw.Draw(x_im)
            for item in pred.xywh[0]:
                x1, y1, w, h, conf, res = item
                x_draw.rectangle((x1-w/2, y1-h/2, x1+w/2, y1+h/2), outline='red', width=3)
                #print(aimbox)
                if aimbox is not None:
                    try:
                        x_draw.regular_polygon((aimbox[0]-region[0]-w.item()//2, aimbox[1]-region[1]-h.item()//2, 10), n_sides=6, fill='green')
                    except:
                        pass
            self.img = ImageTk.PhotoImage(image=x_im)
            self.label.configure(image=self.img)
        #print('disp',time.time()-start)
        self.after(1, self._update_loop)

        
if __name__ == '__main__':
    main()