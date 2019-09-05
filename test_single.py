import argparse
import os
import time
import gin
import gym
import numpy as np
from single_agent_env import make_single_env
from stable_baselines import PPO2
from stable_baselines.common.vec_env import DummyVecEnv, vec_normalize
from tensorflow import flags

FLAGS = flags.FLAGS
flags.DEFINE_string("name", None, "Name of experiment")
flags.DEFINE_multi_string("gin_file", None, "List of paths to the config files.")
flags.DEFINE_multi_string(
    "gin_param", None, "Newline separated list of Gin parameter bindings."
)


def test(experiment_name):
    model = PPO2.load(os.path.join(experiment_name, "model"))
    env = vec_normalize.VecNormalize(
        DummyVecEnv([make_single_env]), training=False, norm_reward=False
    )
    env.load_running_average(experiment_name)

    # Enjoy trained agent
    obs = env.reset()
    env.render()
    input()  # Wait until user presses key to start. Useful for video recording.
    ret = 0
    i = 0
    dones = np.array([False])
    while not np.all(dones):
        action, _states = model.predict(obs, deterministic=True)
        obs, rewards, dones, info = env.step(action)
        print(rewards)
        ret += rewards
        env.render()
        time.sleep(0.04)
        i += 1
    print("Steps: {:d}\tRet: {}".format(i, ret))


if __name__ == "__main__":
    gin.parse_config_files_and_bindings(FLAGS.gin_file, FLAGS.gin_param)
    test(FLAGS.name)
