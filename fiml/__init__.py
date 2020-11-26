import logging
import os
import subprocess
from configparser import ConfigParser
from typing import *

import inquirer

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s\n"
)


def resize(seq: List, n: int, default=None) -> List:
    seq = seq[:n]
    seq = seq + [default] * (n - len(seq))
    return seq


class Video:
    def __init__(self, index: int, video_file: str, sub_file: str):
        self.index = index
        self.video = video_file
        self.sub = sub_file

    def watch(self) -> int:
        logging.info(f"Watching {self.video}...")
        command = ["mpv", self.video, "--no-terminal"]
        if self.sub:
            command.append(f"--sub-file={self.sub}")
        subprocess.run(command)
        return self.index

    @staticmethod
    def is_video(filename: str) -> bool:
        return any(filename.endswith(ext) for ext in (".mp4", ".mkv"))

    @staticmethod
    def is_sub(filename: str) -> bool:
        return filename.endswith("srt")

    @classmethod
    def find_all(cls, files: List[str]):
        videos = sorted(filter(cls.is_video, files))
        subs = sorted(filter(cls.is_sub, files))
        subs = resize(subs, len(videos))
        return [Video(i, vid, sub) for i, (vid, sub) in enumerate(zip(videos, subs))]


class Parser:
    def __init__(self, parser: ConfigParser):
        self.parser = parser
        self.counter = int(parser["main"]["counter"])

    def write(self, filename: str):
        self.parser["main"] = {"counter": str(self.counter)}
        with open(filename, "w") as file:
            self.parser.write(file)

    @classmethod
    def read(cls, filename: str):
        if not os.path.isfile(filename):
            parser = cls.create_default()
        else:
            parser = ConfigParser()
            with open(filename, "r") as file:
                parser.read_file(file)
        return cls(parser)

    @staticmethod
    def create_default() -> ConfigParser:
        logging.info("Initialize configs for first time")
        parser = ConfigParser()
        parser["main"] = {"counter": "0"}
        return parser


def main():
    parser = Parser.read(".fiml")
    all_files = os.listdir()
    videos = Video.find_all(all_files)
    if parser.counter >= len(videos):
        logging.info("You watched all episodes already :)")
        parser.counter = len(videos)

    options = [vid.video for vid in videos]
    options.append("exit")
    current = choose_option(message="Which episode?",
                            options=options,
                            default=parser.counter)
    if current == len(videos):
        logging.info("Ok, no episodes for now")
        return
    if parser.counter != current and ask_confirm("Reset counter to this episode?"):
        parser.counter = current

    videos[current].watch()

    if current == parser.counter and ask_confirm("Did you watch this episode completely?"):
        parser.counter += 1
    parser.write(".fiml")


def choose_option(message: str, options: List[str], default: int = 0) -> int:
    answer = inquirer.prompt([
        inquirer.List("list",
                      message=message,
                      choices=options,
                      default=options[default])
    ])
    return options.index(answer["list"])


def ask_confirm(message: str) -> bool:
    answer = inquirer.prompt([
        inquirer.Confirm("confirm",
                         message=message)
    ])
    return answer["confirm"]


if __name__ == "__main__":
    main()
