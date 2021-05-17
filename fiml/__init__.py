#! /usr/bin/env python3

import json
import logging
import os
import subprocess
import mimetypes
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
        """ call watch process """
        logging.info(f"Watching {self.video}...")
        command = ["mpv", self.video, "--no-terminal"]
        if self.sub:
            command.append(f"--sub-file={self.sub}")
        subprocess.run(command)
        return self.index

    @staticmethod
    def is_video(filename: str) -> bool:
        """ check if video """
        guess_type, encode = mimetypes.guess_type(filename)
        return guess_type is not None and guess_type[:6] == "video/"

    @staticmethod
    def is_sub(filename: str) -> bool:
        """ check if sub """
        guess_type, encode = mimetypes.guess_type(filename)
        return guess_type == "application/x-subrip"

    @classmethod
    def find_all(cls, files: List[str]):
        """ find and match videos and subs """
        # sort lexographically
        videos = sorted(filter(cls.is_video, files))
        subs = sorted(filter(cls.is_sub, files))
        subs = resize(subs, len(videos))
        return [Video(i, vid, sub) for i, (vid, sub) in enumerate(zip(videos, subs))]


class Context:
    def __init__(self):
        self.data = {}
        self.counter = 0

    @property
    def counter(self):
        return self.data['counter']

    @counter.setter
    def counter(self, x: int):
        self.data['counter'] = x

    def read_file(self, filename: str):
        """ load from file """
        if not os.path.isfile(filename):
            return self
        with open(filename, 'r') as file:
            self.data = json.load(file)
        return self

    def write_file(self, filename: str):
        """ write to file """
        with open(filename, 'w') as file:
            json.dump(self.data, file)


def choose_option(message: str, options: List[str], default: int = 0) -> int:
    """ option prompt on terminal """
    answer = inquirer.prompt([
        inquirer.List(
            "list",
            message=message,
            choices=options,
            default=options[default]
        )
    ])
    return options.index(answer["list"])


def ask_confirm(message: str) -> bool:
    """ yes/no question on terminal """
    answer = inquirer.prompt([
        inquirer.Confirm(
            "confirm",
            message=message
        )
    ])
    return answer["confirm"]


def list_files(root):
    """ list all files inside root """
    result = []
    for root, _, files in os.walk(root):
        for f in files:
            result.append(os.path.join(root, f))
    return result


def main():
    ctx = Context().read_file('.fiml')

    # explore whole directory
    all_files = list_files('.')

    # find videos and match subs to them
    videos = Video.find_all(all_files)

    # if no new episode
    if ctx.counter >= len(videos):
        logging.info("You watched all episodes already :)")
        ctx.counter = len(videos)

    # prompt to choose a video
    options = [vid.video for vid in videos]
    options.append("exit")
    current = choose_option(
        message="Which episode?",
        options=options,
        default=ctx.counter
    )

    # exit option
    if current == len(videos):
        logging.info("Ok, no episodes for now")
        return

    # not default option
    if ctx.counter != current and ask_confirm("Reset counter to this episode?"):
        ctx.counter = current

    videos[current].watch()

    # default option and increament
    if current == ctx.counter and ask_confirm("Did you watch this episode completely?"):
        ctx.counter += 1

    ctx.write_file(".fiml")


if __name__ == "__main__":
    main()
