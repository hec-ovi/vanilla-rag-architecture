import { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, BookOpen, Trash2, MessageSquarePlus } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '../ui/Button';
import { Card } from '../ui/Card';
import { TextArea } from '../ui/TextArea';
import { Spinner } from '../ui/Spinner';
import { cn, formatTime } from '../../lib/utils';
import { useChatStore } from '../../stores';
import { ragService } from '../../services';
import type { ChatMessage, Source } from '../../types';

export function ChatPanel() {
  const [input, setInput] = useState('');
  const [conversationId, setConversationId] = useState<string | undefined>();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { messages, isLoading, addMessage, updateMessage, setLoading, clearMessages } = useChatStore();

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput('');

    // Add user message
    addMessage({
      role: 'user',
      content: userMessage,
    });

    // Add placeholder for assistant
    const assistantMsgId = addMessage({
      role: 'assistant',
      content: '',
      isStreaming: true,
    });
    const assistantId = assistantMsgId || '';
    if (!assistantId) return;

    setLoading(true);

    try {
      const response = await ragService.chat(userMessage, conversationId);
      
      // Save conversation ID for follow-up
      setConversationId(response.conversation_id);
      
      updateMessage(assistantId, {
        content: response.answer,
        sources: response.sources,
        isStreaming: false,
      });
    } catch (error) {
      updateMessage(assistantId, {
        content: error instanceof Error ? error.message : 'Sorry, something went wrong.',
        isStreaming: false,
      });
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleNewChat = () => {
    clearMessages();
    setConversationId(undefined);
  };

  return (
    <div className="flex flex-col h-full">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto scrollbar-thin p-4 space-y-4">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center text-muted-foreground">
            <Bot className="h-12 w-12 mb-4 opacity-50" />
            <h3 className="text-lg font-medium text-foreground mb-2">
              Welcome to Vanilla RAG
            </h3>
            <p className="max-w-sm">
              Upload documents and ask questions. I remember our conversation!
            </p>
            {conversationId && (
              <p className="mt-2 text-xs text-muted-foreground">
                Conversation ID: {conversationId.slice(0, 8)}...
              </p>
            )}
          </div>
        )}

        <AnimatePresence initial={false}>
          {messages.map((message) => (
            <Message key={message.id} message={message} />
          ))}
        </AnimatePresence>

        {isLoading && !messages.some(m => m.isStreaming) && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex items-center gap-2 text-muted-foreground"
          >
            <Spinner size="sm" />
            <span className="text-sm">Thinking...</span>
          </motion.div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 border-t border-border bg-card">
        {conversationId && (
          <div className="flex items-center gap-2 mb-2 px-1">
            <span className="text-xs text-muted-foreground">
              Conversation: {conversationId.slice(0, 8)}...
            </span>
          </div>
        )}
        
        <div className="flex gap-2">
          <TextArea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question about your documents..."
            className="min-h-[60px] resize-none"
            disabled={isLoading}
          />
          <div className="flex flex-col gap-2">
            <Button
              onClick={handleSend}
              disabled={!input.trim() || isLoading}
              className="h-[60px] px-4"
            >
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Actions */}
        <div className="flex justify-between items-center mt-3">
          <p className="text-xs text-muted-foreground">
            Press Enter to send, Shift+Enter for new line
          </p>
          
          <div className="flex gap-2">
            {messages.length > 0 && (
              <>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleNewChat}
                  className="text-muted-foreground"
                >
                  <MessageSquarePlus className="h-4 w-4 mr-1" />
                  New chat
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={clearMessages}
                  className="text-muted-foreground hover:text-destructive"
                >
                  <Trash2 className="h-4 w-4 mr-1" />
                  Clear
                </Button>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

interface MessageProps {
  message: ChatMessage;
}

function Message({ message }: MessageProps) {
  const isUser = message.role === 'user';
  const [showSources, setShowSources] = useState(false);

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
        'flex gap-3',
        isUser ? 'flex-row-reverse' : 'flex-row'
      )}
    >
      {/* Avatar */}
      <div className={cn(
        'flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center',
        isUser ? 'bg-primary text-primary-foreground' : 'bg-muted'
      )}>
        {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
      </div>

      {/* Content */}
      <div className={cn(
        'flex flex-col max-w-[80%]',
        isUser ? 'items-end' : 'items-start'
      )}>
        <Card
          padding="md"
          className={cn(
            isUser && 'bg-primary text-primary-foreground'
          )}
        >
          <div className="whitespace-pre-wrap">{message.content}</div>
          
          {message.isStreaming && (
            <span className="inline-block w-2 h-4 bg-current animate-pulse ml-1" />
          )}
        </Card>

        {/* Sources */}
        {!isUser && message.sources && message.sources.length > 0 && (
          <div className="mt-2">
            <button
              onClick={() => setShowSources(!showSources)}
              className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
            >
              <BookOpen className="h-3 w-3" />
              {message.sources.length} source{message.sources.length > 1 ? 's' : ''}
            </button>

            <AnimatePresence>
              {showSources && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="mt-2 space-y-2 overflow-hidden"
                >
                  {message.sources.map((source) => (
                    <SourceCard key={source.chunk_id} source={source} />
                  ))}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        )}

        {/* Timestamp */}
        <span className="text-xs text-muted-foreground mt-1">
          {formatTime(message.timestamp)}
        </span>
      </div>
    </motion.div>
  );
}

interface SourceCardProps {
  source: Source;
}

function SourceCard({ source }: SourceCardProps) {
  return (
    <Card padding="sm" className="text-xs border-l-4 border-l-primary">
      <div className="flex items-center gap-2 text-muted-foreground mb-1">
        <span className="font-medium">{source.filename}</span>
        <span>•</span>
        <span>Score: {(source.score * 100).toFixed(1)}%</span>
      </div>
      <p className="text-foreground line-clamp-3">{source.content}</p>
    </Card>
  );
}
