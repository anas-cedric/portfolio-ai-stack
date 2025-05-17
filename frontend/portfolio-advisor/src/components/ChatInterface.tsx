'use client';

import { useState, useRef, useEffect, FormEvent } from 'react';
import axios from 'axios'; 
import { Message, PortfolioData, UserProfile, PortfolioResponse, BackendChatMessage } from '@/lib/types'; 
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

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
          const initialAssistantMsg = 
            `Hi there! Based on your profile, I've designed this portfolio for you:

${formatPortfolioToString(portfolioData)}

Analysis: ${portfolioData.analysis || 'No analysis provided.'}

Feel free to ask any questions or request adjustments. If you're satisfied, you can approve the portfolio below.` ;
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
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const formatPercentage = (value: number) => {
    return `${value.toFixed(1)}%`; 
  };

  const formatPortfolioToString = (data: any): string => {
    if (!data || !data.allocations) return 'No portfolio data available.';
    
    let output = "Here's your recommended portfolio allocation:\n\n";
    output += Object.entries(data.allocations)
      .map(([assetClass, percentage]) => 
        `- ${assetClass.toUpperCase()}: ${formatPercentage(percentage as number)}`
      )
      .join('\n');
    
    return output;
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
      const response = await axios.post(`${apiUrl}/api/portfolio-chat`, {
        conversation_id: conversationId,
        user_message: messageContent,
        conversation_history: messages.map(m => ({ role: m.role, content: m.content })),
        metadata: {
          conversation_state: 'complete',
          updated_portfolio: portfolioData
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
        setMessages(newHistory.map((m: any, idx: number) => ({ content: m.content, role: m.role })));
      } else {
        const assistantContent = typeof data.response === 'string' ? data.response : JSON.stringify(data.response);
        const newAssistantMessage: Message = {
          content: assistantContent,
          role: 'assistant'
        };
        setMessages(prev => [...prev, newAssistantMessage]);
      }
      
      if (data.updated_portfolio) {
        setLocalPortfolioData(data.updated_portfolio);
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
      };

      // Log the payload being sent for debugging
      console.log('Sending update payload:', JSON.stringify(payload, null, 2));

      const response = await axios.post<PortfolioResponse> 
        (`${apiUrl}/api/update-portfolio-from-chat`, payload, {
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

  return (
    <div className="flex flex-col h-[600px] border border-gray-200 rounded-lg overflow-hidden bg-white shadow-md">
      <div className="flex-1 overflow-y-auto p-6 space-y-4 bg-gray-50">
        {messages.map((message, index) => (
          <div 
            key={index} 
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              // Change text-gray-800 to text-black for assistant messages
              className={`max-w-[75%] rounded-lg px-4 py-2 ${message.role === 'user' ? 'bg-blue-500 text-white' : 'bg-gray-200 text-black'}`}
            >
              <p className="text-sm whitespace-pre-wrap">{message.content}</p>
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="flex justify-start">
            <div className="max-w-[80%] rounded-lg px-4 py-3 bg-white border border-gray-300 text-gray-800 shadow-sm">
              <div className="flex space-x-1.5">
                <div className="w-2 h-2 rounded-full bg-gray-400 animate-bounce"></div>
                <div className="w-2 h-2 rounded-full bg-gray-400 animate-bounce" style={{ animationDelay: '0.15s' }}></div>
                <div className="w-2 h-2 rounded-full bg-gray-400 animate-bounce" style={{ animationDelay: '0.3s' }}></div>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      
      <div className="p-4 border-t border-gray-200 bg-white">
        {portfolioData && (
          <div className="flex flex-wrap gap-2 mb-3 justify-end">
            <Button 
              onClick={handlePortfolioUpdate} 
              size="sm" 
              variant="outline" 
              disabled={isUpdatingPortfolio || isLoading} 
              className="text-xs"
            >
              {isUpdatingPortfolio ? (
                <>
                  <div className="w-2 h-2 rounded-full bg-gray-400 animate-bounce mr-2"></div>
                  Updating...
                </>
              ) : (
                "Update Portfolio"
              )}
            </Button>
            {onApprove && (
              <Button 
                onClick={onApprove} 
                size="sm" 
                disabled={isUpdatingPortfolio || isLoading} 
                className="bg-green-600 hover:bg-green-700 text-white text-xs"
              >
                Approve Portfolio
              </Button>
            )}
          </div>
        )}
        <form onSubmit={handleSubmit} className="flex items-center gap-2">
          <Input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about your portfolio..."
            disabled={isLoading}
          />
          <Button type="submit" disabled={isLoading}>
            Send
          </Button>
        </form>
      </div>
    </div>
  );
}