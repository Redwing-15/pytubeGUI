import customtkinter as ctk
from CTkMessagebox import CTkMessagebox
from pytube import YouTube
from pytube import Playlist
from PIL import Image
import requests

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
        self.master.update_idletasks()

    def progress(self, increment):
        self.progressBar.set(round(self.progressBar.get() + (increment/100), 4))
        self.progressText.configure(text = f"{self.text}\n{round(self.progressBar.get()*100, 1)}%")
        self.master.update_idletasks()
    
    def set(self, value):
        self.progressBar.set(value)
        self.progressText.configure(text = f"{self.text}\n{round(value*100, 1)}%")
        self.master.update_idletasks()
    
    def done(self):
        self.frame.destroy()
        self.master.update_idletasks()

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
        self.selectedStream = None
        
        self.createWidgets()

    def createWidgets(self):
        self.urlEntry = ctk.CTkEntry(self, width = 500, justify = "center")
        self.urlEntry.bind("<Return>", (lambda event: self.updateURL()))
        self.urlEntry.pack()

        self.fileFrame = ctk.CTkFrame(self)
        self.fileFrame.pack(side = "left")

        self.videoFrame = ctk.CTkFrame(self.fileFrame)
        self.videoFrame.pack(side = "top")

        self.fileLeft = ctk.CTkButton(self.videoFrame, text = '<', width = 20, command = lambda: self.updateFile(self.fileNum-1))
        self.fileLeft.pack(side = "left")

        self.fileName = ctk.CTkLabel(self.videoFrame, text = "Video 0/0")
        self.fileName.pack(side = "left")

        self.fileRight = ctk.CTkButton(self.videoFrame, text = '>', width = 20, command = lambda: self.updateFile(self.fileNum+1))
        self.fileRight.pack(side = "right")

        self.infoLbl = ctk.CTkLabel(self.fileFrame, text = f"URL:\nTitle:\nLength: 00:00:00s", justify = "left")
        self.infoLbl.pack(anchor = "center")

        self.streamSelect = ctk.CTkOptionMenu(self.fileFrame, values = [""], command = self.updateStream)
        self.streamSelect.set("Quality")
        self.streamSelect.pack(side = "left")

        self.modeSelect = ctk.CTkOptionMenu(self.fileFrame, values = ["Video", "Audio"], command = self.updateMode)
        self.modeSelect.pack(side = "right")

        self.outputEntry = ctk.CTkEntry(self.fileFrame)
        self.outputEntry.pack(side="bottom")

        self.downloadButton = ctk.CTkButton(self.fileFrame, text = "Download", command = self.download)
        self.downloadButton.pack(anchor = "s", side = "bottom")

        self.thumbnailFrame = ctk.CTkFrame(self)
        self.thumbnailFrame.pack(side = "right")

        self.videoThumbnail = ctk.CTkLabel(self.thumbnailFrame, text = "")
        self.videoThumbnail.pack()

    def updateFile(self, num):
        if num < 0 or num == len(self.videos): return
        
        progress = ProgressFrame(self, "Loading data, please wait!")
        self.fileNum = num
        
        self.video = self.videos[num][0]
        self.videoURL = self.videos[num][1]
        self.mode = self.videos[num][4]
        self.selectedStream = self.videos[num][5]

        self.modeSelect.set(self.mode)
        self.streamSelect.set(self.selectedStream)
        self.fileName.configure(text = f"Video {self.fileNum+1}/{len(self.videos)}")

        self.videoThumbnail.configure(image = self.videos[num][3])
        progress.set(0.875)
        self.updateWidgets()
        progress.progress(12.5)
        progress.done()
        

    def updateWidgets(self):
        if self.mode == "Video":
            streams = self.video.streams.filter(only_video=True)
        else:
            streams = self.video.streams.filter(only_audio=True)
        options = []
        for stream in streams:
            streamInfo = str(stream).split('\"')
            print(streamInfo)
            string = f"{streamInfo[5]}"
            if self.mode == "Video":
                string += f"/{streamInfo[7]}"
            if not string in options:
                options.append(string)
        self.infoLbl.configure(text = f"URL: {self.videoURL}\nTitle: {self.video.title}\nLength: 00:00:00s")
        self.streamSelect.configure(values = options)

    def updateURL(self):
        if self.urlEntry.get() == self.url: return

        progress = ProgressFrame(self, "Loading videos please wait!")
        self.url = self.urlEntry.get()
        if "playlist?list" in self.url:
            playlist = self.tryLoad(self.url, 1)
            if type(playlist) == str:
                CTkMessagebox(title="Error", message=playlist, icon="cancel")
                progress.done()
                return
            self.playlist = playlist
            self.videos = []
            inc = round(5 / len(self.playlist), 2)
            for url in self.playlist:
                progress.progress(inc)
                video = self.tryLoad(url, 0)
                if type(video) == str:
                    CTkMessagebox(title="Error", message=video, icon="cancel")
                    progress.done()
                    return
                self.videos.append([video, url])
                progress
        else:
            self.playlist = False
            video = self.tryLoad(self.url, 0)
            if type(video) == str:
                CTkMessagebox(title="Error", message=video, icon="cancel")
                progress.done()
                return
            self.videos = [[video, self.url]]
        progress.set(0.05)
        inc = round(95 / len(self.videos), 2)
        for n in range(len(self.videos)):
            video = self.videos[n][0]
            streams = video.streams
            url = self.videos[n][1]
            title = video.title
            thumbnail = Image.open(requests.get(video.thumbnail_url, stream=True).raw)
            thumbnail = ctk.CTkImage(thumbnail, size = (640, 480))
            mode = "Video"
            selectedStream = "Quality"
            self.videos[n] = [video, url, title, thumbnail, mode, selectedStream]
            progress.progress(inc)
        progress.done()
        self.updateFile(0)

    def updateMode(self, choice):
        if self.mode == choice: return
        self.mode = choice
        self.selectedStream = "Quality"
        self.streamSelect.set(self.selectedStream)
        self.updateWidgets()

    def updateStream(self, choice):
        if self.selectedStream == choice: return
        self.selectedStream = choice
        self.infoLbl.configure(text = f"Url: {self.videoURL}\nVideo: {self.video}\nTitle: {self.video.title}\nMode: {self.mode}\nselectedStream: {self.selectedStream}")

    def download(self):
        for video in self.videos:    
            url = video[1]
            print(f"\nURL: {url}\nTitle: {video[0].title}\nThumbail: {video[0].thumbnail_url}")
            Input = str(input("Enter output filename: "))
            title = f"{Input}.{format}"
            for stream in video[0].streams:
                if self.selectedStream in str(stream):
                    print(stream)
            # stream = video.streams.get_by_itag(stream.selectedStream)
            # stream.download(None, title)
            # command = "ffmpeg -i \"" + title + "\" -vn -ab 128k -ar 44100 -y \"" + Input + ".mp3\""
            # print(command)
            # os.system(command)
            # os.remove(title)

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
            elif "is streaming live and cannot be loaded" in error:
                return "Cannot download livestreams!"
            else:
                return ("Unknown Error:", error)
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

# Input = str(input("Enter full url: "))
# # Input = "https://youtube.com/playlist?list=PLFt_AvWsXl0dPhqVsKt1Ni_46ARyiCGSq"
# # Input = "https://www.youtube.com/watch?v=wJMDh9QGRgs"
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
#     stream = video.streams.get_by_itag(itag)
#     stream.download(None, title)
#     command = "ffmpeg -i \"" + title + "\" -vn -ab 128k -ar 44100 -y \"" + Input + ".mp3\""
#     print(command)
#     os.system(command)
#     os.remove(title)