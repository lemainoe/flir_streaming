import clr # needs the "pythonnet" package
import sys
import os
import time
import platform

bits, name = platform.architecture()

if bits == "64bit":
	folder = ["x64"]
else:
	folder = ["x86"]

sys.path.append(os.path.join("..", *folder))
sys.path.append(os.path.join(*folder))

clr.AddReference("LeptonUVC")
from Lepton import CCI
import time
import tkinter
from tkinter import ttk
from tkinter import filedialog
from tkinter.constants import NSEW
from tkinter import *
import cv2
import PIL.Image, PIL.ImageTk
import numpy as np


class App:
    def __init__(self, window, window_title, video_source):
        self.window = window
        self.window.title(window_title)
        self.window.geometry("925x925")

        # create a main frame
        self.main_frame = tkinter.Frame(self.window)
        self.main_frame.pack(fill=BOTH, expand=1)

        # create a canvas for ALL
        self.canva_scroll = tkinter.Canvas(self.main_frame)
        self.canva_scroll.pack(side=LEFT, fill=BOTH, expand=1)
        # add a scrollbar to the canvas
        self.scrollbar_v = ttk.Scrollbar(
            self.main_frame, orient=VERTICAL, command=self.canva_scroll.yview)
        self.scrollbar_v.pack(side=RIGHT, fill=Y)
        # configure the canvas
        self.canva_scroll.configure(yscrollcommand=self.scrollbar_v.set)
        self.canva_scroll.bind('<Configure>', lambda e: self.canva_scroll.configure(
            scrollregion=self.canva_scroll.bbox("all")))
        # create another frame inside the canvas
        self.second_frame = tkinter.Frame(self.canva_scroll)
        # add that new frame to a window in the canvas
        self.canva_scroll.create_window(
            (0, 0), window=self.second_frame, anchor=NW)

        # Initialization
        self.video_source = video_source
        self.shutter_val = 0
        self.gain_val = 0
        self.lapse_val = 0
        self.lapse_end = 0
        self.block = []
        self.time_stamp = []
        self.max_want = IntVar(self.second_frame)
        self.max_want.set(400)
        self.min_want = IntVar(self.second_frame)
        self.min_want.set(0)
        self.change = 0
        self.max_frame = 5000  # almost 10 minutes of recording
        self.count_frame = 0
        self.folder_save = os.getcwd()

        # open video source
        self.vid = MyVideoCapture(self.video_source)

        # create a canvas that can fit the above video source size
        self.canvas = tkinter.Canvas(self.second_frame, width=740, height=640)
        self.canvas.grid(row=0, column=0, columnspan=3)

        # creating Labels and Buttons (order grid : up down, left right)
        self.myxy = tkinter.Label(self.second_frame, text="XY coordinates: ")
        self.myxy.grid(row=1, column=0, padx=5, pady=5)

        self.mytempxy = tkinter.Label(
            self.second_frame, text="Temperature in °C: ")
        self.mytempxy.grid(row=2, column=0, padx=5, pady=5)

        self.housing = tkinter.Label(
            self.second_frame, text="System temperature AUX in °C: ")
        self.housing.grid(row=3, column=0, padx=5, pady=5)

        self.core = tkinter.Label(
            self.second_frame, text="Operating temperature FPA in °C: ")
        self.core.grid(row=4, column=0, padx=5, pady=5)

        self.min_maxT = tkinter.Label(
            self.second_frame, text="Min/Max Temp in °C: ")
        self.min_maxT.grid(row=5, column=0, padx=5, pady=5)

        self.btn_flip = tkinter.Button(
            self.second_frame, text="Flip image", width=30, command=self.flip)
        self.btn_flip.grid(row=2, column=1, padx=5, pady=5)

        self.btn_shutter = tkinter.Button(
            self.second_frame, text="Close Shutter", width=30, command=self.shutter)
        self.btn_shutter.grid(row=3, column=1, padx=5, pady=5)

        self.btn_gain = tkinter.Button(
            self.second_frame, text="Gain-Mode: HIGH (140 °C) -> LOW", width=30, command=self.gain)
        self.btn_gain.grid(row=4, column=1, padx=5, pady=5)

        self.btn_tiff = tkinter.Button(
            self.second_frame, text="Timelapse OFF -> ON .tif", width=30, command=self.timelapse)
        self.btn_tiff.grid(row=5, column=1, padx=5, pady=5)

        self.btn_min = tkinter.Label(
            self.second_frame, text='Min Temp in scale (°C): ')
        self.btn_min.grid(row=1, column=2, padx=5)

        self.min_entry = tkinter.Scale(
            self.second_frame, orient='horizontal', from_=0, to=400, resolution=1, tickinterval=50, length=350, variable=self.min_want, takefocus=1)
        self.min_entry.grid(row=2, column=2, padx=5)

        self.btn_max = tkinter.Label(
            self.second_frame, text='Max Temp in scale (°C): ')
        self.btn_max.grid(row=3, column=2, padx=5)

        self.max_entry = tkinter.Scale(
            self.second_frame, orient='horizontal', from_=0, to=400, resolution=1, tickinterval=50, length=350, variable=self.max_want, takefocus=1)
        self.max_entry.grid(row=4, column=2, padx=5)

        self.btn_autoscale = tkinter.Button(
            self.second_frame, text='Autoscale', width=30, command=self.autoscale)
        self.btn_autoscale.grid(row=5, column=2, padx=5, pady=5)

        # after it is called once, the update method will be automatically called every 15ms
        self.delay = 15
        self.update()
        self.canvas.bind('<Motion>', self.motion)

        self.window.mainloop()


    # Inverse the image

    def flip(self):
        self.change = (self.change + 1) % 4

    # Take a timelapse and compress it in a tiff file

    def timelapse(self):
        if self.lapse_val == 0:
            self.btn_tiff.config(text="Timelapse ON -> OFF .tif")
            self.lapse_val = 1
            self.block = []
            self.time_stamp = []
            self.count_frame = 0

            # avoid the FFC Normalization during the record : manual
            shutterModeObj = self.lep.sys.GetFfcShutterModeObj()
            newshutterModeObj = shutterModeObj
            newshutterModeObj.shutterMode = 0  # 0: manual; 1: auto; 2: external
            self.lep.sys.SetFfcShutterModeObj(newshutterModeObj)
            self.lep.sys.RunFFCNormalization()
        else:
            self.btn_tiff.config(text="Timelapse OFF -> ON .tif")
            self.lapse_val = 0
            self.lapse_end = 1

            # set the FFC Normalization back to auto
            shutterModeObj = self.lep.sys.GetFfcShutterModeObj()
            newshutterModeObj = shutterModeObj
            newshutterModeObj.shutterMode = 1  # 0: manual; 1: auto; 2: external
            self.lep.sys.SetFfcShutterModeObj(newshutterModeObj)

    # Open/close the integrated shutter

    def shutter(self):
        if self.shutter_val == 0:
            self.lep.sys.SetShutterPosition(2)  # 2: closed
            self.btn_shutter.config(text="Open Shutter")
            self.shutter_val = 1
        else:
            self.lep.sys.SetShutterPosition(1)  # 1: opened
            self.btn_shutter.config(text="Close Shutter")
            self.shutter_val = 0

    # Change the Gain-Mode (default = HIGH Gain (0) -> up to 140°C; LOW Gain (1) -> up to 400°C; Auto (2))

    def gain(self):
        if self.gain_val == 0:
            self.btn_gain.config(text="Gain-Mode: LOW (400 °C) -> HIGH")
            self.lep.sys.SetGainMode(1)
            self.gain_val = 1
        else:
            self.btn_gain.config(text="Gain-Mode: HIGH (140 °C) -> LOW")
            self.lep.sys.SetGainMode(0)
            self.gain_val = 0

    # Movement of the mouse shows the temperature of the pixel

    def motion(self, event):
        self.x, self.y = event.x, event.y
        self.myxy.config(text="XY coordinates: " +
                         str(self.x) + ", " + str(self.y))
        self.tempx = (int)(self.x/4)
        self.tempy = (int)(self.y/4)

        # reference to the width of the different plots
        if self.change in (0, 2):  # frame: horizontal
            if self.tempx <= 160 and self.tempy <= 120:  # in the image sent by the camera
                self.val = round(
                    self.frame_flip[self.tempy-1, self.tempx-1], 2)
            elif 175 <= self.tempx < 185 and self.tempy < 120:  # in the colorbar
                self.val = round(
                    self.cb_gray[int(np.floor(self.y/480*255))-1][0], 2)
            else:
                self.val = '--'
        elif self.change in (1, 3):  # frame: vertical
            if self.tempx <= 120 and self.tempy <= 160:  # in the image sent by the camera
                self.val = round(
                    self.frame_flip[self.tempy-1, self.tempx-1], 2)
            elif 175 <= self.tempx < 185 and self.tempy < 160:  # in the colorbar
                self.val = round(
                    self.cb_gray[int(np.floor(self.y/640*255))-1][0], 2)
            else:
                self.val = '--'
        self.mytempxy.config(text="Temperature in °C: " + str(self.val))

    # Make an autoscale of the min and max value

    def autoscale(self):
        self.max_want.set(self.max_TC)
        self.min_want.set(self.min_TC)

    # Update routine for the new pictures

    def update(self):
        # Get a frame from the video source
        self.ret, self.frame, self.lep = self.vid.get_frame()

        if self.ret and self.lep.sys.GetFFCStatus() == 0:  # not doing FFC
            color = 2  # Colormap : Jet

            # temperature and data camera
            # with resolution 0.1; T° in °dK -> T° in °C
            self.frame_roi = self.frame[:-2, :]/10-273.15
            self.max_TC = round(np.max(self.frame_roi))
            self.min_TC = round(np.min(self.frame_roi))

            # update in labels
            self.housing.config(text="System temperature AUX in °C: " +
                                str(round(self.lep.sys.GetAuxTemperatureCelsius(), 1)))
            self.core.config(text="Operating temperature FPA in °C: " +
                             str(round(self.lep.sys.GetFpaTemperatureCelsius(), 1)))
            self.min_maxT.config(
                text="Min/Max Temp in °C: " + str(self.min_TC) + " / " + str(self.max_TC))

            # make sure that temp min < temp max in the scale
            if self.max_want.get() <= self.min_want.get():
                self.min_want.set(self.min_isok)
                self.max_want.set(self.max_isok)
            self.max_modif = self.max_want.get()
            self.min_modif = self.min_want.get()

            # rotation of the image 90° by 90°
            if self.change == 0:
                self.frame_flip = self.frame_roi
            elif self.change == 1:
                self.frame_flip = np.flip(self.frame_roi, 0).transpose()
            elif self.change == 2:
                self.frame_flip = np.flip(self.frame_roi)
            elif self.change == 3:
                self.frame_flip = np.flip(self.frame_roi.transpose(), 0)

            # color the image and normalize with the selected temperature
            self.normed = cv2.normalize(self.frame_flip, None, 255*(self.min_TC-self.min_modif)/(self.max_modif-self.min_modif), 255*(
                self.max_TC-self.min_modif)/(self.max_modif-self.min_modif), cv2.NORM_MINMAX, cv2.CV_8U)
            self.colorized_img = cv2.applyColorMap(self.normed, color)
            if self.change in (0, 2):  # frame: horizontal
                self.colorized_img = cv2.resize(self.colorized_img, dsize=(
                    640, 480), interpolation=cv2.INTER_LINEAR)
            elif self.change in (1, 3):  # frame: vertical
                self.colorized_img = cv2.resize(self.colorized_img, dsize=(
                    480, 640), interpolation=cv2.INTER_LINEAR)

            # creation colorbar
            self.cb_gray = np.arange(
                255, 0, -1, dtype=np.uint8).reshape((255, 1))  # column 255->1
            self.cb_color = cv2.applyColorMap(self.cb_gray, color)
            if self.change in (0, 2):  # frame: horizontal
                self.cb_color = cv2.resize(self.cb_color, dsize=(
                    40, 480), interpolation=cv2.INTER_LINEAR)
            elif self.change in (1, 3):  # frame: vertical
                self.cb_color = cv2.resize(self.cb_color, dsize=(
                    40, 640), interpolation=cv2.INTER_LINEAR)

            # between image and colorbar
            if self.change in (0, 2):  # frame: horizontal
                self.blank = np.ones((480, 60), dtype=np.uint8)*255
            elif self.change in (1, 3):  # frame: vertical
                self.blank = np.ones((640, 220), dtype=np.uint8)*255
            self.blank = cv2.applyColorMap(self.blank, 1)

            self.append_img = np.concatenate(
                (self.colorized_img, self.blank, self.cb_color), axis=1)

            # display the max and min temp on the white band
            if self.change in (0, 2):
                cv2.putText(img=self.append_img, text=str(self.max_modif), org=(
                    642, 20), fontFace=cv2.FONT_HERSHEY_PLAIN, fontScale=1, color=(0, 0, 0), thickness=1, lineType=8)
                cv2.putText(img=self.append_img, text=str(self.min_modif), org=(
                    642, 475), fontFace=cv2.FONT_HERSHEY_PLAIN, fontScale=1, color=(0, 0, 0), thickness=1, lineType=8)
            elif self.change in (1, 3):
                cv2.putText(img=self.append_img, text=str(self.max_modif), org=(
                    642, 20), fontFace=cv2.FONT_HERSHEY_PLAIN, fontScale=1, color=(0, 0, 0), thickness=1, lineType=8)
                cv2.putText(img=self.append_img, text=str(self.min_modif), org=(
                    642, 635), fontFace=cv2.FONT_HERSHEY_PLAIN, fontScale=1, color=(0, 0, 0), thickness=1, lineType=8)

            self.photo = PIL.ImageTk.PhotoImage(
                image=PIL.Image.fromarray(self.append_img))
            self.canvas.create_image(
                0, 0, image=self.photo, anchor=tkinter.NW)

            # saving timelapse in .tif
            if self.lapse_val == 1:
                t = time.time()
                self.block.append(PIL.Image.fromarray(
                    self.frame[:-2, :]))  # add the raw photo
                # alternative to %d-%m-%Y-%H-%M-%S-%f format
                self.time_stamp.append(time.strftime(
                    "%d-%m-%Y-%H-%M-%S")+'-'+str(t - int(t))[2:5])
                # check if not too much frames
                if self.count_frame < self.max_frame-1:
                    self.count_frame += 1
                else:
                    self.lapse_end = 1
                    self.count_frame = 0

            if self.lapse_end == 1:
                date = time.strftime("%d-%m-%Y-%H-%M-%S")
                self.block[0].save(self.folder_save+"\\timelapse-"+date+".tif",
                                   compression="tiff_deflate", save_all=True, append_images=self.block[1:])
                with open(self.folder_save+"\\timestamp-"+date+".txt", "w") as file:
                    for row in self.time_stamp:
                        file.write(row + '\n')
                self.lapse_end = 0

            # if there were too much frames during the record
            if self.count_frame == 0:
                self.block = []
                self.time_stamp = []

        self.window.after(self.delay, self.update)
        # fixed couple of temperatures ok (min < max)
        self.min_isok = self.min_want.get()
        self.max_isok = self.max_want.get()


class MyVideoCapture:
    def __init__(self, video_source):
        # open the video source
        self.vid = cv2.VideoCapture(video_source, cv2.CAP_DSHOW)
        self.vid.set(cv2.CAP_PROP_FOURCC,
                     cv2.VideoWriter.fourcc('Y', '1', '6', ' '))
        self.vid.set(cv2.CAP_PROP_CONVERT_RGB, 0)

        if not self.vid.isOpened():
            raise ValueError("Unable to open video source ", video_source)

        # selp.lep : first device opened
        self.lep, = (dev.Open() for dev in CCI.GetDevices())

        # set the resolution of the camera to 0.1°K
        self.lep.rad.SetTLinearResolution(0)  # 0: 0.1°K; 1: 0.01°K
        # set the FFC Normalization to automatic
        shutterModeObj = self.lep.sys.GetFfcShutterModeObj()
        newshutterModeObj = shutterModeObj
        newshutterModeObj.shutterMode = 1  # 0: manual; 1: auto; 2: external
        self.lep.sys.SetFfcShutterModeObj(newshutterModeObj)

    def get_frame(self):
        ret, frame = self.vid.read()
        if self.vid.isOpened() and ret:
            return(ret, frame, self.lep)
        else:
            return(ret, None)

    # Release the video source when the object is destroyed
    def __del__(self):
        if self.vid.isOpened():
            self.vid.release()
            cv2.destroyAllWindows()


# Initialization
# Select the video source
def close():
    global video_source
    video_source = answer.get()
    return(root.destroy())


root = tkinter.Tk()
root.title("Video Source")
# 0, 1, ... (see in README.txt)
ask = tkinter.Label(root, text="Which video source would you like to select ?")
ask.pack()
answer = IntVar()
answer.set(0)
tell_smthg = tkinter.Entry(root, textvariable=answer)
tell_smthg.pack()
confirmation = tkinter.Button(root, text='OK', command=close)
confirmation.pack()
root.mainloop()

# Create a window and pass it to the Application object
exe = App(tkinter.Tk(), "Lepton Flir 3.5", video_source)
