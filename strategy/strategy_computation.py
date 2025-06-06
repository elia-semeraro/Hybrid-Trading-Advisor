class HybridStrategy:
    def __init__(self):
        pass  # Per ora non inizializziamo nulla, ma puoi aggiungere parametri in futuro

    def generate_trading_signal(self, RSI, ADX, PE_ratio, sentiment_score, rsi_mode):
        """
        Generates a trading signal based on RSI, ADX, P/E ratio, and sentiment score,
        with configurable RSI thresholds.

        Args:
            RSI (float): Relative Strength Index (0-100).
            ADX (float): Average Directional Index (0-100).
            PE_ratio (float): Price-to-Earnings ratio (positive).
            sentiment_score (float): Sentiment score (-100 to +100).
            rsi_mode (str, optional): RSI sensitivity mode.
                                   "conservative": RSI thresholds of 20 and 80.
                                   "standard" (default): RSI thresholds of 30 and 70.
                                   "aggressive": RSI thresholds of 40 and 60.
                                   Defaults to "standard".

        Returns:
            tuple: (final_signal, confidence_level, total_score)
               - final_signal: "Buy", "Hold", "Sell"
               - confidence_level: 1 to 5"

        Raises:
            ValueError: If any input value is invalid.
        """

        # 0. Input Validation
        if not 0 <= RSI <= 100:
            raise ValueError("RSI must be between 0 and 100")
        if not 0 <= ADX <= 100:
            raise ValueError("ADX must be between 0 and 100")
        if not -100 <= sentiment_score <= 100:
            raise ValueError("Sentiment score must be between -100 and 100")
        if rsi_mode not in ("conservative", "standard", "aggressive"):
            raise ValueError("Invalid rsi_mode")
        if PE_ratio <= 0:
            raise ValueError("P/E ratio must be positive")

        # 1. Determine Technical Signal from RSI and ADX
        if rsi_mode == "conservative":
            oversold_threshold = 35
            overbought_threshold = 65
        elif rsi_mode == "standard":
            oversold_threshold = 40
            overbought_threshold = 60
        elif rsi_mode == "aggressive":
            oversold_threshold = 45
            overbought_threshold = 55
        else:  # If rsi_mode is invalid, default to standard
            oversold_threshold = 40
            overbought_threshold = 60

        if RSI < oversold_threshold and ADX > 15:
            technical_signal = "Buy"
        elif RSI > overbought_threshold and ADX > 15:
            technical_signal = "Sell"
        else:
            technical_signal = "Hold"

        # 2. Determine Sentiment Signal
        if sentiment_score > 0:
            sentiment_signal = "Buy"
        elif sentiment_score < 0:
            sentiment_signal = "Sell"
        else:
            sentiment_signal = "Neutral"

        # 3. Combine Technical and Sentiment Signals (Basic Strategy)
        if technical_signal == "Buy" and sentiment_signal == "Buy":
            final_signal = "Buy"
        elif technical_signal == "Sell" and sentiment_signal == "Sell":
            final_signal = "Sell"
        elif RSI > overbought_threshold and sentiment_score > 25 and ADX >= 20:
            final_signal = "Buy"  # continuation case
        elif RSI < oversold_threshold and sentiment_score < -25 and ADX >= 20:
            final_signal = "Sell"  # continuation case
        else:
            final_signal = "Hold"

        # 4. Calculate Total Score (Extended Strategy) - Only if final_signal is Buy or Sell
        if final_signal in ("Buy", "Sell"):
            abs_sentiment_score = abs(sentiment_score)
            abs_technical_score = abs(RSI - 50) * 2

            # Avoid division by zero
            if abs_sentiment_score == 0:
                total_score = 0
            else:
                total_score = (0.6 * abs_technical_score + 0.4 * abs_sentiment_score) 
        else:
            total_score = 0  # Default for "Hold"

        # 5. Apply P/E Ratio as Confidence Multiplier - Only if total_score > 0
        if total_score > 0:
            multiplier = 1.0
            if final_signal == "Buy":
                if PE_ratio < 15:
                    multiplier = 1.1
                elif PE_ratio > 25:
                    multiplier = 0.9
            elif final_signal == "Sell":
                if PE_ratio > 25:
                    multiplier = 1.1
                elif PE_ratio < 15:
                    multiplier = 0.9

            total_score *= multiplier

        # 6. Determine Final Signal and Confidence Level based on Total Score
        if final_signal == "Hold":
            confidence_level = "100%"   # Default for "Hold"
        elif total_score >= 80:
            final_signal = "Buy" if final_signal == "Buy" else "Sell"
            confidence_level = f"{int(total_score)}%"
        elif 60 <= total_score < 80:
            confidence_level = f"{int(total_score)}%"
        elif 20 <= total_score < 60:
            final_signal = "Buy" if final_signal == "Buy" else "Sell"
            confidence_level = f"{int(total_score)}%" 
        else:  # 0 <= total_score < 20
            confidence_level = f"{int(total_score)}%" 


        # 7. Build Explanation
        if final_signal == "Hold":
            explanation = "Indicators are not aligned, or momentum is weak: no action recommended."
        elif final_signal == "Buy":
            if RSI > overbought_threshold and sentiment_score > 25:
                explanation = "Despite overbought condition, strong bullish sentiment suggests a continuation of the uptrend."
            elif RSI < oversold_threshold and sentiment_score > 0:
                explanation = "Oversold condition and positive sentiment indicate a likely reversal upward: buying opportunity."
            else:
                explanation = "Moderate bullish sentiment and RSI positioning suggest a possible upward move."
        elif final_signal == "Sell":
            if RSI < oversold_threshold and sentiment_score < -25:
                explanation = "Despite oversold condition, strong bearish sentiment suggests a continuation of the downtrend."
            elif RSI > overbought_threshold and sentiment_score < 0:
                explanation = "Overbought condition and negative sentiment indicate a likely reversal downward: selling opportunity."
            else:
                explanation = "Moderate bearish sentiment and RSI positioning suggest a possible downward move."
        else:
            explanation = "Input conditions are unclear or inconsistent: holding as precaution."


        return final_signal, confidence_level, total_score, explanation
