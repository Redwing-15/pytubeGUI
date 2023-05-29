import customtkinter as ctk
from CTkMessagebox import CTkMessagebox
from tkinter import filedialog
from pytube import YouTube
from pytube import Playlist
from PIL import Image
import threading
import requests
import re
import os
import sys
from pathlib import Path
# Todo: add threading for the download
# Rework outputEntry validation system
# Rework file downloading to only download as mp4 and mp3
class progressFrame():
    def __init__(self, master, text, isDownloading):
        super().__init__()
        self.master = master
        self.isDownloading = isDownloading

        self.frame = ctk.CTkFrame(master)
        self.frame.place(relx=0.5, rely=0.5, anchor="center")

        self.text = text
        self.progressText = ctk.CTkLabel(self.frame, text = f"{self.text}\n0%", justify = "center")
        self.progressText.pack()

        self.progressBar = ctk.CTkProgressBar(self.frame, width = 400)
        self.progressBar.set(0)
        self.progressBar.pack()

        self.master.update()

    def progress(self, increment):
        self.progressBar.set(round(self.progressBar.get() + (increment/100), 4))
        if self.isDownloading:
            text = f"{self.text}\n{round(self.progressBar.get()*100, 1)}%"
            # print(text)
        else:
            text = f"{self.text}\n{round(self.progressBar.get()*100, 1)}%"

        self.progressText.configure(text = text)
        self.master.update()
    
    def set(self, value):
        value /= 100
        self.progressBar.set(value)
        if self.isDownloading:
            text = f"{self.text}\n{round(self.progressBar.get()*100, 1)}%"
            # print(text)
        else:
            text = f"{self.text}\n{round(self.progressBar.get()*100, 1)}%"
        self.progressText.configure(text = text)
        self.master.update()
    
    def done(self):
        self.frame.destroy()
        self.master.update()

class Video():
    def __init__(self, url):
        super().__init__()
        self.isVideo = 1
        if "playlist?list" in url:
            self.isVideo = 0
        
        self.url = url
        self.getVideo()
    
    def getVideo(self):
        self.tryLoad()

        if not self.isVideo: return

        streams = list(self.streams.filter(progressive=True))
        streams += list(self.streams.filter(only_video=True))
        streams += list(self.streams.filter(only_audio=True))

        dict = {}
        for stream in streams:
            streamInfo = str(stream).split('\"')
            String = f"{streamInfo[5]}"
            if "video" in streamInfo[3]:
                String += f"/{streamInfo[7]}"
            if not String in dict:
                dict.update({String:stream})
        self.streams = dict

        self.title = self.video.title
        thumbnail = Image.open(requests.get(self.video.thumbnail_url, stream=True).raw)
        self.thumbnail = ctk.CTkImage(thumbnail, size = (640, 480))
        self.mode = "Video"
        self.selectedStream = "Quality"
        self.outputTitle = self.title
        self.outputExtension = ".mp4"
        self.fileSize = 0
        self.outputPath = os.path.abspath(".")

    def tryLoad(self):
        try:
            if not self.isVideo:
                self.video = Playlist(self.url)
            else:
                self.video = YouTube(self.url, use_oauth=True, allow_oauth_cache=True)
                self.streams = self.video.streams
        except Exception as e:
            error = str(e)
            if "regex_search" in error:#
                error =  "Invalid video URL"
            elif error == "\'list\'":
                error = "Invalid playlist URL"
            elif error == "HTTP Error 410: Gone":
                error = "Cannot access pytube servers, please try again!"
            elif error == "HTTP Error 400: Bad Request":
                self.resetCache()
            elif "is streaming live and cannot be loaded" in error:
                error = "Cannot download livestreams!"

            CTkMessagebox(title="Error", message=error, icon="cancel")
        return
    
    def resetCache(self):
        version = f"{str(sys.version).split('.')[0]}{str(sys.version).split('.')[1]}"
        os.remove(f"{Path.home()}\\AppData\\Roaming\\Python\\Python{version}\\site-packages\\pytube\\__cache__\\tokens.json")
        self.tryLoad()

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.path = os.path.abspath(".")
        WIDTH = 1200
        HEIGHT = 600
        self.geometry('%dx%d+%d+%d' % (WIDTH, HEIGHT, int(self.winfo_screenwidth()/2 - WIDTH/2), int(self.winfo_screenheight()/2 - HEIGHT/2)))
        self.title('Video Downloader')
        # self.iconphoto(True, PhotoImage(file=self.Path + '\\Ico.png'))
        self.resizable (False, False)
        self.protocol("WM_DELETE_WINDOW", self.closing)

        self.fileNum = 0
        self.url = ""
        self.video = None
        self.multiTasking = False
        
        self.createWidgets()

    def createWidgets(self):
        self.urlEntry = ctk.CTkEntry(self, width = 500, justify = "center")
        self.urlEntry.bind("<Return>", (lambda event: self.updateURL()))
        self.urlEntry.pack()

        self.fileFrame = ctk.CTkFrame(self)
        self.fileFrame.pack(side = "left")

        self.videoFrame = ctk.CTkFrame(self.fileFrame)
        self.videoFrame.pack(side = "top")

        self.fileLeft = ctk.CTkButton(self.videoFrame, text = '<', width = 20, command = lambda: self.updateFile(-1))
        self.fileLeft.pack(side = "left")

        self.fileName = ctk.CTkLabel(self.videoFrame, text = "Video 0/0")
        self.fileName.pack(side = "left")

        self.fileRight = ctk.CTkButton(self.videoFrame, text = '>', width = 20, command = lambda: self.updateFile(1))
        self.fileRight.pack(side = "right")

        self.infoLbl = ctk.CTkLabel(self.fileFrame, text = f"URL:\nTitle:\nLength: 00:00:00s", justify = "left")
        self.infoLbl.pack()

        self.optionsFrame = ctk.CTkFrame(self.fileFrame)
        self.optionsFrame.pack()

        self.streamSelect = ctk.CTkOptionMenu(self.optionsFrame, values = [""], command = self.updateStream)
        self.streamSelect.set("Quality")
        self.streamSelect.pack(side = "left")

        self.modeSelect = ctk.CTkOptionMenu(self.optionsFrame, values = ["Video", "Audio"], command = self.updateMode)
        self.modeSelect.pack(side = "right")

        self.outputFrame = ctk.CTkFrame(self.fileFrame)
        self.outputFrame.pack()

        self.outputVariable = ctk.StringVar()
        self.outputVariable.trace("w", lambda var_name, var_index, operation: self.outputChanged())

        self.outputEntry = ctk.CTkEntry(self.outputFrame, width = 300, textvariable=self.outputVariable, state = "disabled")
        self.outputEntry.pack(side="left")

        self.outputPath = ctk.CTkButton(self.outputFrame, text = "V", width = 10, command = self.selectOutput)
        self.outputPath.pack(side = "right")

        self.outputInfo = ctk.CTkLabel(self.fileFrame, text = "Path:\nFormat:\nFilesize:")
        self.outputInfo.pack()

        self.downloadButton = ctk.CTkButton(self.fileFrame, text = "Download", command = self.download)
        self.downloadButton.pack()

        self.thumbnailFrame = ctk.CTkFrame(self)
        self.thumbnailFrame.pack(side = "right", anchor = "center")

        self.videoThumbnail = ctk.CTkLabel(self.thumbnailFrame, text = "")
        self.videoThumbnail.pack()

        self.update_idletasks() # Playlist: youtube.com/playlist?list=PLFt_AvWsXl0dPhqVsKt1Ni_46ARyiCGSq
        self.urlEntry.insert(0, "youtube.com/watch?v=QZwneRb-zqA") # Video: youtube.com/watch?v=QZwneRb-zqA
        self.updateURL()

    def updateFile(self, newNum):
        num = self.fileNum + newNum
        if num < 0 or num == len(self.videos): return

        self.fileNum = num
        self.video = self.videos[self.fileNum]

        self.modeSelect.set(self.video.mode)
        self.streamSelect.set(self.video.selectedStream)
        self.fileName.configure(text = f"Video {self.fileNum+1}/{len(self.videos)}")

        self.videoThumbnail.configure(image = self.video.thumbnail)

        self.updateWidgets()

    def updateWidgets(self):
        options = []
        for item in self.video.streams:
            if not self.video.mode.lower() in str(self.video.streams[item]): continue
            if self.video.mode == "Video":
                item = item.split('/')
            else:
                item = re.split('(\d+)',item)
            options.append(item)
        
        if self.video.mode == "Video":
            options = sorted(options, key=lambda x: (int(x[0][:-1]), int(x[1][:-3])), reverse=True)
            for n in range(len(options)):
                options[n] = "/".join(options[n])
        elif self.video.mode == "Audio":
            options = sorted(options, key=lambda x: int(x[1]), reverse=True)
            for n in range(len(options)):
                options[n] = "".join(options[n])
        
        time = "{:02}:{:02}".format(self.video.video.length%3600//60, self.video.video.length%60)
        if self.video.video.length >= 3600: time = f"{self.video.video.length//3600}:{time}"
        self.infoLbl.configure(text = f"URL: {self.video.url}\nTitle: {self.video.title}\nLength: {time}s")
        fileSize = 0
        if self.video.selectedStream != "Quality": 
            fileSize = self.video.streams[self.video.selectedStream].filesize
            if fileSize > 1000000000:
                fileSize = str(f"{round(fileSize/1000000000, 2)}Gb")
            else:
                fileSize = str(f"{round(fileSize/1000000, 2)}Mb")
        self.video.fileSize = fileSize

        self.outputVariable.set(self.video.outputTitle)

        self.outputInfo.configure(text = f"Path: {self.video.outputPath}\\{self.video.outputTitle}\nFormat: {self.video.outputExtension}\nFilesize: {self.video.fileSize}")
        self.streamSelect.configure(values = options)

    def getVideo(self, temp, url):
        self.video = Video(url)
        self.progress = 5
        if not self.video.isVideo:
            inc = round(95 / len(self.video.video), 2)
            for video in self.video.video:
                self.videos.append(Video(video))
                self.progress += inc
            self.video = self.videos[0]
        else:
            self.progress = 100
            self.videos.append(self.video)
        self.multiTasking = False

    def updateURL(self):
        if self.urlEntry.get() == self.url: return
        self.url = self.urlEntry.get()
        self.videos = []

        thread = threading.Thread(target = self.getVideo, args=(self, self.url),daemon=True)
        thread.start()

        self.multiTasking = True
        self.progress = 0

        self.urlEntry.configure(state="disabled")
        self.downloadButton.configure(state="disabled")
        for item in self.fileFrame.winfo_children():
            if str(type(item)) == "<class \'customtkinter.windows.widge6ts.ctk_frame.CTkFrame\'>":
                for child in item.winfo_children():
                    child.configure(state="disabled")

        progress = progressFrame(self, "Loading videos, please wait!", False)
        while self.multiTasking:
            progress.set(self.progress)
        
        for item in self.fileFrame.winfo_children():
            if str(type(item)) == "<class \'customtkinter.windows.widgets.ctk_frame.CTkFrame\'>":
                for child in item.winfo_children():
                    child.configure(state="normal")
        self.downloadButton.configure(state="normal")
        self.urlEntry.configure(state="normal")
        self.outputEntry.configure(state = "normal")

        progress.set(self.progress)
        progress.done()

        self.updateFile(0)

    def updateMode(self, choice):
        if self.video.mode == choice: return
        self.video.mode = choice
        self.streamSelect.set("Quality")
        self.video.selectedStream = "Quality"
        if choice == "Video":
            self.video.outputExtension = ".mp4"
        else:
            self.video.outputExtension = ".mp3"

        self.updateWidgets()

    def updateStream(self, choice):
        if self.video.selectedStream == choice: return
        self.video.selectedStream = choice

        self.updateWidgets()
    
    def selectOutput(self):
        if self.video.mode == "Video":
            fileTypes = [("MPEG-4", ".mp4"), ("MPEG", ".mp3"), ("3GPP", ".3gp"), ("Ogg", ".ogg"), ("WebM", ".webm")]
        elif self.video.mode == "Audio": 
            fileTypes = [("MPEG", ".mp3"), ("MPEG-4", ".mp4"), ("Ogg", ".ogg"), ("WAVE", ".wav"), ("WebM", ".webm")]
        path = filedialog.asksaveasfilename(initialdir=self.video.outputPath, initialfile=self.video.outputTitle, title="Output Directory", filetypes=fileTypes, defaultextension=self.video.outputExtension)
        self.video.outputExtension = str(Path(path).suffix)
        self.video.outputPath = path[:-(len(self.video.outputExtension)+len(self.video.outputTitle))]
        # print(self.video.outputPath)

        self.updateWidgets()

    def download(self):
        downloads = []
        i = 0
        for item in self.videos:    
            if re.search(r'[<>:"\/|?*]', item.outputTitle):
                CTkMessagebox(title="Warning Message!", message="Illegal character in title! Cannot contain: \'<>:/\\?*\'", icon="warning")
                self.video = item
                self.updateFile(i - self.fileNum)
                return
            for stream in item.streams:
                if item.selectedStream == "Quality":
                    CTkMessagebox(title="Warning Message!", message="Please select a quality", icon="warning")
                    self.video = item
                    self.updateFile(i - self.fileNum)
                    return
                elif stream != item.selectedStream: continue
                stream = str(item.streams[stream]).split('\"')
                downloads.append([item, stream])
                break
            i += 1

        inc = round(100 / (len(downloads)*3), 2)
        progress = progressFrame(self, "Downloading Videos.\nThis may take a while.", True)
        for download in downloads:
            Video = download[0]
            progress.progress(inc)
            stream = Video.video.streams.get_by_itag(download[1][1])
            progress.progress(inc)
            title = f"{Video.outputTitle}_video.{download[1][3][6:]}"
            stream.download(f"{Video.outputPath}\\temp", title)
            progress.progress(inc)
        progress.done() 
        
        for download in downloads:
            if download[1][11] != "False": # Is an audio stream or progressive  
                download[1] =  f"{self.path}\\temp\\{download[0].outputTitle}_video.{download[1][3][6:]}"
                continue
            audioStream = download[0].video.streams.filter(only_audio=True).last()
            stream = str(audioStream).split('\"')

            audioTitle = f"temp\\{download[0].outputTitle}_audio.{stream[3][6:]}"
            audioStream.download(download[0].outputPath, audioTitle)

            videoTitle = f"{self.path}\\temp\\{download[0].outputTitle}_video.{download[1][3][6:]}"   
            outputTitle = f"{self.path}\\temp\\{download[0].outputTitle}.mkv"
            command = f"ffmpeg -i \"{videoTitle}\" -i \"{audioTitle}\" -c copy \"{outputTitle}\""

            os.system(command)
            download[1] = outputTitle

        for download in downloads:
            
            default = download[1].split('.')
            default = f".{default[len(default)-1]}"

            if default == download[0].outputExtension:
                path = f"{download[0].outputPath}\\{download[0].outputTitle}{download[0].outputExtension}"
                print(download[1], path)
                os.rename(download[1], path)
                continue
            codecs = {".mp3":"PCM", ".mp4":"mpeg4", ".ogg":"opus", ".wav":"", ".webm":"opus"}
            outputTitle = f"{download[0].outputPath}\\{download[0].outputTitle}{download[0].outputExtension}"

            if download[0].isVideo:
                print(download[0].outputExtension.replace('.', ''))
                command = f"ffmpeg -i \"{download[1]}\" -c:v libx264 -qp 0 \"{outputTitle}\""
                print(command)
                os.system(command)
            else:
                command = f"ffmpeg -i \"{download[1]}\" -vn -ab 128k -ar 44100 -y \"{outputTitle}\""
                print(command)
                os.system(command)
        
        for subdir, dirs, files in os.walk("temp"):
            for file in files:
                os.remove(os.path.abspath(f"temp\\{file}"))
        os.rmdir("temp")
                # else:
            # stream = video.streams.get_by_itag(stream.selectedStream)
            # stream.download(None, title)
            # command = "ffmpeg -i \"" + title + "\" -vn -ab 128k -ar 44100 -y \"" + Input + ".mp3\""
            # print(command)
            # os.system(command)
            # os.remove(title)

    def outputChanged(self): # Allow user to type in illegal characters, but if detected it will popup saying "Changes wont be saved" and will use the last valid name
        if self.video == None or self.outputVariable.get() == self.video.outputTitle:
            return
        self.video.outputTitle = self.outputVariable.get()
        self.updateWidgets()

    def closing(self):
        self.destroy()

if __name__ == "__main__":
    app = App()
    app.mainloop()

# from pytube import YouTube
# from pytube import Playlist
# from time import sleep
# import os

# # Input = str(input("Enter full url: "))
# # Input = "https://youtube.com/playlist?list=PLFt_AvWsXl0dPhqVsKt1Ni_46ARyiCGSq"
# Input = "https://www.youtube.com/watch?v=wJMDh9QGRgs"
# playlist = False
# if "playlist?list" in Input:
#     playlist = True
# videos = []
# for attempt in range(3):
#     try:
#         if playlist:
#             Video = Playlist(Input)
#             print(f"Playlist URL: {Video.playlist_url}\nPlaylist Title: {Video.title}")
#             for vid in Video:
#                 video = YouTube(vid, use_oauth=True, allow_oauth_cache=True)
#                 videos.append(video)
#         else:
#             Video = YouTube(Input, use_oauth=True, allow_oauth_cache=True)
#             videos.append(Video)
#         break
#     except Exception as e:
#         sleep(1)
#         print(e)
#         if attempt < 2:
#             continue
#         error = str(e)
#         if "regex_search" in error:
#             print("Invalid video URL")
#         elif error == "\'list\'":
#             print("Invalid playlist URL")
#         elif error == "urllib.error.HTTPError: HTTP Error 410: Gone":
#             print("Requst error (cant access servers rn)")
#         else:
#             print("Cannot access pytube servers right now, please try again later!")

# for video in videos:
#     url = str(video).split('=')
#     url = f"https://youtu.be/{url[1][:-1]}"
#     print(f"\nURL: {url}\nTitle: {video.title}\nThumbail: {video.thumbnail_url}")

#     try:
#         for stream in video.streams.filter(only_audio=True):
#             itag = str(stream).split(" ")
#             format = itag[2][17:-1]
#             itag = itag[1][6:-1]
#     except Exception as e:
#         if "is streaming live and cannot be loaded" in str(e):
#             print("Cannot download livestreams!")
#         # print(format, itag)
#     Input = str(input("Enter output filename: "))
#     # Input = "Overlord Op 4"
#     title = f"{Input}.{format}"
#     # print(video.streams)
#     # stream = video.streams.get_by_itag(itag)
#     stream = video.streams.get_by_itag(308)
#     # stream.download(None, title)
#     stream.download()
#     command = "ffmpeg -i \"" + title + "\" -vn -ab 128k -ar 44100 -y \"" + Input + ".mp3\""
#     print(command)
#     os.system(command)
#     os.remove(title)