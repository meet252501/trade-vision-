export interface PriceBar {
  ts: string; // "YYYY-MM-DD"
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export type TradeSide = "buy" | "sell";

export interface Trade {
  date: string; // "YYYY-MM-DD" or with time
  ticker: string;
  side: TradeSide;
  qty: number;
  price: number;
  value: number;
  pnl: number; // profit/loss dollar amount, or 0 if opening
}

export interface Signal {
  date: string;
  ticker: string;
  action: "BUY" | "SELL" | "HOLD";
  reason: string;
  momentum: number; // e.g. percent rate of change or trend score
  change_pct?: number; // active daily change
}

export interface MetricSet {
  total_return_pct: number;
  ann_return_pct: number;
  max_drawdown_pct: number;
  calmar_ratio: number;
  sharpe_ratio: number;
  sortino_ratio: number;
  win_rate_pct: number;
  profit_factor: number;
  volatility_pct: number;
}

export interface EquityCurvePoint {
  date: string;
  strategy: number;
  benchmark: number;
}

export interface DrawdownPoint {
  date: string;
  drawdown: number;
}

export interface BacktestResponse {
  equity_curve: EquityCurvePoint[];
  drawdown_series: DrawdownPoint[];
  trades: Trade[];
  metrics: MetricSet;
}

export type StrategyType = "Dual Momentum" | "SMA Crossover" | "Volatility Target";

export interface StrategyConfig {
  strategy: StrategyType;
  lookback: number; // in days, default 63
  top_n: number; // default 3
  max_pos_size: number; // default 30%
  sma_filter: boolean; // default true
  leverage_cap: number; // fixed 1.5
  tickers: string[];
}
