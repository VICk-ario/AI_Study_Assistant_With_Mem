"use client"; 

import { useState } from "react";

export default function ChatInterface({ userId }: { userId: string }) {
  const [message, setMessage] = useState("");
  const [chatHistory, setChatHistory] = useState<{ role: string, content: string }[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const sendMessage = async () => {
    if (!message.trim()) return;
    setIsLoading(true);

    // 1. Add your message to the screen immediately
    const userMessage = { role: "user", content: message };
    setChatHistory((prev) => [...prev, userMessage]);
    
    try {
      // 2. Send the message to your FastAPI backend
      const response = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
            message: message, 
            user_id: userId 
        }),
      });

      const data = await response.json();

      // 3. Add the AI's Socratic response to the screen
      setChatHistory((prev) => [...prev, { role: "assistant", content: data.reply }]);
    } catch (error) {
      console.error("Connection to FastAPI failed:", error);
      setChatHistory((prev) => [...prev, { role: "assistant", content: "I can't reach my brain right now. Is the backend running?" }]);
    } finally {
      setMessage("");
      setIsLoading(false);
    }
  };

  return (
    <div className="w-full max-w-2xl mt-8 flex flex-col gap-4">
      {/* Chat Display Area */}
      <div className="h-[400px] overflow-y-auto border rounded-xl bg-white p-4 shadow-inner flex flex-col gap-3">
        {chatHistory.length === 0 && (
          <p className="text-gray-400 text-center mt-20">Ask your tutor anything to begin...</p>
        )}
        {chatHistory.map((msg, i) => (
          <div 
            key={i} 
            className={`max-w-[80%] p-3 rounded-2xl ${
              msg.role === 'user' 
                ? 'bg-blue-600 text-white self-end rounded-tr-none' 
                : 'bg-gray-200 text-gray-800 self-start rounded-tl-none'
            }`}
          >
            <p className="text-sm">{msg.content}</p>
          </div>
        ))}
      </div>

      {/* Input Area */}
      <div className="flex gap-2">
        <input 
          className="flex-1 border-2 border-gray-200 p-3 rounded-xl focus:border-blue-500 outline-none transition-all" 
          value={message} 
          onChange={(e) => setMessage(e.target.value)}
          placeholder="How do I use a for-loop?"
          onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
        />
        <button 
          onClick={sendMessage} 
          disabled={isLoading}
          className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-xl font-bold disabled:opacity-50 transition-colors"
        >
          {isLoading ? "..." : "Send"}
        </button>
      </div>
    </div>
  );
}