# Hard SPARQL Queries for ChessKG RAG Testing

## 1. Multi-Player Head-to-Head Comparison
**Natural Language:** "Find all SuperGMs who have dominated each other in a chain. Show player names and their domination records."
**Complexity:** Multi-hop relationships, filtering by player type, aggregation

## 2. Opening Preference Analysis with Winning Rate
**Natural Language:** "For players with rating >= 2700, find their preferred opening as white and calculate their win percentage with that opening."
**Complexity:** Combining player ratings, opening preferences, game results aggregation

## 3. Federation Top Players with Head-to-Head Records
**Natural Language:** "Find the top 3 players by standard rating in India (IND federation). For each, find how many GMs they have beaten."
**Complexity:** Federation filtering, rating ranking, player type filtering, head-to-head stats

## 4. Distinctive Opening Specialists
**Natural Language:** "Find OpeningSpecialists who play completely different openings as white vs black (no common openings between their two preferences)."
**Complexity:** Set operations, filtering by player subclass, comparing two properties

## 5. Underdog Success Against Elite
**Natural Language:** "Find Underdog players and calculate their average rating when they beat SuperGMs. Show which SuperGMs they beat most often."
**Complexity:** Player subclass filtering, game result filtering, rating extraction, aggregation

## 6. Domination Chains
**Natural Language:** "Find a chain of players where A dominates B, B dominates C, and C dominates D. Show the complete chain."
**Complexity:** Graph traversal, path finding, multiple hops

## 7. DecisivePlayer vs EndgameSpecialist Matchups
**Natural Language:** "How many games have been played between DecisivePlayer types and EndgameSpecialist types? What's the win distribution?"
**Complexity:** Multiple player type filtering, game counting with results filtering

## 8. Opening Evolution by Rating
**Natural Language:** "For each opening, find the average rating of players who use it as white vs black. Which openings are preferred by higher-rated players?"
**Complexity:** GROUP BY opening, aggregation by color, rating analysis

## 9. Style Similarity Networks
**Natural Language:** "Find all players who have the exact same opening preferences (same white opening AND same black opening). Group them by opening pair."
**Complexity:** stylesSimilarTo relationship, grouping, multiple property matching

## 10. Rare Cross-Federation Dominance
**Natural Language:** "Find players from different federations where one strictly dominates the other. Show federation pairs and the rating difference."
**Complexity:** Federation comparison, dominance filtering, multi-federation queries

## 11. Title-Based Strength Progression
**Natural Language:** "For each FIDE title (GM, IM, FM), calculate the average standard rating and the average number of games played. Sort by average rating."
**Complexity:** GROUP BY title, aggregation, sorting, multiple statistics

## 12. Tournament Event Analysis
**Natural Language:** "Find events where SuperGMs and Underdogs both played. For each event, count how many games between them occurred and who won more."
**Complexity:** Event filtering, multiple player type filtering, result counting with GROUP BY

## Test Command Format:
```python
result = chain.invoke("YOUR_HARD_QUERY_HERE")
print(result["result"])
```

These queries test:
- ✅ UNION operations (combining white/black perspectives)
- ✅ Multiple FILTER conditions
- ✅ GROUP BY and aggregations (COUNT, AVG)
- ✅ rdf:type filtering (player subclasses)
- ✅ Property comparisons (ratings, game results)
- ✅ Relationship traversal (dominates, evenlyMatches, stylesSimilarTo)
- ✅ String matching (CONTAINS for federation, opening names)
- ✅ ORDER BY and LIMIT
- ✅ OPTIONAL clauses
- ✅ Complex pattern matching (chains, networks)
