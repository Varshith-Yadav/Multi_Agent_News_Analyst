import { type ReactNode } from "react";
import { BarChart3, Bot, Combine, Eye, Search, ShieldCheck } from "lucide-react";

interface AgentPanelProps {
  isAnalyzing?: boolean;
  hasReport?: boolean;
}

interface Agent {
  name: string;
  role: string;
  status: "active" | "processing" | "idle";
  icon: ReactNode;
  tasks: number;
}

const statusColor: Record<Agent["status"], string> = {
  active: "bg-success",
  processing: "bg-warning",
  idle: "bg-muted-foreground",
};

const buildAgents = (isAnalyzing: boolean, hasReport: boolean): Agent[] => [
  {
    name: "Collector",
    role: "Source Retrieval",
    status: isAnalyzing ? "processing" : hasReport ? "active" : "idle",
    icon: <Search className="h-4 w-4" />,
    tasks: isAnalyzing ? 1 : 0,
  },
  {
    name: "Summarizer",
    role: "Synthesis",
    status: isAnalyzing ? "processing" : hasReport ? "active" : "idle",
    icon: <Combine className="h-4 w-4" />,
    tasks: isAnalyzing ? 1 : 0,
  },
  {
    name: "Sentiment",
    role: "Tone Analysis",
    status: isAnalyzing ? "processing" : hasReport ? "active" : "idle",
    icon: <BarChart3 className="h-4 w-4" />,
    tasks: isAnalyzing ? 1 : 0,
  },
  {
    name: "Verifier",
    role: "Claim Checking",
    status: isAnalyzing ? "processing" : hasReport ? "active" : "idle",
    icon: <ShieldCheck className="h-4 w-4" />,
    tasks: isAnalyzing ? 1 : 0,
  },
  {
    name: "Trend Monitor",
    role: "Trend Extraction",
    status: isAnalyzing ? "processing" : hasReport ? "active" : "idle",
    icon: <Eye className="h-4 w-4" />,
    tasks: isAnalyzing ? 1 : 0,
  },
];

const AgentPanel = ({ isAnalyzing = false, hasReport = false }: AgentPanelProps) => {
  const agents = buildAgents(isAnalyzing, hasReport);
  const onlineCount = agents.filter((agent) => agent.status !== "idle").length;

  return (
    <div className="card-gradient space-y-4 rounded-lg border border-border p-4">
      <div className="flex items-center justify-between">
        <h2 className="flex items-center gap-2 text-sm font-semibold tracking-tight">
          <Bot className="h-4 w-4 text-primary" />
          Agent Network
        </h2>
        <span className="rounded-full bg-primary/10 px-2 py-0.5 text-[10px] text-primary">
          {onlineCount} ONLINE
        </span>
      </div>

      <div className="space-y-2">
        {agents.map((agent) => (
          <div
            key={agent.name}
            className="group flex items-center justify-between rounded-md border border-border/50 bg-background/50 p-3 transition-colors hover:border-primary/30"
          >
            <div className="flex items-center gap-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-md bg-secondary text-primary transition-colors group-hover:bg-primary/15">
                {agent.icon}
              </div>
              <div>
                <p className="text-sm font-medium text-foreground">{agent.name}</p>
                <p className="text-[11px] text-muted-foreground">{agent.role}</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-[11px] text-muted-foreground">{agent.tasks} tasks</span>
              <div
                className={`h-2 w-2 rounded-full ${statusColor[agent.status]} ${agent.status === "processing" ? "animate-pulse" : ""}`}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default AgentPanel;
