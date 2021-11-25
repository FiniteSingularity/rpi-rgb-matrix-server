Some example code for using a raspberry pi to draw text (including emojis) and twitch emotes to a HUB75 RGB matrix via an HTTP post endpoint.

In order for this code to run properly, you will first need to build/install the `rpi-rgb-led-matrix` library from https://github.com/hzeller/rpi-rgb-led-matrix .

Two tasks must be launched for the matrix to work: the flask server, and a celery server.  Due to how the `rpi-rgb-led-matrix` library works, the celery server must be run as root.
