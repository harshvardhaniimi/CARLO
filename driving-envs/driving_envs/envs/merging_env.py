import io
import math
import time
from typing import Dict, Text, Tuple
import gin
import gym
from PIL import Image
import numpy as np
import scipy.special
from driving_envs.world import World
from driving_envs.agents import Car, Building, Pedestrian, Painting
from driving_envs.geometry import Point

expit = scipy.special.expit


class TurningEnv(gym.Env):
    """Driving gym interface."""

    def __init__(self, dt: float = 0.04, width: int = 120, height: int = 120):
        super(TurningEnv, self).__init__()
        self.dt, self.width, self.height = dt, width, height
        self.world = World(self.dt, width=width, height=height, ppm=6)
        self.buildings, self.cars = [], {}

    def step(self, action: np.ndarray):
        offset = 0
        for agent in self.world.dynamic_agents:
            agent.set_control(*action[offset : offset + 2])
            offset += 2
        self.world.tick()  # This ticks the world for one time step (dt second)
        done = False
        reward = {name: self._get_car_reward(name) for name in self.cars.keys()}
        if self.cars["R"].collidesWith(self.cars["H"]):
            reward["H"] -= 200
            reward["R"] -= 200
            done = True
        for car_name, car in self.cars.items():
            for building in self.buildings:
                if car.collidesWith(building):
                    reward[car_name] -= 200
                    done = True
            if car_name == "R" and car.y >= self.height or car.y <= 0 or car.x <= 0:
                done = True
        return self.world.state, reward, done, {}

    def _get_vel_reward(self, car):
        vel_rew = 0
        if car.y <= 80:
            vel_rew = car.velocity.y
        elif car.y >= 86:
            vel_rew = -car.velocity.y
        else:
            vel_rew = -car.velocity.x
            # Orient car angle to turn left.
            # vel_rew -= np.square(np.pi - car.state[4])
        return vel_rew

    def _get_pos_reward(self, car):
        car_pos = np.array((car.x, car.y))
        target = np.array((0.0, 83.0))
        return -np.linalg.norm(target - car_pos, ord=1) / 10

    def _get_car_reward(self, name: Text):
        car = self.cars[name]
        vel_rew = self._get_vel_reward(car)
        control_cost = np.square(car.inputAcceleration)
        return 0.1 * vel_rew - 0.0 * control_cost

    def reset(self):
        self.world.reset()
        self.buildings = [
            Building(Point(28.5, 40), Point(57, 80), "gray80"),
            Building(Point(28.5, 103), Point(57, 34), "gray80"),
            Building(Point(91.5, 60), Point(57, 120), "gray80"),
        ]
        self.cars = {
            "H": Car(Point(58.5, 10), np.pi / 2),
            "R": Car(Point(58.5, 5), np.pi / 2, "blue"),
        }
        for building in self.buildings:
            self.world.add(building)
        # NOTE: Order that dynamic agents are added to world determines
        # the concatenated state and action representation.
        self.world.add(self.cars["H"])
        self.world.add(self.cars["R"])
        self.cars["H"].velocity = Point(0, 7)
        self.cars["R"].velocity = Point(0, 7)
        return self.world.state

    def render(self, mode="human"):
        if mode != "human":
            raise NotImplementedError("Unsupported mode: {}".format(mode))
        self.world.render()


class MergingEnv(gym.Env):
    """Driving gym interface."""

    def __init__(
        self,
        dt: float = 0.04,
        width: int = 120,
        height: int = 120,
        ctrl_cost_weight: float = 0.0,
        time_limit: int = 200
    ):
        super(MergingEnv, self).__init__()
        self.dt, self.width, self.height = dt, width, height
        self.world = World(self.dt, width=width, height=height, ppm=6)
        self.buildings, self.cars = [], {}
        self._ctrl_cost_weight = ctrl_cost_weight
        self.time_limit = time_limit

    def step(self, action: np.ndarray):
        self.step_num += 1
        offset = 0
        for agent in self.world.dynamic_agents:
            agent.set_control(*action[offset : offset + 2])
            offset += 2
        self.world.tick()  # This ticks the world for one time step (dt second)
        done = False
        reward = {name: self._get_car_reward(name) for name in self.cars.keys()}
        if self.cars["R"].collidesWith(self.cars["H"]):
            done = True
            reward["H"] -= 200
            reward["R"] -= 200
        for car_name, car in self.cars.items():
            for building in self.buildings:
                if car.collidesWith(building):
                    done = True
                    reward[car_name] -= 200
            if car_name == "R" and car.y >= self.height or car.y <= 0:
                done = True
        if self.step_num >= self.time_limit:
            done = True
        if done:
            for car_name, car in self.cars.items():
                reward[car_name] += 200*((car.y/self.height)**4)
        return self.world.state, reward, done, {}

    def _get_car_reward(self, name: Text):
        car = self.cars[name]
        dist_rew = -0.008 * (self.height - car.y)
        right_lane_cost = 0.01 * np.abs(car.x - 58.5)
        control_cost = np.square(car.inputAcceleration)
        return dist_rew - right_lane_cost - self._ctrl_cost_weight * control_cost

    def reset(self):
        self.world.reset()
        self.buildings = [
            Building(Point(28.5, 60), Point(57, 120), "gray80"),
            # Building(Point(66.7, 115.9), Point(10, 10.19), "gray80", heading=0.1974),
            Building(Point(91.5, 60), Point(57, 120), "gray80"),
        ]
        self.cars = {
            "H": Car(Point(58.5, 5), np.pi / 2),
            "R": Car(Point(61.5, 5), np.pi / 2, "blue"),
        }
        for building in self.buildings:
            self.world.add(building)
        # NOTE: Order that dynamic agents are added to world determines
        # the concatenated state and action representation.
        self.world.add(self.cars["H"])
        self.world.add(self.cars["R"])
        self.cars["H"].velocity = Point(0, 10)
        self.cars["R"].velocity = Point(0, 10)
        self.step_num = 0
        return self.world.state

    def render(self, mode="human"):
        if mode != "human":
            raise NotImplementedError("Unsupported mode: {}".format(mode))
        self.world.render()


class MergingEnv2(gym.Env):
    """Driving gym interface."""

    def __init__(
        self,
        dt: float = 0.1,
        width: int = 120,
        height: int = 120,
        ctrl_cost_weight: float = 0.0,
        time_limit: int = 60
    ):
        super(MergingEnv2, self).__init__()
        self.dt, self.width, self.height = dt, width, height
        self.world = World(self.dt, width=width, height=height, ppm=6)
        self.buildings, self.cars = [], {}
        self._ctrl_cost_weight = ctrl_cost_weight
        self.time_limit = time_limit

    def step(self, action: np.ndarray):
        self.step_num += 1
        offset = 0
        for agent in self.world.dynamic_agents:
            agent.set_control(*action[offset : offset + 2])
            offset += 2
        self.world.tick()  # This ticks the world for one time step (dt second)
        done = False
        reward = {name: self._get_car_reward(name) for name in self.cars.keys()}
        if self.cars["R"].collidesWith(self.cars["H"]):
            done = True
        for car_name, car in self.cars.items():
            for building in self.buildings:
                if car.collidesWith(building):
                    done = True
            if car_name == "R" and car.y >= self.height or car.y <= 0:
                raise ValueError("Car went out of bounds!")
        if self.step_num >= self.time_limit:
            done = True
        return self.world.state, reward, done, {}

    def _get_car_reward(self, name: Text):
        car = self.cars[name]
        vel_rew = .1 * car.velocity.y
        right_lane_cost = expit((car.y - 60)/7) * max(car.x - 58.5, 0)
        # right_lane_cost = .1 * max(car.x - 59, 0)
        control_cost = np.square(car.inputAcceleration)
        return vel_rew - right_lane_cost - self._ctrl_cost_weight * control_cost

    def reset(self):
        self.world.reset()
        self.buildings = [
            Building(Point(28.5, 60), Point(57, 120), "gray80"),
            Building(Point(91.5, 60), Point(57, 120), "gray80"),
            Building(Point(62, 90), Point(2, 60), "gray80"),
        ]
        self.cars = {
            "H": Car(Point(58.5, 5), np.pi / 2),
            "R": Car(Point(61.5, 5), np.pi / 2, "blue"),
        }
        for building in self.buildings:
            self.world.add(building)
        # NOTE: Order that dynamic agents are added to world determines
        # the concatenated state and action representation.
        self.world.add(self.cars["H"])
        self.world.add(self.cars["R"])
        self.cars["H"].velocity = Point(0, 10)
        self.cars["R"].velocity = Point(0, 10)
        self.step_num = 0
        return self.world.state

    def render(self, mode="human"):
        self.world.render()
        if mode == "rgb_array":
            cnv = self.world.visualizer.win
            ps = cnv.postscript(colormode = 'color')
            img = Image.open(io.BytesIO(ps.encode('utf-8')))
            return np.array(img)
