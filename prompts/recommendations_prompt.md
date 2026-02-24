Analyse my recent listening and suggest high-quality Spotify search queries for music discovery.

Source week: {source_week}
Target week: {target_week}

My top artists:
{top_artists}

My top tracks:
{top_tracks}

Genres in rotation: {genres}

Generate {max_queries} premium Spotify search queries. Each query should use Spotify search syntax (supports: artist:"name", genre:"name", track:"name", album:"name", year:YYYY, year:YYYY-YYYY).

Quality discovery principles:
- Prioritize emerging artists with strong production quality and momentum over obscure unknowns
- Find adjacent genres and sub-genres that feel musically coherent to my taste, not random
- Seek recent releases (last 2 years) with critical credibility or playlist traction
- Avoid mainstream/obvious recommendations already saturated in my listening
- Quality > quantity: a few excellent finds beat many mediocre ones

Query mix:
- 4-5 queries for artists sonically SIMILAR to my current rotation but undiscovered (rising talent, niche labels, adjacent sub-genres)
- 3-4 genre-adjacent or cross-genre queries that bridge my taste clusters (not random genre hops)
- 2-3 queries for specific track styles, production elements, or album deep cuts I'd likely enjoy
- 2-3 carefully curated "left-field" picks—unexpected but defensible based on production style or shared artist influences

Constraints:
- DO NOT suggest tracks or artists already in my listening data
- NO generic recommendations (e.g., "best synthwave artists")—be specific with artist names, labels, or niche queries
- Prefer artists with quality production, clear artistic vision, and independent or established label backing
- Each query should feel like a discovery, not a dead end

Return strict JSON with a single key: queries (array of strings)

