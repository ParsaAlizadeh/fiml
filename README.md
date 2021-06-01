# fiml

VCS-like program for managing episodes and subtitles, and watching through mpv

# Install

Install python3, pip, and mpv (default player). Then run these commands inside project directory

```bash
$ make  # build and install fiml
```

# Usage

Open a terminal, go to your series directory and run `fiml`. It will show all episodes and wait for you to select one of them.
The default option is the first unwatched episode.

This script also detect subtitles and match them in lexicographical order with episodes. 
