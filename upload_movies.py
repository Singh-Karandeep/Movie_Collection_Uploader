import os
import subprocess
from collections import OrderedDict
from json import dump

import psutil
from pymediainfo import MediaInfo

from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

class Drive:
    DRIVE_TO_SEARCH = 'CHANVEER'
    MOVIES_FOLDER = 'Movies Collection'
    TV_SERIES_FOLDER = 'TV Series Collection'
    HARD_DRIVE_JSON = 'Movies_TV_Series_Collection.json'

    def __init__(self):
        self.drive_dict = {}
        self.movies_tv_series_dict = OrderedDict()

    @staticmethod
    def get_drive_name(driveletter):
        try:
            return subprocess.check_output(["cmd", "/c vol " + driveletter]).split("\r\n")[0].split(" ").pop()
        except Exception as e:
            pass

    def get_drives(self):
        drps = psutil.disk_partitions()
        drives = [dp.device for dp in drps if dp.fstype == 'NTFS']
        for drive in drives:
            self.drive_dict[drive] = Drive.get_drive_name(drive[:-1])

    @property
    def get_drive_dict(self):
        return self.drive_dict

    def convert_tree_to_dict(self, path):
        tree = OrderedDict()
        for root, dirs, files in os.walk(path):
            for d in dirs:
                tree[d] = self.convert_tree_to_dict(os.path.join(root, d))
            x = OrderedDict()
            for f in files:
                if not f.endswith('.db'):
                    abs_path = os.path.join(root, f)
                    print "Processing File : {}".format(f)
                    x[f] = Drive.get_resolution(abs_path)
            tree.update(x)
            return tree

    def dump_to_json(self):
        with open(Drive.HARD_DRIVE_JSON, 'w')as f:
            dump(self.movies_tv_series_dict, f, indent=4)

    @staticmethod
    def get_resolution(file_path):
        media_info = MediaInfo.parse(file_path)
        for track in media_info.tracks:
            if track.track_type == 'Video':
                return "Resolution - {}x{}".format(track.width, track.height)
        return 'NA'

    def fetch_files(self):
        for drive_letter, drive_name in self.drive_dict.items():
            if drive_name == Drive.DRIVE_TO_SEARCH:
                folders = os.listdir(drive_letter)
                if Drive.MOVIES_FOLDER in folders:
                    self.movies_tv_series_dict[Drive.MOVIES_FOLDER] = self.convert_tree_to_dict(
                        os.path.join(drive_letter, Drive.MOVIES_FOLDER))
                if Drive.TV_SERIES_FOLDER in folders:
                    self.movies_tv_series_dict[Drive.TV_SERIES_FOLDER] = self.convert_tree_to_dict(
                        os.path.join(drive_letter, Drive.TV_SERIES_FOLDER))

        self.dump_to_json()

    def start(self):
        self.get_drives()
        self.fetch_files()

    @staticmethod
    def upload_to_drive():
        files = os.listdir(os.getcwd())
        if Drive.HARD_DRIVE_JSON in files:
            g_login = GoogleAuth()
            g_login.LocalWebserverAuth()
            drive = GoogleDrive(g_login)
            f = open(Drive.HARD_DRIVE_JSON, "r")
            fn = os.path.basename(f.name)
            file_drive = drive.CreateFile({'title': fn})
            file_drive.SetContentString(f.read())
            file_drive.Upload()
            f.close()
            print "The file: {} has been uploaded".format(fn)
        else:
            print "{} not present in current directory...!!!".format(Drive.HARD_DRIVE_JSON)

if __name__ == '__main__':
    d = Drive()
    try:
        d.start()
        d.upload_to_drive()
    except KeyboardInterrupt as e:
        print "\n\nManually Stopped...!!!"
