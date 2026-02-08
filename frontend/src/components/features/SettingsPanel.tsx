import { useState } from 'react';
import { Settings, Trash2, AlertCircle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '../ui/Button';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/Card';
import { StatusBadge } from '../ui/StatusBadge';
// import { Spinner } from '../ui/Spinner';
import { ragService } from '../../services';

export function SettingsPanel() {
  const [isResetting, setIsResetting] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [resetStatus, setResetStatus] = useState<'idle' | 'success' | 'error'>('idle');

  const handleReset = async () => {
    setIsResetting(true);
    setResetStatus('idle');

    try {
      await ragService.reset();
      setResetStatus('success');
      setTimeout(() => {
        setShowConfirm(false);
        setResetStatus('idle');
      }, 2000);
    } catch (error) {
      setResetStatus('error');
    } finally {
      setIsResetting(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Settings className="h-5 w-5" />
          Settings
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Reset Section */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <h4 className="text-sm font-medium text-foreground">Reset Knowledge Base</h4>
              <p className="text-xs text-muted-foreground">
                Delete all uploaded documents and embeddings
              </p>
            </div>

            <AnimatePresence mode="wait">
              {!showConfirm ? (
                <motion.div
                  key="reset-btn"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                >
                  <Button
                    variant="danger"
                    size="sm"
                    onClick={() => setShowConfirm(true)}
                  >
                    <Trash2 className="h-4 w-4 mr-1" />
                    Reset
                  </Button>
                </motion.div>
              ) : (
                <motion.div
                  key="confirm"
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.9 }}
                  className="flex items-center gap-2"
                >
                  {resetStatus === 'idle' && (
                    <>
                      <span className="text-xs text-muted-foreground">Are you sure?</span>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setShowConfirm(false)}
                        disabled={isResetting}
                      >
                        Cancel
                      </Button>
                      <Button
                        variant="danger"
                        size="sm"
                        onClick={handleReset}
                        isLoading={isResetting}
                      >
                        Yes, Reset
                      </Button>
                    </>
                  )}
                  {resetStatus === 'success' && (
                    <StatusBadge status="complete" text="Reset complete" />
                  )}
                  {resetStatus === 'error' && (
                    <div className="flex items-center gap-1 text-destructive text-xs">
                      <AlertCircle className="h-4 w-4" />
                      Reset failed
                    </div>
                  )}
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          <AnimatePresence>
            {showConfirm && resetStatus === 'idle' && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="p-3 bg-destructive/10 border border-destructive/20 rounded-lg"
              >
                <p className="text-sm text-destructive">
                  <AlertCircle className="h-4 w-4 inline mr-1" />
                  This will permanently delete all uploaded documents and cannot be undone.
                </p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Info Section */}
        <div className="pt-4 border-t border-border">
          <h4 className="text-sm font-medium text-foreground mb-2">About</h4>
          <div className="space-y-1 text-xs text-muted-foreground">
            <p>Vanilla RAG Architecture v0.1.0</p>
            <p>Local-first RAG with semantic reranking</p>
            <p>Embeddings: all-MiniLM-L6-v2</p>
            <p>Reranker: ms-marco-MiniLM-L-6-v2</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
