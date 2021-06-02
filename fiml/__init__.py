#! /usr/bin/env python3

import argparse
import json
import logging
import os
import subprocess
import mimetypes
import sys
from typing import *
from pathlib import Path

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
        logging.info("Watching %s...", self.video)
        command = ["mpv", self.video, "--no-terminal"]
        if self.sub:
            command.append(f"--sub-file={self.sub}")
        try:
            subprocess.run(command, check=True)
        except subprocess.CalledProcessError as err:
            logging.error("Watch process ends with %s code", err.returncode)
        return self.index

    @staticmethod
    def is_video(filename: str) -> bool:
        """ check if video """
        guess_type, _ = mimetypes.guess_type(filename)
        return guess_type is not None and guess_type[:6] == "video/"

    @staticmethod
    def is_sub(filename: str) -> bool:
        """ check if sub """
        guess_type, _ = mimetypes.guess_type(filename)
        return guess_type == "application/x-subrip"

    @classmethod
    def find_all(cls, files: List[str]) -> List['Video']:
        """ find and match videos and subs """
        # sort lexographically
        videos = sorted(filter(cls.is_video, files))
        subs = sorted(filter(cls.is_sub, files))
        subs = resize(subs, len(videos))
        return [Video(i, vid, sub) for i, (vid, sub) in enumerate(zip(videos, subs))]


class Context:
    def __init__(self, filename: Path):
        self.data = {}
        self.counter = 0
        self.filename = filename
        self.read_file()

    def __del__(self):
        self.write_file()

    @property
    def counter(self) -> int:
        return self.data['counter']

    @counter.setter
    def counter(self, x: int):
        self.data['counter'] = x

    def read_file(self):
        """ load from file """
        if not self.filename.is_file():
            return
        with self.filename.open() as file:
            self.data = json.load(file)

    def write_file(self) -> None:
        """ write to file """
        with self.filename.open(mode='w') as file:
            json.dump(self.data, file)


def choose_option(message: str, options: List[str], default: int = 0) -> int:
    """ option prompt on terminal """
    choices = [(opt, i) for i, opt in enumerate(options)]
    return inquirer.list_input(
        message=message,
        choices=choices,
        default=default
    )


def ask_confirm(message: str, default: bool = True) -> bool:
    """ yes/no question on terminal """
    return inquirer.confirm(
        message=message,
        default=default,
    )


def workflow(path: Path):
    # create context
    ctx = Context(filename=path/'.fiml')

    # explore whole directory
    all_files = list(map(str, path.rglob('*')))

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

def main():
    # parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-p', '--path',
        default='./',
        type=Path,
        help='path to series (default: %(default)s)'
    )
    args = parser.parse_args()
    path = args.path.resolve()

    # check for non-exist path
    if not path.is_dir():
        logging.error('No such path: %s', path)
        return

    # log keyboard interrupts
    try:
        workflow(path)
    except KeyboardInterrupt:
        logging.info("Skipped")


if __name__ == "__main__":
    main()
