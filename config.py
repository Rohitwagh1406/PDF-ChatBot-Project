import os

class Config:
    DEBUG = True
    DEVELOPMENT = False
    SECRET_KEY = os.getenv("SECRET_KEY", "YOUR_API_KEY")

class ProductionConfig(Config):
    pass

class StagingConfig(Config):
    DEBUG = True

class DevelopmentConfig(Config):
    DEBUG = True
    DEVELOPMENT = True
