import { cn } from '../../lib/utils';

type Status = 'pending' | 'uploading' | 'processing' | 'complete' | 'error' | 'idle';

interface StatusBadgeProps {
  status: Status;
  text?: string;
  className?: string;
}

const statusConfig: Record<Status, { bg: string; text: string; label: string; dot?: string }> = {
  pending: { bg: 'bg-muted', text: 'text-muted-foreground', label: 'Pending' },
  uploading: { bg: 'bg-blue-500/10', text: 'text-blue-600 dark:text-blue-400', label: 'Uploading', dot: 'bg-blue-500' },
  processing: { bg: 'bg-yellow-500/10', text: 'text-yellow-600 dark:text-yellow-400', label: 'Processing', dot: 'bg-yellow-500' },
  complete: { bg: 'bg-green-500/10', text: 'text-green-600 dark:text-green-400', label: 'Complete' },
  error: { bg: 'bg-destructive/10', text: 'text-destructive', label: 'Error' },
  idle: { bg: 'bg-muted', text: 'text-muted-foreground', label: 'Idle' },
};

export function StatusBadge({ status, text, className }: StatusBadgeProps) {
  const config = statusConfig[status];

  return (
    <span className={cn(
      'inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium',
      config.bg,
      config.text,
      className
    )}>
      {config.dot && (
        <span className={cn('relative flex h-2 w-2', config.dot)}>
          <span className={cn('animate-ping absolute inline-flex h-full w-full rounded-full opacity-75', config.dot)} />
          <span className={cn('relative inline-flex rounded-full h-2 w-2', config.dot)} />
        </span>
      )}
      {text || config.label}
    </span>
  );
}
