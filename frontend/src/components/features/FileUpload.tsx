import { useCallback, useState } from 'react';
import { Upload, X, FileText, Image as ImageIcon, File } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '../ui/Button';
import { Card } from '../ui/Card';
import { StatusBadge } from '../ui/StatusBadge';
import { cn, formatFileSize } from '../../lib/utils';
import { useChatStore } from '../../stores';
import { ragService } from '../../services';

const ACCEPTED_TYPES = [
  '.txt', '.md', '.csv', '.json',
  '.pdf', '.docx',
  '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'
];

export function FileUpload() {
  const [isDragging, setIsDragging] = useState(false);
  const { uploads, addUpload, updateUpload, removeUpload } = useChatStore();

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    const files = Array.from(e.dataTransfer.files);
    files.forEach(processFile);
  }, []);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    files.forEach(processFile);
    e.target.value = ''; // Reset input
  }, []);

  const processFile = async (file: File) => {
    // Validate file type
    const extension = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!ACCEPTED_TYPES.includes(extension)) {
      addUpload({
        filename: file.name,
        progress: 0,
        status: 'error',
        error: `Unsupported file type: ${extension}`,
      });
      return;
    }

    // Add to uploads
    addUpload({
      filename: file.name,
      progress: 0,
      status: 'uploading',
    });

    try {
      // Upload file
      await ragService.ingest(file, (progress) => {
        updateUpload(file.name, { progress, status: progress < 100 ? 'uploading' : 'processing' });
      });

      // Mark complete
      updateUpload(file.name, { status: 'complete', progress: 100 });
      
      // Remove after delay
      setTimeout(() => removeUpload(file.name), 3000);
    } catch (error) {
      updateUpload(file.name, {
        status: 'error',
        error: error instanceof Error ? error.message : 'Upload failed',
      });
    }
  };

  const getFileIcon = (filename: string) => {
    const ext = filename.split('.').pop()?.toLowerCase();
    if (['png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'].includes(ext || '')) {
      return <ImageIcon className="h-5 w-5 text-blue-500" />;
    }
    if (['pdf', 'docx'].includes(ext || '')) {
      return <File className="h-5 w-5 text-red-500" />;
    }
    return <FileText className="h-5 w-5 text-gray-500" />;
  };

  return (
    <div className="space-y-4">
      {/* Drop Zone */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={cn(
          'relative border-2 border-dashed rounded-xl p-8 transition-all duration-200 text-center cursor-pointer',
          isDragging
            ? 'border-primary bg-primary/5 scale-[1.02]'
            : 'border-muted-foreground/20 hover:border-muted-foreground/40 hover:bg-muted/50'
        )}
      >
        <input
          type="file"
          multiple
          accept={ACCEPTED_TYPES.join(',')}
          onChange={handleFileSelect}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
        />
        
        <motion.div
          initial={false}
          animate={{ scale: isDragging ? 1.1 : 1 }}
          className="flex flex-col items-center gap-3"
        >
          <div className={cn(
            'p-4 rounded-full transition-colors',
            isDragging ? 'bg-primary/10' : 'bg-muted'
          )}>
            <Upload className={cn(
              'h-8 w-8',
              isDragging ? 'text-primary' : 'text-muted-foreground'
            )} />
          </div>
          
          <div>
            <p className="text-sm font-medium text-foreground">
              {isDragging ? 'Drop files here' : 'Drag & drop files here'}
            </p>
            <p className="text-xs text-muted-foreground mt-1">
              or click to browse
            </p>
          </div>
          
          <p className="text-xs text-muted-foreground">
            Supports: TXT, PDF, DOCX, PNG, JPG
          </p>
        </motion.div>
      </div>

      {/* Upload List */}
      <AnimatePresence>
        {uploads.length > 0 && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="space-y-2"
          >
            {uploads.map((upload) => (
              <motion.div
                key={upload.filename}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
              >
                <Card padding="sm" className="flex items-center gap-3">
                  {getFileIcon(upload.filename)}
                  
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-foreground truncate">
                      {upload.filename}
                    </p>
                    
                    {upload.status === 'uploading' && (
                      <div className="mt-1.5">
                        <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                          <motion.div
                            className="h-full bg-primary"
                            initial={{ width: 0 }}
                            animate={{ width: `${upload.progress}%` }}
                            transition={{ duration: 0.3 }}
                          />
                        </div>
                      </div>
                    )}
                    
                    {upload.error && (
                      <p className="text-xs text-destructive mt-1">{upload.error}</p>
                    )}
                  </div>
                  
                  <StatusBadge status={upload.status} />
                  
                  <button
                    onClick={() => removeUpload(upload.filename)}
                    className="p-1 hover:bg-muted rounded"
                  >
                    <X className="h-4 w-4 text-muted-foreground" />
                  </button>
                </Card>
              </motion.div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
