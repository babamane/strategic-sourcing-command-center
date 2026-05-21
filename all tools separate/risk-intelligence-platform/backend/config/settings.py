from dotenv import load_dotenv
import os

load_dotenv()


class Settings:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

    SHODAN_API_KEY = os.getenv("SHODAN_API_KEY")
    OTX_API_KEY = os.getenv("OTX_API_KEY")
    ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
    OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
    NVD_API_KEY = os.getenv("NVD_API_KEY")

    DATABASE_URL = os.getenv("DATABASE_URL")

    APP_ENV = os.getenv("APP_ENV")
    LOG_LEVEL = os.getenv("LOG_LEVEL")


settings = Settings()
