import time
import pygame
from single_agent_env import make_single_env

LEFT_Y_AXIS = 1
RIGHT_X_AXIS = 3


def main():
    pygame.init()
    pygame.joystick.init()
    joysticks = [pygame.joystick.Joystick(x) for x in range(pygame.joystick.get_count())]
    joystick = joysticks[0]
    joystick.init()
    env = make_single_env()
    for _ in range(1):
        done = False
        obs = env.reset()
        env.render()
        episode_data = []
        i = 0
        ret = 0
        print("Starting in 5!")
        time.sleep(5)
        while not done:
            pygame.event.pump()
            action = (
                -0.3 * joystick.get_axis(RIGHT_X_AXIS),
                -1 * joystick.get_axis(LEFT_Y_AXIS),
            )
            next_obs, rew, done, debug = env.step(action)
            ret += rew
            del debug
            episode_data.append((obs, action, rew, next_obs, done))
            obs = next_obs
            env.render()
            time.sleep(env.multi_env.dt)
            i += 1
        print("i: {}, Return: {}".format(i, ret))
    env.multi_env.world.close()
    return


if __name__ == "__main__":
    main()