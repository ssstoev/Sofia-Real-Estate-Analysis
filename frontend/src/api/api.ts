const API_BASE = "http://localhost:8000";

export interface Listing {
    hash_id: string;
    title: string;
    total_price_eur: number;
    size_m2: string;
    neighbourhood: string;
    score: number;
    img_url: string;
    link: string;
    nr_of_rooms: number
}

export interface SearchResponse {
    results: Listing[];
    total: number;
}

export interface ChatResponse {
    response: string;
    listings: Listing[];
}

export async function sendChatMessage(message: string, sessionId: string): Promise<ChatResponse> {
    console.log("Calling API...")
    const response = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message, session_id: sessionId })
    });

    if (!response.ok) throw new Error("Chat request failed");

    const data = await response.json();
    console.log("Chat API response:", data);
    return data;
}
