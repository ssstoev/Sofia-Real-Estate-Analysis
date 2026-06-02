import { useState, useRef, useEffect } from "react";
import { Send, Sparkles, Building2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import ListingCard from "./ListingCard";
import { Listing, sendChatMessage } from "@/api/api";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  listings?: Listing[];
}

const SUGGESTED_QUERIES = [
  "Покажи ми двустайни апартаменти под 2500eur/m2",
  "Намери ми тристайни до 300000EUR",
  "Намери ми двустаен до 180000EUR близо до метро",
  "Kаква е средната цена на двустайни апартаменти в София?",
];

const sampleListing: Listing = {
    hash_id: "string",
    title: "string",
    total_price_eur: 120000,
    size_m2: "string",
    neighbourhood: "string",
    score: 0.2,
    imgUrl: "https://www.imoti.net/web/files/obiavi/6217591/main_image/thumb_880x0_wm_4-1.jpg?ver=1776588194",
    link: "https://www.imoti.net/bg/obiava/prodava/sofia/ovcha-kupel/tristaen/6217591/?sid=it0yuZ&page=1"
}

const ChatInterface = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const sessionId = useRef<string>(crypto.randomUUID());

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async (text?: string) => {
    console.log("message sent")
    const messageText = text || input.trim();
    if (!messageText || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: messageText,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    // Call the chat API
    try {
      const data = await sendChatMessage(messageText, sessionId.current);
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: data.response,
        listings: data.listings?.length > 0 ? data.listings : undefined,
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      console.log("Error:", err)
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: "Sorry, something went wrong while searching. Please try again.",
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex h-screen flex-col bg-background">
      {/* Header */}
      <header className="flex items-center gap-3 border-b border-border px-6 py-4">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary">
          <Building2 className="h-5 w-5 text-primary-foreground" />
        </div>
        <div>
          <h1 className="text-lg font-semibold text-foreground">ImotQuery</h1>
          <p className="text-xs text-muted-foreground">
            AI-powered real estate search
          </p>
        </div>
      </header>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-6">
        <div className="mx-auto max-w-2xl space-y-6">
          {messages.length === 0 && (
            <div className="flex flex-col items-center py-16 text-center">
              <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-secondary">
                <Sparkles className="h-8 w-8 text-primary" />
              </div>
              <h2 className="mb-2 text-xl font-semibold text-foreground">
                Ask me about real estate
              </h2>
              <p className="mb-8 max-w-md text-sm text-muted-foreground">
                Search listings, compare prices, analyze neighborhoods, or paste
                a listing URL to get insights.
              </p>
              <div className="grid w-full max-w-lg grid-cols-1 gap-2 sm:grid-cols-2">
                {SUGGESTED_QUERIES.map((query) => (
                  <button
                    key={query}
                    onClick={() => handleSend(query)}
                    className="rounded-xl border border-border bg-card px-4 py-3 text-left text-sm text-foreground transition-colors hover:border-primary hover:bg-secondary"
                  >
                    {query}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[85%] space-y-3 ${
                  message.role === "user"
                    ? "rounded-2xl rounded-br-md bg-chat-user px-4 py-3 text-chat-user-foreground"
                    : ""
                }`}
              >
                <p className={`text-sm leading-relaxed ${message.role === "assistant" ? "text-foreground" : ""}`}>
                  {message.content.split("**").map((part, i) =>
                    i % 2 === 1 ? (
                      <strong key={i}>{part}</strong>
                    ) : (
                      <span key={i}>{part}</span>
                    )
                  )}
                </p>
                {message.listings && (
                  <div className="max-h-[60vh] overflow-y-auto space-y-2 pr-1">
                    {message.listings.map((listing) => (
                      <ListingCard key={listing.hash_id} listing={listing} />
                    ))}
                  </div>
                )}                 
                {/* <ListingCard key = {sampleListing.hash_id} listing={sampleListing}/> */}
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex justify-start">
              <div className="flex items-center gap-1.5 rounded-2xl bg-chat-assistant px-4 py-3">
                <div className="h-2 w-2 animate-pulse rounded-full bg-primary" />
                <div className="h-2 w-2 animate-pulse rounded-full bg-primary [animation-delay:150ms]" />
                <div className="h-2 w-2 animate-pulse rounded-full bg-primary [animation-delay:300ms]" />
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input */}
      <div className="border-t border-border px-4 py-4">
        <div className="mx-auto flex max-w-2xl items-end gap-2">
          <div className="flex-1 rounded-xl border border-border bg-card px-4 py-3 focus-within:border-primary focus-within:ring-1 focus-within:ring-primary">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about real estate listings..."
              rows={1}
              className="w-full resize-none bg-transparent text-sm text-foreground outline-none placeholder:text-muted-foreground"
            />
          </div>
          <Button
            onClick={() => handleSend()}
            disabled={!input.trim() || isLoading}
            size="icon"
            className="h-11 w-11 rounded-xl"
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;
