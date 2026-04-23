import { Activity, Shield, Zap } from "lucide-react";

interface HeaderProps {
  username?: string;
  onLogout?: () => void;
}

const Header = ({ username, onLogout }: HeaderProps) => {
  return (
    <header className="border-b border-border bg-card/50 backdrop-blur-sm sticky top-0 z-50">
      <div className="container flex items-center justify-between h-16 px-6">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-primary/15 border border-primary/30 flex items-center justify-center">
            <Shield className="w-5 h-5 text-primary" />
          </div>
          <div>
            <h1 className="text-lg font-semibold tracking-tight text-foreground">
              Neural<span className="text-gradient">News</span>
            </h1>
            <p className="text-[10px] font-mono text-muted-foreground tracking-widest uppercase">
              Multi-Agent Intelligence
            </p>
          </div>
        </div>

        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2 text-xs font-mono text-muted-foreground">
            <Activity className="w-3.5 h-3.5 text-success animate-pulse" />
            <span>5 agents active</span>
          </div>
          <div className="flex items-center gap-2 text-xs font-mono text-muted-foreground">
            <Zap className="w-3.5 h-3.5 text-warning" />
            <span>Real-time</span>
          </div>
          {username && (
            <div className="text-xs text-muted-foreground">
              Signed in as <span className="font-semibold text-foreground">{username}</span>
            </div>
          )}
          <button
            type="button"
            className="rounded-md border border-border bg-secondary px-3 py-1.5 text-xs font-medium text-foreground transition hover:border-primary/40 hover:text-primary"
            onClick={onLogout}
          >
            Logout
          </button>
        </div>
      </div>
    </header>
  );
};

export default Header;
