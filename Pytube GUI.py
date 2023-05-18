import customtkinter as ctk
from CTkMessagebox import CTkMessagebox
from tkinter import filedialog
from pytube import YouTube
from pytube import Playlist
from PIL import Image
import requests
import re
import os
import sys
from pathlib import Path

class ProgressFrame():
    def __init__(self, master, text):
        super().__init__()
        self.master = master

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
        self.progressText.configure(text = f"{self.text}\n{round(self.progressBar.get()*100, 1)}%")
        self.master.update()
    
    def set(self, value):
        self.progressBar.set(value)
        self.progressText.configure(text = f"{self.text}\n{round(value*100, 1)}%")
        self.master.update()
    
    def done(self):
        self.frame.destroy()
        self.master.update()

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        WIDTH = 1200
        HEIGHT = 600
        self.geometry('%dx%d+%d+%d' % (WIDTH, HEIGHT, int(self.winfo_screenwidth()/2 - WIDTH/2), int(self.winfo_screenheight()/2 - HEIGHT/2)))
        self.title('Video Downloader')
        # self.iconphoto(True, PhotoImage(file=self.Path + '\\Ico.png'))
        self.resizable (False, False)
        self.protocol("WM_DELETE_WINDOW", self.closing)

        self.playlist = False
        self.fileNum = 0
        self.url = ""

        self.videoURL = ""
        self.video = None
        self.mode = "Video"
        self.thumbnail = None
        self.selectedStream = ""
        self.streams = {}
        self.path = os.path.abspath(".")
        
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

        self.outputEntry = ctk.CTkEntry(self.outputFrame, width = 300, state = "disabled")
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

        # self.update_idletasks()
        # self.urlEntry.insert(0, "youtube.com/watch?v=KmweVl9cUtA&")
        # self.updateURL()

    def updateFile(self, newNum):
        num = self.fileNum + newNum
        if num < 0 or num == len(self.videos): return
        if newNum != 0:
            self.videos[self.fileNum] = [self.video, self.videoURL, self.video.title, self.thumbnail, self.mode, self.selectedStream, self.streams, self.outputName, self.path]

        progress = ProgressFrame(self, "Loading data, please wait!")
        self.fileNum = num

        self.video = self.videos[num][0]
        self.videoURL = self.videos[num][1]
        self.thumbnail = self.videos[num][3]
        self.mode = self.videos[num][4]
        self.selectedStream = self.videos[num][5]
        self.streams = self.videos[num][6]
        self.outputName = self.videos[num][7]
        self.path = self.videos[num][8]

        self.modeSelect.set(self.mode)
        self.streamSelect.set(self.selectedStream)
        self.fileName.configure(text = f"Video {self.fileNum+1}/{len(self.videos)}")

        self.videoThumbnail.configure(image = self.videos[num][3])
        progress.set(0.875)
        self.updateWidgets()
        
        progress.progress(12.5)
        progress.done()
        

    def updateWidgets(self):
        options = []
        for item in self.streams:
            if not self.mode.lower() in str(self.streams[item]): continue
            if self.mode == "Video":
                item = item.split('/')
            else:
                item = re.split('(\d+)',item)
            options.append(item)
        
        if self.mode == "Video":
            options = sorted(options, key=lambda x: (int(x[0][:-1]), int(x[1][:-3])), reverse=True)
            for n in range(len(options)):
                options[n] = "/".join(options[n])
        elif self.mode == "Audio":
            options = sorted(options, key=lambda x: int(x[1]), reverse=True)
            for n in range(len(options)):
                options[n] = "".join(options[n])
        
        time = "{:02}:{:02}".format(self.video.length%3600//60, self.video.length%60)
        if self.video.length >= 3600: time = f"{self.video.length//3600}:{time}"
        self.infoLbl.configure(text = f"URL: {self.videoURL}\nTitle: {self.video.title}\nLength: {time}s")
        fileSize = 0
        if self.selectedStream != "Quality": 
            fileSize = self.streams[self.selectedStream].filesize
            if fileSize > 1000000000:
                fileSize = str(f"{round(fileSize/1000000000, 2)}Gb")
            else:
                fileSize = str(f"{round(fileSize/1000000, 2)}Mb")

        self.outputEntry.configure(state = "normal")
        self.outputEntry.delete(0, ctk.END)
        self.outputEntry.insert(0, self.video.title)

        self.outputInfo.configure(text = f"Path: {self.path}\nFormat: mp4\nFilesize: {fileSize}")
        self.streamSelect.configure(values = options)

    def updateURL(self):
        if self.urlEntry.get() == self.url: return
        Input = self.urlEntry.get()
        progress = ProgressFrame(self, "Loading videos please wait!")
        if "playlist?list" in Input:
            playlist = self.tryLoad(Input, 1)
            if type(playlist) == str:
                CTkMessagebox(title="Error", message=playlist, icon="cancel")
                progress.done()
                return
            self.playlist = playlist
            self.videos = []
            inc = round(5 / len(self.playlist), 2)
            for url in self.playlist:
                video = self.tryLoad(url, 0)
                if type(video) == str:
                    CTkMessagebox(title="Error", message=video, icon="cancel")
                    progress.done()
                    return
                self.videos.append([video, Input])
                progress.progress(inc)
        else:
            self.playlist = False
            video = self.tryLoad(Input, 0)
            if type(video) == str:
                CTkMessagebox(title="Error", message=video, icon="cancel")
                progress.done()
                return
            self.videos = [[video, Input]]
        self.url = Input
        progress.set(0.05)
        inc = round(95 / len(self.videos), 2)
        for n in range(len(self.videos)):
            video = self.videos[n][0]
            dict = {}
            streams = video.streams
            for stream in streams:
                streamInfo = str(stream).split('\"')
                string = f"{streamInfo[5]}"
                if "video" in streamInfo[3]:
                    string += f"/{streamInfo[7]}"
                if not string in dict:
                    dict.update({string:stream})
            url = self.videos[n][1]
            title = video.title
            thumbnail = Image.open(requests.get(video.thumbnail_url, stream=True).raw)
            thumbnail = ctk.CTkImage(thumbnail, size = (640, 480))
            mode = self.mode
            selectedStream = "Quality"
            outputPath = f"{self.path}\\{title}"
            self.videos[n] = [video, url, title, thumbnail, mode, selectedStream, dict, title, outputPath]
            progress.progress(inc)
        progress.done()
        self.updateFile(0)

    def updateMode(self, choice):
        if self.mode == choice: return
        self.mode = choice
        self.streamSelect.set("Quality")
        self.selectedStream = "Quality"
        self.updateWidgets()

    def updateStream(self, choice):
        if self.selectedStream == choice: return
        self.selectedStream = choice
        self.updateWidgets()
    
    def selectOutput(self):
        if self.mode == "Audio":
            fileTypes = [("MPEG", "*.mp3", "*.mpeg"), "*.wav", "*.webm", "*.mp4", "*.3gp", "*.ogg"]
        elif self.mode == "Video":
            fileTypes = [("MPEG", "*.mp3 *.mpeg"), ("WAVE", ".wav"), ("WebM", ".webm"), ("MPEG-4", ".mp4"), ("3GPP", ".3gp"), ("Ogg", ".ogg")]
        self.path = filedialog.asksaveasfilename(initialdir=self.path, initialfile=self.outputName, title="Output Directory", filetypes=fileTypes, defaultextension=("MPEG"))
        print(Path(self.path).suffix)
        self.updateWidgets()

    def download(self):
        self.videos[self.fileNum] = [self.video, self.videoURL, self.video.title, self.thumbnail, self.mode, self.selectedStream, self.streams, self.outputName, self.path]

        downloads = []
        for item in self.videos:    
            video = item[0]
            selectedStream = item[5]
            for stream in self.streams:
                if selectedStream == "Quality":
                    CTkMessagebox(title="Warning Message!", message="Please select a quality", icon="warning")
                    return
                elif stream != selectedStream: continue

                stream = self.streams[stream]
                itag = str(stream).split('\"')
                itag = itag[1]
                downloads.append([video, itag])
                break
        
        inc = round(100 / (len(downloads)*3), 2)
        progress = ProgressFrame(self, "Downloading Videos.\nThis may take a while.")
        for list in downloads:
            video = list[0]
            progress.progress(inc)
            video = video.streams.get_by_itag(list[1])
            progress.progress(inc)
            video.download()
            progress.progress(inc)
        progress.done()
        print("Done")

        # stream.download()
                # else:
            # stream = video.streams.get_by_itag(stream.selectedStream)
            # stream.download(None, title)
            # command = "ffmpeg -i \"" + title + "\" -vn -ab 128k -ar 44100 -y \"" + Input + ".mp3\""
            # print(command)
            # os.system(command)
            # os.remove(title)
    
    def resetCache(self, params):
        version = f"{str(sys.version).split('.')[0]}{str(sys.version).split('.')[1]}"
        os.remove(f"{Path.home()}\\AppData\\Roaming\\Python\\Python{version}\\site-packages\\pytube\\__cache__\\tokens.json")
        self.tryLoad(params[0], params[1])

    def tryLoad(self, url, mode):
        try:
            if mode == 1:
                playlist = Playlist(url)
                url = playlist[0]
            video = YouTube(url, use_oauth=True, allow_oauth_cache=True)
            streams = video.streams
        except Exception as e:
            error = str(e)
            print(error)
            if "regex_search" in error:
                return "Invalid video URL"
            elif error == "\'list\'":
                return "Invalid playlist URL"
            elif error == "HTTP Error 410: Gone":
                return "Cannot access pytube servers, please try again!"
            elif error == "HTTP Error 400: Bad Request":
                self.resetCache([url, mode])
            elif "is streaming live and cannot be loaded" in error:
                return "Cannot download livestreams!"
            else:
                return error
        if mode == 1:
            return playlist
        return video

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