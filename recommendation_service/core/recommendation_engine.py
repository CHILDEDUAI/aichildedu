"""
Recommendation Engine Core Implementation
"""

import logging
from typing import Dict, List, Optional, Tuple
from uuid import UUID

import numpy as np
from scipy.spatial.distance import cosine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from ..models.recommendation import (
    ContentFeatureVector,
    RecommendationHistory,
    UserContentInteraction,
    UserPreference
)
from ..schemas.recommendation import (
    InteractionType,
    RecommendationType,
    RecommendationResponse
)

logger = logging.getLogger(__name__)

class RecommendationEngine:
    """Core recommendation engine implementing multiple recommendation strategies"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.interaction_weights = {
            InteractionType.VIEW: 1.0,
            InteractionType.COMPLETE: 3.0,
            InteractionType.LIKE: 2.0,
            InteractionType.BOOKMARK: 2.5
        }
    
    async def get_recommendations(
        self,
        user_id: UUID,
        content_type: Optional[str] = None,
        subject: Optional[str] = None,
        difficulty_level: Optional[str] = None,
        limit: int = 10
    ) -> List[RecommendationResponse]:
        """
        Get personalized recommendations for a user using hybrid approach
        
        Args:
            user_id: Target user ID
            content_type: Optional content type filter
            subject: Optional subject filter
            difficulty_level: Optional difficulty level filter
            limit: Maximum number of recommendations to return
            
        Returns:
            List of recommended content items with scores
        """
        # Get user preferences
        user_prefs = await self._get_user_preferences(user_id)
        
        # Get content-based recommendations
        content_based_recs = await self._get_content_based_recommendations(
            user_id,
            user_prefs,
            content_type,
            subject,
            difficulty_level,
            limit
        )
        
        # Get collaborative filtering recommendations
        collab_recs = await self._get_collaborative_recommendations(
            user_id,
            content_type,
            subject,
            difficulty_level,
            limit
        )
        
        # Combine recommendations using hybrid strategy
        final_recs = await self._hybrid_merge_recommendations(
            content_based_recs,
            collab_recs,
            limit
        )
        
        # Record recommendations in history
        await self._record_recommendations(user_id, final_recs)
        
        return final_recs
    
    async def _get_user_preferences(self, user_id: UUID) -> Optional[UserPreference]:
        """Get user preferences from database"""
        result = await self.db.execute(
            select(UserPreference).where(UserPreference.user_id == user_id)
        )
        return result.scalars().first()
    
    async def _record_recommendations(
        self,
        user_id: UUID,
        recommendations: List[RecommendationResponse]
    ) -> None:
        """Record recommendations in history"""
        for rec in recommendations:
            history = RecommendationHistory(
                user_id=user_id,
                content_id=rec.content_id,
                recommendation_type=rec.recommendation_type,
                score=rec.score,
                metadata=rec.metadata
            )
            self.db.add(history)
        await self.db.commit()
    
    def _calculate_similarity_score(
        self,
        vec1: List[float],
        vec2: List[float]
    ) -> float:
        """Calculate cosine similarity between two vectors"""
        if not vec1 or not vec2:
            return 0.0
        return 1 - cosine(vec1, vec2)  # Convert distance to similarity
    
    def _normalize_scores(
        self,
        scores: List[float],
        min_score: float = 0.0,
        max_score: float = 1.0
    ) -> List[float]:
        """Normalize scores to range [min_score, max_score]"""
        if not scores:
            return []
        
        scores_array = np.array(scores)
        score_min = scores_array.min()
        score_max = scores_array.max()
        
        if score_min == score_max:
            return [max_score] * len(scores)
            
        normalized = (scores_array - score_min) / (score_max - score_min)
        return (normalized * (max_score - min_score) + min_score).tolist() 
    
    async def _get_content_based_recommendations(
        self,
        user_id: UUID,
        user_prefs: Optional[UserPreference],
        content_type: Optional[str] = None,
        subject: Optional[str] = None,
        difficulty_level: Optional[str] = None,
        limit: int = 10
    ) -> List[RecommendationResponse]:
        """
        Get content-based recommendations based on user preferences and content features
        """
        # Get user's interaction history
        interactions = await self._get_user_interactions(user_id)
        if not interactions and not user_prefs:
            return []
            
        # Get content feature vectors
        content_vectors = await self._get_content_feature_vectors(
            content_type,
            subject,
            difficulty_level
        )
        if not content_vectors:
            return []
            
        # Calculate user profile vector from interactions and preferences
        user_profile = await self._calculate_user_profile(
            user_id,
            interactions,
            user_prefs
        )
        
        # Calculate similarity scores
        recommendations = []
        for content_id, feature_vector in content_vectors.items():
            # Skip already interacted content
            if content_id in {i.content_id for i in interactions}:
                continue
                
            similarity = self._calculate_similarity_score(
                user_profile,
                feature_vector
            )
            
            if similarity > 0:
                recommendations.append(
                    RecommendationResponse(
                        content_id=content_id,
                        score=similarity,
                        recommendation_type=RecommendationType.CONTENT_BASED,
                        metadata={
                            "similarity_score": similarity,
                            "recommendation_source": "content_based"
                        }
                    )
                )
        
        # Sort by score and limit results
        recommendations.sort(key=lambda x: x.score, reverse=True)
        return recommendations[:limit]
    
    async def _get_user_interactions(
        self,
        user_id: UUID
    ) -> List[UserContentInteraction]:
        """Get user's content interaction history"""
        result = await self.db.execute(
            select(UserContentInteraction)
            .where(UserContentInteraction.user_id == user_id)
            .order_by(UserContentInteraction.created_at.desc())
        )
        return result.scalars().all()
    
    async def _get_content_feature_vectors(
        self,
        content_type: Optional[str] = None,
        subject: Optional[str] = None,
        difficulty_level: Optional[str] = None
    ) -> Dict[UUID, List[float]]:
        """Get content feature vectors with optional filtering"""
        query = select(ContentFeatureVector)
        
        # Apply filters if provided
        if content_type or subject or difficulty_level:
            filters = []
            if content_type:
                filters.append(ContentFeatureVector.metadata["content_type"].astext == content_type)
            if subject:
                filters.append(ContentFeatureVector.metadata["subject"].astext == subject)
            if difficulty_level:
                filters.append(ContentFeatureVector.metadata["difficulty_level"].astext == difficulty_level)
            
            if filters:
                query = query.where(and_(*filters))
        
        result = await self.db.execute(query)
        vectors = result.scalars().all()
        
        return {v.content_id: v.feature_vector for v in vectors}
    
    async def _calculate_user_profile(
        self,
        user_id: UUID,
        interactions: List[UserContentInteraction],
        user_prefs: Optional[UserPreference]
    ) -> List[float]:
        """
        Calculate user profile vector based on interactions and preferences
        """
        if not interactions and not user_prefs:
            return []
            
        # Get feature vectors for interacted content
        interacted_content_ids = [i.content_id for i in interactions]
        if interacted_content_ids:
            result = await self.db.execute(
                select(ContentFeatureVector)
                .where(ContentFeatureVector.content_id.in_(interacted_content_ids))
            )
            content_vectors = {v.content_id: v.feature_vector for v in result.scalars().all()}
        else:
            content_vectors = {}
            
        # Calculate weighted average of interacted content vectors
        profile_vector = None
        total_weight = 0.0
        
        for interaction in interactions:
            if interaction.content_id not in content_vectors:
                continue
                
            vector = content_vectors[interaction.content_id]
            weight = (
                self.interaction_weights.get(interaction.interaction_type, 1.0) *
                interaction.engagement_score
            )
            
            if profile_vector is None:
                profile_vector = np.array(vector) * weight
            else:
                profile_vector += np.array(vector) * weight
            
            total_weight += weight
        
        if profile_vector is not None and total_weight > 0:
            profile_vector = profile_vector / total_weight
        
        # Incorporate user preferences if available
        if user_prefs and profile_vector is not None:
            pref_vector = await self._calculate_preference_vector(user_prefs)
            if pref_vector:
                profile_vector = (profile_vector + np.array(pref_vector)) / 2
        elif user_prefs:
            pref_vector = await self._calculate_preference_vector(user_prefs)
            if pref_vector:
                profile_vector = np.array(pref_vector)
        
        return profile_vector.tolist() if profile_vector is not None else []
    
    async def _calculate_preference_vector(
        self,
        user_prefs: UserPreference
    ) -> Optional[List[float]]:
        """Calculate feature vector from user preferences"""
        # Implementation depends on how preferences map to feature space
        # This is a placeholder that should be customized based on your feature engineering
        return None  # TODO: Implement preference to feature vector mapping 
    
    async def _get_collaborative_recommendations(
        self,
        user_id: UUID,
        content_type: Optional[str] = None,
        subject: Optional[str] = None,
        difficulty_level: Optional[str] = None,
        limit: int = 10
    ) -> List[RecommendationResponse]:
        """
        Get collaborative filtering recommendations based on user similarity
        """
        # Get target user's interactions
        user_interactions = await self._get_user_interactions(user_id)
        if not user_interactions:
            return []
            
        # Get similar users
        similar_users = await self._find_similar_users(user_id, user_interactions)
        if not similar_users:
            return []
            
        # Get recommendations from similar users
        recommendations = await self._get_recommendations_from_similar_users(
            user_id,
            similar_users,
            content_type,
            subject,
            difficulty_level
        )
        
        # Sort by score and limit results
        recommendations.sort(key=lambda x: x.score, reverse=True)
        return recommendations[:limit]
    
    async def _find_similar_users(
        self,
        user_id: UUID,
        user_interactions: List[UserContentInteraction]
    ) -> List[Tuple[UUID, float]]:
        """Find users with similar content interaction patterns"""
        # Get all users who interacted with the same content
        interacted_content_ids = {i.content_id for i in user_interactions}
        if not interacted_content_ids:
            return []
            
        result = await self.db.execute(
            select(UserContentInteraction)
            .where(
                and_(
                    UserContentInteraction.content_id.in_(interacted_content_ids),
                    UserContentInteraction.user_id != user_id
                )
            )
        )
        other_users_interactions = result.scalars().all()
        
        # Group interactions by user
        user_interactions_map = {}
        for interaction in other_users_interactions:
            if interaction.user_id not in user_interactions_map:
                user_interactions_map[interaction.user_id] = []
            user_interactions_map[interaction.user_id].append(interaction)
        
        # Calculate similarity scores
        user_similarities = []
        target_user_vector = self._create_interaction_vector(
            user_interactions,
            interacted_content_ids
        )
        
        for other_user_id, interactions in user_interactions_map.items():
            other_user_vector = self._create_interaction_vector(
                interactions,
                interacted_content_ids
            )
            
            similarity = self._calculate_similarity_score(
                target_user_vector,
                other_user_vector
            )
            
            if similarity > 0:
                user_similarities.append((other_user_id, similarity))
        
        # Sort by similarity score
        user_similarities.sort(key=lambda x: x[1], reverse=True)
        return user_similarities[:10]  # Return top 10 similar users
    
    def _create_interaction_vector(
        self,
        interactions: List[UserContentInteraction],
        content_ids: set
    ) -> List[float]:
        """Create a vector representation of user interactions"""
        # Create a vector where each position represents interaction strength with a content
        vector = [0.0] * len(content_ids)
        content_id_to_index = {id_: idx for idx, id_ in enumerate(sorted(content_ids))}
        
        for interaction in interactions:
            if interaction.content_id in content_id_to_index:
                idx = content_id_to_index[interaction.content_id]
                weight = self.interaction_weights.get(interaction.interaction_type, 1.0)
                vector[idx] = weight * interaction.engagement_score
        
        return vector
    
    async def _get_recommendations_from_similar_users(
        self,
        user_id: UUID,
        similar_users: List[Tuple[UUID, float]],
        content_type: Optional[str] = None,
        subject: Optional[str] = None,
        difficulty_level: Optional[str] = None
    ) -> List[RecommendationResponse]:
        """Get recommendations based on similar users' interactions"""
        # Get target user's interacted content
        user_interactions = await self._get_user_interactions(user_id)
        user_content_ids = {i.content_id for i in user_interactions}
        
        # Get similar users' interactions
        similar_user_ids = [u[0] for u in similar_users]
        similar_user_weights = dict(similar_users)
        
        result = await self.db.execute(
            select(UserContentInteraction)
            .where(UserContentInteraction.user_id.in_(similar_user_ids))
        )
        similar_users_interactions = result.scalars().all()
        
        # Calculate content scores
        content_scores = {}
        for interaction in similar_users_interactions:
            if interaction.content_id in user_content_ids:
                continue
                
            user_weight = similar_user_weights[interaction.user_id]
            interaction_weight = (
                self.interaction_weights.get(interaction.interaction_type, 1.0) *
                interaction.engagement_score
            )
            
            score = user_weight * interaction_weight
            
            if interaction.content_id not in content_scores:
                content_scores[interaction.content_id] = 0.0
            content_scores[interaction.content_id] += score
        
        # Create recommendations
        recommendations = []
        for content_id, score in content_scores.items():
            recommendations.append(
                RecommendationResponse(
                    content_id=content_id,
                    score=score,
                    recommendation_type=RecommendationType.COLLABORATIVE,
                    metadata={
                        "collaborative_score": score,
                        "recommendation_source": "collaborative"
                    }
                )
            )
        
        return recommendations 
    
    async def _hybrid_merge_recommendations(
        self,
        content_based_recs: List[RecommendationResponse],
        collaborative_recs: List[RecommendationResponse],
        limit: int = 10
    ) -> List[RecommendationResponse]:
        """
        Merge recommendations from different sources using a hybrid approach
        """
        # Create a map of content_id to recommendations
        merged_recs = {}
        
        # Process content-based recommendations
        for rec in content_based_recs:
            merged_recs[rec.content_id] = {
                "content_id": rec.content_id,
                "content_based_score": rec.score,
                "collaborative_score": 0.0,
                "metadata": rec.metadata
            }
        
        # Process collaborative recommendations
        for rec in collaborative_recs:
            if rec.content_id in merged_recs:
                merged_recs[rec.content_id]["collaborative_score"] = rec.score
                merged_recs[rec.content_id]["metadata"].update(rec.metadata)
            else:
                merged_recs[rec.content_id] = {
                    "content_id": rec.content_id,
                    "content_based_score": 0.0,
                    "collaborative_score": rec.score,
                    "metadata": rec.metadata
                }
        
        # Calculate hybrid scores
        recommendations = []
        for content_id, data in merged_recs.items():
            # Weighted average of scores
            content_based_weight = 0.6  # Give more weight to content-based
            collaborative_weight = 0.4
            
            hybrid_score = (
                data["content_based_score"] * content_based_weight +
                data["collaborative_score"] * collaborative_weight
            )
            
            # Create hybrid recommendation
            recommendations.append(
                RecommendationResponse(
                    content_id=content_id,
                    score=hybrid_score,
                    recommendation_type=RecommendationType.HYBRID,
                    metadata={
                        "hybrid_score": hybrid_score,
                        "content_based_score": data["content_based_score"],
                        "collaborative_score": data["collaborative_score"],
                        "recommendation_source": "hybrid",
                        **data["metadata"]
                    }
                )
            )
        
        # Sort by hybrid score and limit results
        recommendations.sort(key=lambda x: x.score, reverse=True)
        return recommendations[:limit] 