"""
Schemas for public interfaces. Re-exports models from main for convenience.
"""
from src.api.main import DailyForecast, ClothingRecommendation, PopularPlace, TravelGuideResponse

__all__ = ["DailyForecast", "ClothingRecommendation", "PopularPlace", "TravelGuideResponse"]
