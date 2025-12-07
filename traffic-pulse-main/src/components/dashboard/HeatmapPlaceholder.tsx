import { Map } from 'lucide-react';

export function HeatmapPlaceholder() {
  return (
    <div className="bg-card border border-border rounded-xl p-5 h-full flex flex-col">
      <div className="flex items-center gap-2 mb-4">
        <div className="p-1.5 bg-primary/10 rounded-md">
          <Map className="h-4 w-4 text-primary" />
        </div>
        <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wider">
          Congestion Heatmap
        </h3>
      </div>
      
      <div className="flex-1 flex items-center justify-center min-h-[200px]">
        <div className="text-center">
          <div className="w-24 h-24 mx-auto mb-4 rounded-xl bg-gradient-to-br from-primary/20 via-warning/20 to-destructive/20 flex items-center justify-center">
            <Map className="h-10 w-10 text-muted-foreground" />
          </div>
          <p className="text-muted-foreground text-sm font-medium">
            Congestion Heatmap
          </p>
          <p className="text-xs text-muted-foreground/60 mt-1">
            Coming Soon
          </p>
        </div>
      </div>
    </div>
  );
}
