import os
import subprocess
import inquirer
from configparser import ConfigParser


def main():
    parser = get_parser(".fiml")
    counter = int(parser["main"]["counter"])
    all_files = os.listdir()
    video_files = sorted(filter(is_video, all_files))
    sub_files = sorted(filter(is_sub, all_files))
    assert not sub_files or len(video_files) <= len(sub_files)

    if counter >= len(video_files):
        return print("You watched all episodes already")

    answer = inquirer.prompt([
        inquirer.List("episode",
                      message="Which episode do you want to watch?",
                      choices=video_files,
                      default=video_files[counter])
    ])

    current = video_files.index(answer["episode"])
    watch_video(video_files[current],
                sub_files[current] if sub_files else "")

    if current == counter:
        answer = inquirer.prompt([
            inquirer.Confirm("complete",
                             message="Did you watch this episode completely?")
        ])
        if answer["complete"]:
            parser["main"]["counter"] = str(counter + 1)
            write_parser(parser, ".fiml")


def get_parser(filename: str):
    if not os.path.isfile(filename):
        return create_parser(filename)
    parser = ConfigParser()
    with open(filename, "r") as file:
        parser.read_file(file)
    return parser


def create_parser(filename: str):
    parser = ConfigParser()
    parser["main"] = {"counter": "0"}
    write_parser(parser, filename)
    return parser


def write_parser(parser: ConfigParser, filename: str):
    with open(filename, "w") as file:
        parser.write(file)


def is_video(filename: str):
    return any(filename.endswith(ext) for ext in (".mp4", ".mkv"))


def is_sub(filename: str):
    return filename.endswith("srt")


def get_command(video: str, sub: str):
    command = ["mpv", video, "--no-terminal"]
    if sub:
        command.append(f"--sub-file={sub}")
    return command


def watch_video(video: str, sub: str):
    print(f"Watching {video}...")
    command = get_command(video, sub)
    subprocess.run(command)


if __name__ == "__main__":
    main()
