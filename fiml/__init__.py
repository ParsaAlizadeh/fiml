#! /usr/bin/env python3
__version__ = '0.2.0'

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
    """ resize seq to exactly have n members """
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
        """ get current counter """
        return self.data['counter']

    @counter.setter
    def counter(self, value: int):
        """ update counter """
        self.data['counter'] = value

    def read_file(self):
        """ load from file """
        if not self.filename.is_file():
            return
        with self.filename.open() as file:
            self.data = json.load(file)

    def write_file(self) -> None:
        """ write to file """
        with self.filename.open(mode='w') as file:
            json.dump(self.data, file, indent=4)


class Workflow:
    def __init__(self, root: Path, noconfirm: bool = False):
        self.root = root
        self.ctx = Context(filename=self.root/'.fiml')
        self.noconfirm = noconfirm

    def run(self) -> bool:
        """ run the workflow """
        # explore whole directory
        all_files = list(map(str, self.root.rglob('*')))

        # find videos and match subs to them
        videos = Video.find_all(all_files)

        # if no new episode
        if self.ctx.counter >= len(videos):
            logging.info("You watched all episodes already :)")
            self.ctx.counter = len(videos)

        # prompt to choose a video
        options = [vid.video for vid in videos]
        options.append("exit")
        current = self.choose_option(
            message="Which episode?",
            options=options,
            default=self.ctx.counter
        )

        # exit option
        if current == len(videos):
            logging.info("Ok, no episodes for now")
            return False

        # not default option
        reset_message = "Reset counter to this episode?"
        if self.ctx.counter != current and self.ask_confirm(reset_message):
            self.ctx.counter = current

        videos[current].watch()

        # default option and increament
        complete_message = "Did you watch this episode completely?"
        if current == self.ctx.counter and self.ask_confirm(complete_message):
            self.ctx.counter += 1
            return True

        # no further watch
        return False

    def choose_option(self, message: str, options: List[str], default: int = 0) -> int:
        """ option prompt on terminal """
        if self.noconfirm:
            return default
        choices = [(opt, i) for i, opt in enumerate(options)]
        return inquirer.list_input(
            message=message,
            choices=choices,
            default=default
        )

    def ask_confirm(self, message: str, default: bool = True) -> bool:
        """ yes/no question on terminal """
        if self.noconfirm:
            return default
        return inquirer.confirm(
            message=message,
            default=default,
        )


def main():
    """ command line function """
    # parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-v', '--version',
        action='version',
        version=f'%(prog)s {__version__}'
    )
    parser.add_argument(
        '-n', '--noconfirm',
        action='store_true',
        help='no confirmation'
    )
    parser.add_argument(
        '-b', '--batch',
        action='store_true',
        help='play in batch'
    )
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

    workflow = Workflow(
        root=path,
        noconfirm=args.noconfirm
    )
    try:
        further_watch = True
        while further_watch:
            further_watch = workflow.run() and args.batch
    except KeyboardInterrupt:
        # log keyboard interrupts
        logging.info("Skipped")


if __name__ == "__main__":
    main()
