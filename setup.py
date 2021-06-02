from setuptools import find_packages, setup
from fiml import __version__

with open("requirements.txt", "r") as file:
    install_requires = file.readlines()

setup(
    name="fiml",
    description="VCS-like program for managing episodes and subtitles, and watching through mpv",
    version=__version__,
    author="Parsa Alizadeh",
    license="MIT",
    packages=find_packages(),
    entry_points={
        "console_scripts": ["fiml=fiml:main"]
    },
    install_requires=install_requires,
)
