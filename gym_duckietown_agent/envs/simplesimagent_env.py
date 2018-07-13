import os

import gym
from duckietown_slimremote.pc.robot import RemoteRobot
from gym import error, spaces, utils
from gym.utils import seeding
import numpy as np

from gym_duckietown_agent.config import CAMERA_HEIGHT, CAMERA_WIDTH
from matplotlib import pyplot as plt


class SimpleSimAgentEnv(gym.Env):
    """
    Simple road simulator to test RL training.
    Draws a road with turns using OpenGL, and simulates
    basic differential-drive dynamics.
    """

    metadata = {
        'render.modes': ['human', 'rgb_array'],
        'video.frames_per_second': 30  # do we need this on the client?
    }

    def __init__(self, debug=False):
        # Produce graphical output
        self.debug = debug

        # in the docker container this will be set to point to the
        # hostname of the `gym-duckietown-server` container, but in
        # the local test environment this will just map to localhost
        host = os.getenv("DUCKIETOWN_SERVER", "localhost")

        # Create ZMQ connection
        self.sim = RemoteRobot(host)

        # Tuple of velocity and steering angle, each in the range
        # [-1, 1] for full speed ahead, full speed backward, full
        # left turn, and full right turn respectively
        self.action_space = spaces.Box(
            low=-1,
            high=1,
            shape=(2,),
            dtype=np.float32
        )

        # We observe an RGB image with pixels in [0, 255]
        # Note: the pixels are in uint8 format because this is more compact
        # than float32 if sent over the network or stored in a dataset
        self.observation_space = spaces.Box(
            low=0,
            high=255,
            shape=(CAMERA_HEIGHT, CAMERA_WIDTH, 3),
            dtype=np.uint8
        )
        self.last_obs = np.zeros((CAMERA_HEIGHT, CAMERA_WIDTH, 3), np.uint8)

        self.reward_range = (-1000, 1000)

        self._windows_exists = False

        # Initialize the state
        self.seed()
        self.reset()  # FIXME: I'm quite sure this has to be called by the agent, like by gym convention

    def reset(self):
        """
        Reset the simulation at the start of a new episode
        This also randomizes many environment parameters (domain randomization)
        """

        self.sim.reset()

    def close(self):
        """
        Doesn't do anything,
        but should be used to end the simulation by gym convention
        """

        pass

    def seed(self, seed=None):
        # TODO: for now this function doesn't do anything.
        # The seed is on the side of the server. Therefore we
        # must transmit the seed to the server. But what if the
        # server is already running and seeded?

        # self.np_random, _ = seeding.np_random(seed)
        return [seed]

    def step(self, action):
        assert len(action) == 2
        action = np.array(action)
        obs, rew, done = self.sim.step(action, with_observation=True)
        return obs, rew, done, {}

    def _create_window(self):
        plt.ion()
        plt.ion()
        img = np.zeros((CAMERA_HEIGHT, CAMERA_WIDTH, 3))
        self._plt_img = plt.imshow(img, interpolation='none', animated=True, label="blah")
        self._plt_ax = plt.gca()

    def _draw_window(self, obs):
        if obs is not None:
            self._plt_img.set_data(obs)
            self._plt_ax.plot([0])
            plt.pause(0.001)  # I found this necessary - otherwise no visible img

    def render(self, mode='human', close=False):
        obs, _, _ = self.sim.observe()
        if mode == "rgb_array":
            return obs
        else:
            if not self._windows_exists:
                self._create_window()
                self._windows_exists = True
            self._draw_window(obs)


if __name__ == '__main__':
    import gym_duckietown_agent
    import time

    env = gym.make("SimpleSim-Agent-v0")

    env.reset()
    env.render(mode="human")

    for i in range(100):
        action = env.action_space.sample()
        obs, rew, done, misc = env.step(action)
        env.render(mode="human")

        if obs is None:
            obs_shape = "-no observation-"
        else:
            obs_shape = obs.shape

        print("action: {}, reward: {}, done: {}, misc: {}, obs shape: {}".format(
            action,
            rew,
            done,
            misc,
            obs_shape
        ))
        time.sleep(0.1)

    env.close()