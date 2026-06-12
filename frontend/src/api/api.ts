const API_BASE = "http://localhost:8000";

export interface Listing {
    hash_id: string;
    title: string;
    total_price_eur: number;
    size_m2: string;
    neighbourhood: string;
    score: number;
    img_url: string;
    link: string
}

export interface SearchResponse {
    results: Listing[];
    total: number;
}

export interface ChatResponse {
    response: string;
    listings: Listing[];
}

export async function searchListings(query: string, topK: number = 10): Promise<SearchResponse> {
    console.log("Calling API...")
    const response = await fetch(`${API_BASE}/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, top_k: topK })
    });

    if (!response.ok) throw new Error("Search failed");

    return response.json();
}

export async function sendChatMessage(message: string, sessionId: string): Promise<ChatResponse> {
    const response = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message, session_id: sessionId })
    });

    if (!response.ok) throw new Error("Chat request failed");

    return response.json();
}
