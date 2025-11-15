"""
Registry-agnostic asset scoring and ranking.

Provides scoring algorithms that work with any registry's StandardizedAsset format.
Enables intelligent asset selection based on relevance, quality, and popularity.
"""

from typing import List
from ..registry_base import StandardizedAsset


def calculate_relevance(asset: StandardizedAsset, query: str) -> float:
    """
    Calculate relevance score for an asset based on query.
    
    Works with any registry since it operates on StandardizedAsset.
    
    Args:
        asset: StandardizedAsset to score
        query: Search query to match against
        
    Returns:
        Relevance score between 0.0 and 1.0
    """
    if not query:
        return 0.5
    
    score = 0.0
    query_words = query.lower().split()
    asset_name = asset.name.lower()
    
    # Name exact match gets highest score
    if query.lower() in asset_name:
        score += 1.0
    
    # Partial name matches
    for word in query_words:
        if word in asset_name:
            score += 0.7
    
    # Tag matches
    for tag in asset.tags:
        for word in query_words:
            if word in tag.lower():
                score += 0.5
    
    # Category matches
    for cat in asset.categories:
        for word in query_words:
            if word in cat.lower():
                score += 0.3
    
    return min(score, 1.0)  # Cap at 1.0


def score_and_rank_assets(
    assets: List[StandardizedAsset],
    query: str,
) -> List[StandardizedAsset]:
    """
    Score and rank assets by relevance, quality, and popularity.
    
    Registry-agnostic: Works with any registry's StandardizedAsset format.
    
    Args:
        assets: List of StandardizedAsset objects to score
        query: Search query for relevance calculation
        
    Returns:
        Sorted list of assets by total score (highest first)
    """
    # Calculate scores for each asset
    for asset in assets:
        relevance = calculate_relevance(asset, query)
        
        # Combined score: relevance (40%) + quality (30%) + popularity (20%) + rating (10%)
        total_score = (
            relevance * 0.4
            + asset.quality_score * 0.3
            + min(asset.download_count / 10000, 1.0) * 0.2
            + asset.rating * 0.1
        )
        
        # Store score on asset for sorting
        asset.score = total_score
    
    # Sort by total score (highest first)
    return sorted(assets, key=lambda a: a.score, reverse=True)
