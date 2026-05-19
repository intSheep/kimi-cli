import {
  type ReactElement,
  memo,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";
import { cn } from "@/lib/utils";
import type { GitDiffStats } from "@/lib/api/models";
import type { TokenUsage } from "@/hooks/wireTypes";
import { useQueueStore } from "../../queue-store";
import { useToolEventsStore } from "@/features/tool/store";
import { useShallow } from "zustand/react/shallow";
import { ToolbarActivityIndicator, type ActivityDetail } from "../activity-status-indicator";
import { ToolbarQueuePanel, ToolbarQueueTab } from "./toolbar-queue";
import { ToolbarChangesPanel, ToolbarChangesTab } from "./toolbar-changes";
import { ToolbarTodoPanel, ToolbarTodoTab } from "./toolbar-todo";
import { ToolbarContextIndicator } from "./toolbar-context";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

// ─── Types ───────────────────────────────────────────────────

type TabId = "queue" | "changes" | "todo";

type PromptToolbarProps = {
  gitDiffStats?: GitDiffStats | null;
  isGitDiffLoading?: boolean;
  workDir?: string | null;
  planMode?: boolean;
  activityStatus?: ActivityDetail;
  usagePercent?: number;
  usedTokens?: number;
  maxTokens?: number;
  tokenUsage?: TokenUsage | null;
  tokensPerSecond?: number;
  mcpStatus?: {
    loading: boolean;
    connected: number;
    total: number;
    tools: number;
    servers: { name: string; status: string; error?: string | null }[];
  } | null;
  activityHint?: string;
  onSteer?: (text: string) => void;
  sessionId?: string;
};

// ─── Main toolbar ────────────────────────────────────────────

export const PromptToolbar = memo(function PromptToolbarComponent({
  gitDiffStats,
  isGitDiffLoading,
  workDir,
  planMode = false,
  activityStatus,
  usagePercent,
  usedTokens,
  maxTokens,
  tokenUsage,
  tokensPerSecond,
  mcpStatus,
  activityHint,
  onSteer,
  sessionId,
}: PromptToolbarProps): ReactElement | null {
  const queue = useQueueStore(
    useShallow((s) => (sessionId ? s.queues[sessionId] ?? [] : [])),
  );
  const todoItems = useToolEventsStore((s) => s.todoItems);
  const [activeTab, setActiveTab] = useState<TabId | null>(null);
  const prevQueueLenRef = useRef(0);

  const stats = gitDiffStats;
  const hasChanges = Boolean(stats?.isGitRepo && stats.hasChanges && stats.files && !stats.error);
  const hasQueue = queue.length > 0;
  const hasTodo = todoItems.length > 0;
  const hasContext = usagePercent !== undefined && usedTokens !== undefined && maxTokens !== undefined;
  const hasTabs = hasQueue || hasChanges || hasTodo;

  // Auto-open queue tab when first item is added
  useEffect(() => {
    if (prevQueueLenRef.current === 0 && queue.length > 0) {
      setActiveTab("queue");
    }
    prevQueueLenRef.current = queue.length;
  }, [queue.length]);

  // Auto-close tab when its data becomes empty
  useEffect(() => {
    if (activeTab === "queue" && !hasQueue) setActiveTab(null);
    if (activeTab === "changes" && !hasChanges) setActiveTab(null);
    if (activeTab === "todo" && !hasTodo) setActiveTab(null);
  }, [activeTab, hasQueue, hasChanges, hasTodo]);

  const toggleTab = useCallback((tab: TabId) => {
    setActiveTab((prev) => (prev === tab ? null : tab));
  }, []);

  if (!(hasTabs || activityStatus || hasContext || planMode)) return null;

  return (
    <div className={cn("w-full px-1 sm:px-2 flex flex-col gap-1 mb-2", isGitDiffLoading && "opacity-70")}>
      {/* ── Expanded panel ── */}
      {activeTab && (
        <div className={cn(
          "rounded-md border border-border bg-background",
          activeTab !== "changes" && "max-h-32 overflow-y-auto py-1 px-0.5",
        )}>
          {activeTab === "queue" && <ToolbarQueuePanel queue={queue} sessionId={sessionId} onSteer={onSteer} />}
          {activeTab === "changes" && stats && (
            <ToolbarChangesPanel stats={stats} workDir={workDir} />
          )}
          {activeTab === "todo" && (
            <ToolbarTodoPanel items={todoItems} />
          )}
        </div>
      )}

      {/* ── Tab bar ── */}
      <div className="flex items-center px-1">
        {/* Left: activity / mcp / tok/s / tabs */}
        <div className="flex items-center gap-1.5 flex-1 justify-start">
          {activityStatus && (
            <ToolbarActivityIndicator activity={activityStatus} />
          )}

          {mcpStatus && mcpStatus.total > 0 && (
            <Tooltip>
              <TooltipTrigger asChild>
                <span
                  className={cn(
                    "flex items-center gap-1 h-7 px-2.5 rounded-full text-xs font-medium border border-border/60 bg-transparent select-none cursor-help",
                    mcpStatus.loading ? "text-primary" : "text-muted-foreground",
                  )}
                >
                  mcp {mcpStatus.connected}/{mcpStatus.total}
                </span>
              </TooltipTrigger>
              <TooltipContent side="top" className="max-w-xs">
                <div className="space-y-1">
                  {mcpStatus.servers.map((s) => (
                    <div key={s.name} className="flex items-center gap-2 text-xs">
                      <span
                        className={cn(
                          "size-1.5 rounded-full shrink-0",
                          s.status === "connected" && "bg-success",
                          s.status === "connecting" && "bg-warning animate-pulse",
                          s.status === "failed" && "bg-destructive",
                          s.status === "unauthorized" && "bg-muted-foreground",
                          s.status === "pending" && "bg-muted-foreground/50",
                        )}
                      />
                      <span className="font-medium">{s.name}</span>
                      <span className="text-muted-foreground capitalize">{s.status}</span>
                      {s.error && (
                        <span className="text-destructive truncate max-w-[120px]" title={s.error}>
                          {s.error}
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              </TooltipContent>
            </Tooltip>
          )}

          {tokensPerSecond && tokensPerSecond > 0 && (
            <span className="flex items-center gap-1 h-7 px-2.5 rounded-full text-xs font-medium border border-border/60 bg-transparent text-muted-foreground select-none">
              {tokensPerSecond} tok/s
            </span>
          )}

          {hasQueue && (
            <ToolbarQueueTab
              count={queue.length}
              isActive={activeTab === "queue"}
              onToggle={() => toggleTab("queue")}
            />
          )}

          {hasChanges && stats?.files && (
            <ToolbarChangesTab
              stats={stats}
              isActive={activeTab === "changes"}
              onToggle={() => toggleTab("changes")}
            />
          )}

          {hasTodo && (
            <ToolbarTodoTab
              items={todoItems}
              isActive={activeTab === "todo"}
              onToggle={() => toggleTab("todo")}
            />
          )}
        </div>

        {/* Center: activity hint with flowing light */}
        <div className="flex items-center justify-center flex-shrink-0">
          {activityHint && (
            <div className="relative flex items-center justify-center">
              {/* Outer glow — blurred ambient halo with breathe */}
              <div
                className="absolute rounded-full pointer-events-none"
                style={{
                  inset: "-3px",
                  padding: "2px",
                  background: "conic-gradient(from var(--activity-angle), transparent 0%, transparent 60%, rgba(140, 210, 220, 0.18) 75%, rgba(200, 245, 255, 0.35) 85%, rgba(140, 210, 220, 0.18) 95%, transparent 100%)",
                  WebkitMask: "linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0)",
                  WebkitMaskComposite: "xor",
                  maskComposite: "exclude",
                  filter: "blur(2px)",
                  animation: "activity-hint-spin 3.5s linear infinite, activity-hint-soft-breathe 4s ease-in-out infinite",
                }}
              />
              {/* Main stream — crisp flowing light */}
              <div
                className="absolute rounded-full pointer-events-none"
                style={{
                  inset: "-1.5px",
                  padding: "1.5px",
                  background: "conic-gradient(from var(--activity-angle), transparent 0%, transparent 65%, rgba(150, 220, 230, 0.45) 78%, rgba(210, 250, 255, 0.85) 88%, rgba(150, 220, 230, 0.45) 95%, transparent 100%)",
                  WebkitMask: "linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0)",
                  WebkitMaskComposite: "xor",
                  maskComposite: "exclude",
                  animation: "activity-hint-spin 3.5s linear infinite",
                }}
              />
              {/* Static border — whisper thin */}
              <div
                className="absolute rounded-full pointer-events-none"
                style={{
                  inset: "-0.5px",
                  border: "1px solid rgba(130, 210, 220, 0.12)",
                }}
              />
              <span className="relative flex items-center h-7 px-2.5 rounded-full text-xs font-medium bg-transparent text-muted-foreground select-none truncate">
                {activityHint}
              </span>
            </div>
          )}
        </div>

        {/* Right: context */}
        <div className="flex items-center gap-1.5 flex-1 justify-end">
          {hasContext && (
            <ToolbarContextIndicator
              usagePercent={usagePercent!}
              usedTokens={usedTokens!}
              maxTokens={maxTokens!}
              tokenUsage={tokenUsage ?? null}
            />
          )}
        </div>
      </div>
    </div>
  );
});
