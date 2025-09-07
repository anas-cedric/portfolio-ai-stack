'use client';

import { useState, useRef, useEffect, FormEvent } from 'react';
import axios from 'axios'; 
import { Message, PortfolioData, UserProfile, PortfolioResponse, BackendChatMessage } from '@/lib/types'; 
import { Button } from '@/components/ui/button';
import { ArrowRight } from 'lucide-react';

interface ChatInterfaceProps {
  portfolioData?: PortfolioData; 
  userPreferences?: UserProfile; 
  apiKey?: string;
  apiUrl?: string;
  onChatError?: (message: string) => void;
  onApprove?: () => void; 
  onPortfolioUpdate?: (updatedPortfolioResponse: PortfolioResponse) => void;
}

export default function ChatInterface({
  portfolioData, 
  userPreferences, 
  apiKey = process.env.NEXT_PUBLIC_API_KEY || 'test_api_key_for_development',
  // If NEXT_PUBLIC_API_URL is defined (even if it's an empty string) use it.
  // Otherwise (undefined) fall back to localhost when running locally (development).
  apiUrl =
    process.env.NEXT_PUBLIC_API_URL !== undefined
      ? process.env.NEXT_PUBLIC_API_URL
      : process.env.NODE_ENV === 'development'
        ? 'http://localhost:8000'
        : '',
  onChatError,
  onApprove,
  onPortfolioUpdate
}: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([]); 
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false); 
  const [isUpdatingPortfolio, setIsUpdatingPortfolio] = useState(false);
  const [localPortfolioData, setLocalPortfolioData] = useState<PortfolioData | undefined>(portfolioData);
  const [localUserPreferences, setLocalUserPreferences] = useState<UserProfile | undefined>(userPreferences);
  const [conversationId, setConversationId] = useState<string>('');
  const [suggestions, setSuggestions] = useState<string[]>([]); 
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setLocalPortfolioData(portfolioData);
    setLocalUserPreferences(userPreferences);
    if (portfolioData && messages.length === 0) {
        if (portfolioData) {
          const initialAssistantMsg = `Here’s your allocation. I’ll keep answers under 50 words. Ask for more if you want detail.`;
          setMessages([
            {
              content: initialAssistantMsg,
              role: 'assistant'
            }
          ]);
        }
    }
  }, [portfolioData, userPreferences]);

  useEffect(() => {
    // Scroll to the bottom when new messages are added
    if (messages.length > 1) {
      // Find the parent scrollable container
      const scrollableContainer = document.querySelector('.overflow-y-auto');
      if (scrollableContainer) {
        setTimeout(() => {
          scrollableContainer.scrollTo({ 
            top: scrollableContainer.scrollHeight, 
            behavior: 'smooth' 
          });
        }, 100);
      }
    }
  }, [messages]);


  const limitWords = (text: string, maxWords = 50) => {
    const words = text.trim().split(/\s+/);
    if (words.length <= maxWords) return text.trim();
    return words.slice(0, maxWords).join(' ') + '… If you want more detail, ask me to expand.';
  };

  const handleSubmit = async (e: FormEvent, suggestionText?: string) => {
    e.preventDefault();
    
    const messageContent = suggestionText || input;
    if (!messageContent.trim() || isLoading) return;
    
    const newUserMessage: Message = {
      content: messageContent,
      role: 'user'
    };
    
    setMessages(prev => [...prev, newUserMessage]);
    setInput('');
    setSuggestions([]);
    setIsLoading(true);
    
    try {
      const response = await axios.post(`/api/portfolio-chat`, {
        conversation_id: conversationId,
        user_message: messageContent,
        conversation_history: messages.map(m => ({ role: m.role, content: m.content })),
        metadata: {
          conversation_state: 'complete',
          updated_portfolio: portfolioData,
          system_instructions: `You are a professional wealth assistant. Keep each response under 50 words. Avoid long paragraphs. Use short sentences. If the user wants more, ask if they would like to expand. Provide educational context, not individualized advice. Focus on allocation rationale and simple explanations.`
        }
      }, {
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': apiKey
        }
      });
      
      const data = response.data;
      
      if (data.conversation_id && data.conversation_id !== conversationId) {
        setConversationId(data.conversation_id);
      }
      
      const newHistory = data.conversation_history || [];
      if (newHistory.length > 0) {
        setMessages(newHistory.map((m: any) => ({ content: limitWords(m.content), role: m.role })));
      } else {
        const assistantContentRaw = typeof data.response === 'string' ? data.response : JSON.stringify(data.response);
        const assistantContent = limitWords(assistantContentRaw);
        const newAssistantMessage: Message = {
          content: assistantContent,
          role: 'assistant'
        };
        setMessages(prev => [...prev, newAssistantMessage]);
      }
      
      if (data.updated_portfolio) {
        setLocalPortfolioData(data.updated_portfolio);
        // Propagate the updated portfolio to the parent so the chart & asset list stay in sync
        onPortfolioUpdate?.(data as unknown as PortfolioResponse);
      }
      
    } catch (error: any) {
      console.error('Error sending message:', error);
      
      let displayError = "Sorry, I encountered an error. Please try again."; 

      const errorData = error.response?.data;
      if (errorData && Array.isArray(errorData.detail) && errorData.detail.length > 0 && errorData.detail[0].msg) {
        displayError = `Error: ${errorData.detail[0].msg}`;
      } else if (typeof errorData?.detail === 'string') {
        displayError = errorData.detail;
      }

      const errorMessage: Message = {
        content: displayError, 
        role: 'assistant'
      };
      setMessages(prev => [...prev, errorMessage]);
      onChatError?.(errorMessage.content); 
    } finally {
      setIsLoading(false);
    }
  };

  const handlePortfolioUpdate = async () => {
    if (!localPortfolioData || !localUserPreferences || messages.length === 0) { 
      console.error("Cannot update portfolio without portfolio data, user preferences, or chat history.");
      onChatError?.("Missing data needed to update portfolio.");
      return;
    }

    setIsUpdatingPortfolio(true);
    onChatError?.(''); 

    try {
      const backendChatHistory: BackendChatMessage[] = messages.map(msg => ({
          role: msg.role,
          content: msg.content
        }));

      // Construct the nested payload expected by the backend
      const currentPortfolioNested: PortfolioResponse = {
        portfolioData: localPortfolioData,
        userPreferences: localUserPreferences,
      };

      const payload = {
        current_portfolio: currentPortfolioNested, // Send the nested structure
        chat_history: backendChatHistory,
        system_instructions: `You are a professional wealth manager having a conversation with your client. 
          
Key guidelines:
- Respond in a warm, professional, and conversational tone
- Write in complete paragraphs, not bullet points or lists
- Focus on percentage allocations, not dollar amounts
- Explain investment concepts in accessible terms
- Show empathy and understanding of the client's financial goals
- Be confident in your recommendations while remaining open to adjustments
- Discuss risk, diversification, and long-term strategy
- Avoid technical jargon unless explaining it clearly
- Always maintain a human, personalized approach

Remember: You're their trusted financial advisor, not a chatbot.`
      };

      // Log the payload being sent for debugging
      console.log('Sending update payload:', JSON.stringify(payload, null, 2));

      const response = await axios.post<PortfolioResponse> 
        (`/api/update-portfolio-from-chat`, payload, {
          headers: {
            'x-api-key': apiKey,
            'Content-Type': 'application/json',
          },
      });

      onPortfolioUpdate?.(response.data); 
        
    } catch (err: any) {
      console.error("Error updating portfolio:", err);
      const errorMessage = err.response?.data?.detail || err.message || "An unknown error occurred while updating the portfolio.";
      onChatError?.(errorMessage);
    } finally {
      setIsUpdatingPortfolio(false);
    }
  };

  // Add messages to the scrollable container when they exist
  useEffect(() => {
    if (messages.length > 1) {
      const scrollContainer = document.querySelector('.overflow-y-auto');
      if (scrollContainer) {
        const existingMessages = scrollContainer.querySelector('.chat-messages-container');
        if (existingMessages) {
          existingMessages.remove();
        }
        
        // Create messages container
        const messagesDiv = document.createElement('div');
        messagesDiv.className = 'chat-messages-container mt-8 space-y-4 max-w-[744px] mx-auto';
        
        messages.slice(1).forEach((message) => {
          const messageDiv = document.createElement('div');
          messageDiv.className = `flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`;
          
          const contentDiv = document.createElement('div');
          contentDiv.className = `max-w-[75%] rounded-2xl px-4 py-3 ${
            message.role === 'user' 
              ? 'bg-[#00121F]/5 text-[#00121F]' 
              : 'text-[#00121F]'
          } fade-in`;
          contentDiv.textContent = message.content;
          
          messageDiv.appendChild(contentDiv);
          messagesDiv.appendChild(messageDiv);
        });
        
        // Add loading indicator if needed
        if (isLoading) {
          const loadingDiv = document.createElement('div');
          loadingDiv.className = 'flex justify-start';
          loadingDiv.innerHTML = '<div class="text-sm text-[#00121F]/50">Thinking...</div>';
          messagesDiv.appendChild(loadingDiv);
        }
        
        // Add to the main content area after the analysis section
        const mainContent = scrollContainer.querySelector('.max-w-\\[744px\\]');
        if (mainContent) {
          mainContent.appendChild(messagesDiv);
        }
        
        // Scroll to bottom
        setTimeout(() => {
          scrollContainer.scrollTop = scrollContainer.scrollHeight;
        }, 100);
      }
    }
  }, [messages, isLoading]);

  return (
    <div className="relative w-full">
      {/* Chat input */}
      <div>
        <form
          onSubmit={handleSubmit}
          className="flex items-center bg-white/80 backdrop-blur-[24px] border border-white/20 rounded-full shadow-[0_4px_24px_rgba(0,0,0,0.06)] transition-all duration-200 hover:shadow-[0_4px_32px_rgba(0,0,0,0.08)]"
        >
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about your portfolio"
            disabled={isLoading}
            className="flex-1 bg-transparent outline-none text-[16px] leading-[24px] text-[#00121F] placeholder:text-[#00121F]/40 px-6 py-4"
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="mr-2 w-10 h-10 rounded-full bg-[#096EA0] hover:bg-[#075a85] flex items-center justify-center transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M5 12H19" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M15 8L19 12L15 16" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </button>
        </form>
      </div>
    </div>
  );
}