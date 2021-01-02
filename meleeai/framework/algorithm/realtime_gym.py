import gym
import gym.spaces as spaces
import json
import logging
import numpy as np

from meleeai.utils.controller_parser import ControllerParser
from meleeai.utils.message_type import MessageType
from meleeai.utils.slippi_parser import SlippiParser
from rtgym import RealTimeGymInterface, DEFAULT_CONFIG_DICT

class RealTimeInterface(RealTimeGymInterface):
    """A Real Time Gym implementation"""
    def __init__(self, observation_collect_func, network_send_func):
        """Initialization function for RealTimeInterface.
        :param observation_collect_func: Functional parameter to retrieve published data from Data Manager.
        :param network_send_func: Functional parameter to send data to Ishiiruka Alfred.
        """
        assert callable(observation_collect_func), logging.error('Parameter passed must be of type function (callable).')
        assert callable(network_send_func), logging.error('Parameter passed must be of type function (callable).')

        self._controller_parser = ControllerParser()
        self._slippi_parser     = SlippiParser()
        self._realtime_env      = None

        self._obs_func          = observation_collect_func
        self._net_send_func     = network_send_func

        # TODO: Update my_config, add to absl.FLAGS
        self.my_config = DEFAULT_CONFIG_DICT
        self.my_config["interface"] = self
        self.my_config["time_step_duration"] = 0.05
        self.my_config["start_obs_capture"] = 0.05
        self.my_config["time_step_timeout_factor"] = 1.0
        self.my_config["ep_max_length"] = 100
        self.my_config["act_buf_len"] = 4
        self.my_config["reset_act_buf"] = False

    def has_initialized(self):
        return self._realtime_env is not None

    def initialize(self):
        if not self.has_initialized():
            published_data = self._obs_func()
            if published_data:
                for (message_type, _, _) in published_data:
                    if isinstance(message_type, MessageType.VIDEO):
                        self._realtime_env = gym.make("rtgym:real-time-gym-v0", config=self.my_config)
                        break

    def send_control(self, control):
        """
        Non-blocking function
        Applies the action given by the RL policy
        If control is None, does nothing
        Args:
            control: np.array of the dimension of the action-space
        """
        # if control is not None:
        #     ...
        self._net_send_func(
            bytes(
                json.dumps(self._controller_parser.parse_list(control.to_jsonable())), encoding='utf-8'
            )
        )

    def reset(self):
        """
        Returns:
            obs: must be a list
        Note: Do NOT put the action buffer in the returned obs (automated)
        """
        # return obs

        raise NotImplementedError

    def wait(self):
        """
        Non-blocking function
        The agent stays 'paused', waiting in position
        """
        self.send_control(self.get_default_action())

    def get_obs_rew_done(self):
        """
        Returns:
            obs: list
            rew: scalar
            done: boolean
        Note: Do NOT put the action buffer in obs (automated)
        """
        # return obs, rew, done

        raise NotImplementedError

    def get_observation_space(self):
        """
        Returns:
            observation_space: gym.spaces.Tuple
        Note: Do NOT put the action buffer here (automated)
        """
        # return spaces.Tuple(...)
        init_obs_space = self._obs_func()
        video_data = [x[1] for x in init_obs_space if x[0] == MessageType.VIDEO][0]

        video_space                         = spaces.Box(0, 255, [reversed(video_data.size), 3])
        slippi_pre_space, slippi_post_space = self._slippi_parser.get_domain_restriction()
        return spaces.Tuple((video_space, slippi_pre_space, slippi_post_space))

    def get_action_space(self):
        """
        Returns:
            action_space: gym.spaces.Box
        """
        # return spaces.Box(...)

        raise NotImplementedError

    def get_default_action(self):
        """
        Returns:
            default_action: numpy array of the dimension of the action space
        initial action at episode start
        """
        # return np.array([...], dtype='float32')

        raise NotImplementedError

    def render(self):
        """
        Optional: implement this if you want to use the render() method of the gym environment
        """
        pass

