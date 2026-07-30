import numpy as np
import gymnasium as gym
from gymnasium import spaces

class TradingEnv(gym.Env):
    """A custom Trading Environment for Reinforcement Learning using Gymnasium."""
    metadata = {'render_modes': ['human']}

    def __init__(self, df, initial_balance=100000):
        super(TradingEnv, self).__init__()
        
        self.df = df
        self.initial_balance = initial_balance
        self.max_steps = len(self.df) - 1
        
        # Actions: 0 = Hold, 1 = Buy, 2 = Sell
        self.action_space = spaces.Discrete(3)
        
        # Observation space: Contains the last 5 days of normalized Close prices + Current Balance + Position Status
        self.window_size = 5
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(self.window_size + 2,), dtype=np.float32
        )
        
        self.reset()

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.current_step = self.window_size
        self.balance = self.initial_balance
        self.shares_held = 0
        self.net_worth = self.initial_balance
        self.max_net_worth = self.initial_balance
        
        return self._next_observation(), {}

    def _next_observation(self):
        # Get the historical price window
        obs = self.df['close'].values[self.current_step - self.window_size : self.current_step]
        # Normalize prices to the first price in the window
        obs = obs / obs[0]
        
        # Append internal state
        state = np.array([self.balance / self.initial_balance, float(self.shares_held > 0)])
        return np.concatenate((obs, state)).astype(np.float32)

    def step(self, action):
        self.current_step += 1
        current_price = self.df['close'].values[self.current_step]
        
        prev_net_worth = self.net_worth
        
        if action == 1: # Buy
            if self.balance > current_price:
                shares_bought = self.balance // current_price
                self.balance -= shares_bought * current_price
                self.shares_held += shares_bought
                
        elif action == 2: # Sell
            if self.shares_held > 0:
                self.balance += self.shares_held * current_price
                self.shares_held = 0
                
        self.net_worth = self.balance + (self.shares_held * current_price)
        self.max_net_worth = max(self.max_net_worth, self.net_worth)
        
        # Reward is simply the change in net worth (P&L)
        reward = self.net_worth - prev_net_worth
        
        terminated = self.net_worth <= 0 or self.current_step >= self.max_steps
        truncated = False
        
        return self._next_observation(), reward, terminated, truncated, {}

    def render(self):
        print(f"Step: {self.current_step} | Net Worth: ${self.net_worth:.2f} | Balance: ${self.balance:.2f} | Shares: {self.shares_held}")

# Example of how this would be trained in a future script:
# from stable_baselines3 import PPO
# env = TradingEnv(historical_dataframe)
# model = PPO("MlpPolicy", env, verbose=1)
# model.learn(total_timesteps=100000)
# model.save("ppo_trading_agent")
