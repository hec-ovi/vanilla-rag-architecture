import { useEffect } from 'react';
import { Database, Upload, MessageSquare } from 'lucide-react';
import { motion } from 'framer-motion';
import { ChatPanel, FileUpload, SettingsPanel, ThemeToggle } from './components/features';
import { Card, CardHeader, CardTitle } from './components/ui/Card';
import { useThemeStore } from './stores';

function App() {
  const { initTheme } = useThemeStore();

  useEffect(() => {
    initTheme();
  }, [initTheme]);

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Header */}
      <header className="border-b border-border bg-card sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-primary/10 rounded-lg">
              <Database className="h-6 w-6 text-primary" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-foreground">Vanilla RAG</h1>
              <p className="text-xs text-muted-foreground hidden sm:block">
                Local-first RAG with semantic reranking
              </p>
            </div>
          </div>
          
          <ThemeToggle />
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[calc(100vh-8rem)]">
          {/* Left Sidebar - Upload & Settings */}
          <div className="lg:col-span-1 space-y-6 overflow-y-auto scrollbar-thin">
            {/* Upload Section */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
            >
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Upload className="h-5 w-5" />
                    Upload Documents
                  </CardTitle>
                </CardHeader>
                <FileUpload />
              </Card>
            </motion.div>

            {/* Settings Section */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
            >
              <SettingsPanel />
            </motion.div>
          </div>

          {/* Right Panel - Chat */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="lg:col-span-2 h-full"
          >
            <Card className="h-full flex flex-col">
              <CardHeader className="border-b border-border">
                <CardTitle className="flex items-center gap-2">
                  <MessageSquare className="h-5 w-5" />
                  Chat
                </CardTitle>
              </CardHeader>
              <div className="flex-1 overflow-hidden">
                <ChatPanel />
              </div>
            </Card>
          </motion.div>
        </div>
      </main>
    </div>
  );
}

export default App;
