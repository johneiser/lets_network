[![Documentation Status](https://readthedocs.org/projects/lets/badge/?version=latest)](https://lets.readthedocs.io/en/latest/?badge=latest)
[![Build Status](https://travis-ci.com/johneiser/lets_network.svg?branch=main)](https://travis-ci.com/johneiser/lets_network)
[![FOSSA Status](https://app.fossa.io/api/projects/git%2Bgithub.com%2Fjohneiser%2Flets_network.svg?type=shield)](https://app.fossa.io/projects/git%2Bgithub.com%2Fjohneiser%2Flets_network?ref=badge_shield)

# lets_network

A set of modules for miscellaneous computer networking, to be used in the [lets](https://github.com/johneiser/lets) framework.

## Requirements

- [docker](https://docs.docker.com/install/linux/docker-ce/ubuntu/)
- python >= 3.5
- python3-pip
- [lets](https://lets.readthedocs.io/en/latest/install.html)

## Install

**lets** is built on top of [docker](https://docs.docker.com/install/linux/docker-ce/ubuntu), so make sure it is installed. You may need to log out and back in for this to take effect.

```
$ curl -fsSL https://get.docker.com | sudo sh
$ sudo usermod -aG docker $USER
```

Install **lets**

```
$ pip3 install docker-lets
```

Install **lets_network**

```
$ pip3 install git+https://github.com/johneiser/lets_network.git
```

Activate **lets** *tab-completion* for bash.

```
$ lets support/autocomplete bash >> ~/.profile
$ source ~/.profile
$ lets sample/my[TAB][TAB]
sample/mydockermodule   sample/mymodule
```

## Usage

Quickstart:

```
$ echo SGVsbG8gd29ybGQhCg== | lets decode/base64
Hello world!
```

For further details, refer to the [docs](https://lets.readthedocs.io/en/latest/usage.html) and [modules](https://johneiser.github.io/lets_network/).

## License
[![FOSSA Status](https://app.fossa.io/api/projects/git%2Bgithub.com%2Fjohneiser%2Flets_network.svg?type=large)](https://app.fossa.io/projects/git%2Bgithub.com%2Fjohneiser%2Flets_network?ref=badge_large)
