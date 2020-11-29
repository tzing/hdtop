import os

from setuptools import setup


def get_version():
    # workaround to resolve import issue
    basedir = os.path.dirname(os.path.realpath(__file__))
    version_line = None
    with open(os.path.join(basedir, "hdtop/__init__.py")) as fp:
        for line in fp:
            if line.startswith("__version__"):
                version_line = line
                break

    l_quote = version_line.find('"')
    r_quote = version_line.rfind('"')
    return version_line[l_quote + 1 : r_quote]


setup(
    name="hdtop",
    version=get_version(),
    description="Top-liked monitoring console for hadoop.",
    author="Tzing",
    author_email="tzingshih@gmail.com",
    url="https://github.com/tzing/hdtop",
    packages=["hdtop"],
    python_requires=">=3.6",
    entry_points={
        "console_scripts": ["hdtop = hdtop.__main__:main"],
    },
    install_requires=["httpx", "urwid"],
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Environment :: Console",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3 :: Only",
    ],
)
