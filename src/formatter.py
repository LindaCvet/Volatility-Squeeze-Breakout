from .data_sources import localize_ts
import math

def _format_price(x: float, mode="auto", fixed=2):
    if mode == "fixed":
        return f"{x:.{fixed}f}"
    # auto: vienkāršs heuristisks noapaļojums
    absx = abs(x)
    if absx < 0.1:
        dec = 5
    elif absx < 1:
        dec = 4
    elif absx < 10:
        dec = 3
    elif absx < 100:
        dec = 2
    else:
        dec = 2
    return f"{x:.{dec}f}"

def get_signal_comment(direction: str, row, cfg) -> str:
    # Interpretācija ar RSI/ADX
    ma_state = ("virs" if row["close"] > row["ma_fast"] else "zem",
                "virs" if row["close"] > row["ma_slow"] else "zem")
    vol_pct = None
    if row["vol_sma"] and row["vol_sma"] > 0:
        vol_pct = (row["volume"] / row["vol_sma"] - 1) * 100

    # Bāzes uz “vērts/pagaidi/nav vērts”
    if direction == "up":
        strong = (row["filters_ok_up"] and
                  (not cfg.USE_RSI_FILTER or row["rsi"] >= cfg.RSI_LONG_MIN) and
                  (not cfg.USE_ADX_FILTER or row["adx"] >= cfg.ADX_MIN))
        if strong:
            return "🟢 Vērts pirkt (bullish breakout)"
        else:
            return "🟡 Pagaidi — apstiprinājums vājš"
    else:
        strong_down = (row["filters_ok_dn"] and
                       (not cfg.USE_ADX_FILTER or row["adx"] >= cfg.ADX_MIN))
        if strong_down:
            return "🔴 Nav vērts pirkt (bearish breakout)"
        else:
            return "🟠 Pagaidi — iespējams viltus izlauziens"

def levels_for_long(row, cfg):
    # Entry/SL/TP tikai pie “Vērts pirkt”
    entry = row["close"]
    if cfg.ENTRY_USE_BUFFER:
        entry = entry + cfg.ENTRY_BUFFER_ATR * row["atr"]
    sl = entry - cfg.SL_ATR_MULT * row["atr"]
    r = entry - sl
    tps = [entry + m * r for m in cfg.TP_MULTS]
    fmt = lambda x: _format_price(x, cfg.ROUNDING_MODE, cfg.FIXED_DECIMALS)
    return {
        "entry": fmt(entry),
        "sl": fmt(sl),
        "tps": [fmt(x) for x in tps],
    }

def format_message(symbol: str, timeframe: str, res, cfg) -> str:
    row = res["row"]
    direction = res["direction"]

    bbwidth = row["bb_width"] if row["bb_width"] == row["bb_width"] else 0.0
    vol_pct = 0.0
    if row["vol_sma"] and row["vol_sma"] > 0:
        vol_pct = (row["volume"] / row["vol_sma"] - 1) * 100

    ma_fast_state = "virs" if row["close"] > row["ma_fast"] else "zem"
    ma_slow_state = "virs" if row["close"] > row["ma_slow"] else "zem"

    head = f"[SQUEEZE] {symbol} {timeframe} → "
    if direction == "up":
        head += "breakout_up ✅"
    else:
        head += "breakout_down ⬇"

    # pamatlīnija
    base = (
        f"Cena: {_format_price(row['close'], cfg.ROUNDING_MODE, cfg.FIXED_DECIMALS)} | "
        f"BBWidth: {bbwidth:.4f} | "
        f"Vol {vol_pct:+.0f}% vs. SMA{int(cfg.VOL_SMA_WIN)} | "
        f"MA{cfg.MA_FAST}/{cfg.MA_SLOW}: {ma_fast_state}/{ma_slow_state} | "
        f"ATR{cfg.ATR_PERIOD}: {_format_price(row['atr'], cfg.ROUNDING_MODE, cfg.FIXED_DECIMALS)} | "
        f"RSI{cfg.RSI_PERIOD}: {row['rsi']:.1f} | ADX{cfg.ADX_PERIOD}: {row['adx']:.1f}"
    )

    comment = get_signal_comment(direction, row, cfg)

    lines = [head, base, comment]

    # Entry/SL/TP tikai, ja “Vērts pirkt”
    if comment.startswith("🟢"):
        lv = levels_for_long(row, cfg)
        tp_parts = [f"TP{i+1}: {p}" for i, p in enumerate(lv["tps"])]
        lines.append(f"Entry: {lv['entry']} | SL: {lv['sl']} | " + " | ".join(tp_parts))

    return "\n".join(lines)
