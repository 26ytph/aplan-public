import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from src.core.retriever import Retriever
from src.api.v1.schemas import RecommendationRequest
import json

async def main():
    retriever = Retriever()
    query = "捷運公館站"
    req = RecommendationRequest(
        user_id="test",
        raw_intent=query,
        latitude=25.033,
        longitude=121.565
    )
    print(f"Query: {query}")
    results = await retriever.get_candidate_pois(req, limit=5)
    for i, r in enumerate(results):
         print(f"{i+1}. {r.get('name')} (Source: {r.get('source')}, Category: {r.get('category')})")

if __name__ == "__main__":
    asyncio.run(main())
