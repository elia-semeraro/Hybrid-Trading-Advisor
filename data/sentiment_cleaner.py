import pandas as pd
import re

class SentimentCleaner:
    """Simple cleaner for sentiment text data, removing only links."""
    
    def __init__(self):
        """Initialize regex pattern for cleaning."""
        # Pattern per URL
        self.url_pattern = r'http\S+|www\S+|https\S+'
    
    def clean_text(self, text: str) -> str:
        """
        Clean a single text string by removing links.
        
        Args:
            text (str): Input text to clean.
        
        Returns:
            str: Cleaned text, or empty string if invalid.
        """
        if not isinstance(text, str) or not text.strip():
            return ""
        
        # Rimuovi URL
        text = re.sub(self.url_pattern, '', text, flags=re.MULTILINE)
        
        # Rimuovi spazi multipli e strip
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text if text else ""
    
    def clean_sentiment_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean the 'text' column in the sentiment DataFrame.
        
        Args:
            df (pd.DataFrame): Input DataFrame with columns ['timestamp', 'text', 'source', 'ticker'].
        
        Returns:
            pd.DataFrame: DataFrame with additional 'cleaned_text' column, rows with empty cleaned_text removed.
        """
        if df.empty or 'text' not in df.columns:
            print("Warning: Empty DataFrame or missing 'text' column. Returning empty DataFrame.")
            return pd.DataFrame(columns=['timestamp', 'text', 'cleaned_text', 'source', 'ticker'])
        
        # Applica la pulizia alla colonna 'text'
        df['cleaned_text'] = df['text'].apply(self.clean_text)
        
        # Rimuovi righe con cleaned_text vuoto
        initial_rows = len(df)
        df = df[df['cleaned_text'] != '']
        removed_rows = initial_rows - len(df)
        if removed_rows > 0:
            print(f"Removed {removed_rows} rows with empty or invalid cleaned_text.")
        
        return df

if __name__ == "__main__":
    # Esempio di utilizzo
    cleaner = SentimentCleaner()
    
    # DataFrame di esempio
    sample_data = pd.DataFrame({
        'timestamp': [pd.Timestamp('2025-04-25 10:00:00+00:00'), pd.Timestamp('2025-04-25 09:00:00+00:00')],
        'text': [
            "Apple Q2 earnings beat expectations! 🚀 $AAPL up 10% https://t.co/example",
            "Apple unveils new iPhone 16 for $999... Amazing tech! 😊"
        ],
        'source': ['reddit_wallstreetbets', 'news'],
        'ticker': ['AAPL', 'AAPL']
    })
    
    cleaned_df = cleaner.clean_sentiment_data(sample_data)
    print(cleaned_df)