"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  DollarSign,
  Wallet,
  TrendingUp,
  Briefcase,
  Percent,
  BarChart3,
  PieChart,
  Hash,
} from "lucide-react";
import { useAccount, usePositions, useMetrics, useSignals } from "@/hooks/use-api";
import { cn } from "@/lib/utils";
import { KillSwitchButton } from "@/components/trading/kill-switch-button";
import { SignalBadge } from "@/components/analysis/signal-badge";

export default function DashboardPage() {
  const account = useAccount();
  const positions = usePositions();
  const metrics = useMetrics();
  const signals = useSignals(5);

  const acc = account.data;
  const pos = positions.data ?? [];
  const met = metrics.data;
  const sigs = signals.data;
  const totalPnl = pos.reduce((s, p) => s + p.unrealized_pnl, 0);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Dashboard</h1>

      {/* Primary metric cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          title="Equity"
          value={acc ? `$${acc.equity.toLocaleString("en-US", { minimumFractionDigits: 2 })}` : "—"}
          icon={<DollarSign className="h-4 w-4 text-muted-foreground" />}
        />
        <MetricCard
          title="Cash"
          value={acc ? `$${acc.cash.toLocaleString("en-US", { minimumFractionDigits: 2 })}` : "—"}
          icon={<Wallet className="h-4 w-4 text-muted-foreground" />}
        />
        <MetricCard
          title="Unrealized P&L"
          value={`$${totalPnl.toFixed(2)}`}
          className={totalPnl >= 0 ? "text-emerald-500" : "text-red-500"}
          icon={<TrendingUp className="h-4 w-4 text-muted-foreground" />}
        />
        <MetricCard
          title="Open Positions"
          value={String(pos.length)}
          icon={<Briefcase className="h-4 w-4 text-muted-foreground" />}
        />
      </div>

      {/* Secondary metric cards (from /api/metrics) */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          title="Win Rate"
          value={met?.win_rate != null ? `${(met.win_rate * 100).toFixed(1)}%` : "N/A"}
          icon={<Percent className="h-4 w-4 text-muted-foreground" />}
        />
        <MetricCard
          title="Profit Factor"
          value={met?.profit_factor != null ? met.profit_factor.toFixed(2) : "N/A"}
          icon={<BarChart3 className="h-4 w-4 text-muted-foreground" />}
        />
        <MetricCard
          title="Exposure"
          value={met ? `${(met.exposure * 100).toFixed(1)}%` : "—"}
          icon={<PieChart className="h-4 w-4 text-muted-foreground" />}
        />
        <MetricCard
          title="Total Trades"
          value={met ? String(met.total_trades) : "—"}
          icon={<Hash className="h-4 w-4 text-muted-foreground" />}
        />
      </div>

      {/* Positions table */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Open Positions</CardTitle>
        </CardHeader>
        <CardContent>
          {pos.length === 0 ? (
            <p className="text-sm text-muted-foreground">No open positions.</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Symbol</TableHead>
                  <TableHead className="text-right">Qty</TableHead>
                  <TableHead className="text-right">Entry</TableHead>
                  <TableHead className="text-right">Current</TableHead>
                  <TableHead className="text-right">P&L</TableHead>
                  <TableHead className="text-right">P&L %</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {pos.map((p) => (
                  <TableRow key={p.symbol}>
                    <TableCell className="font-medium">{p.symbol}</TableCell>
                    <TableCell className="text-right">{p.quantity}</TableCell>
                    <TableCell className="text-right">
                      ${p.entry_price.toFixed(2)}
                    </TableCell>
                    <TableCell className="text-right">
                      ${p.current_price.toFixed(2)}
                    </TableCell>
                    <TableCell
                      className={cn(
                        "text-right font-medium",
                        p.unrealized_pnl >= 0 ? "text-emerald-500" : "text-red-500"
                      )}
                    >
                      ${p.unrealized_pnl.toFixed(2)}
                    </TableCell>
                    <TableCell
                      className={cn(
                        "text-right",
                        p.unrealized_pnl_pct >= 0 ? "text-emerald-500" : "text-red-500"
                      )}
                    >
                      {(p.unrealized_pnl_pct * 100).toFixed(2)}%
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Bottom row */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {/* Active Signals */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Active Signals</CardTitle>
          </CardHeader>
          <CardContent>
            {!sigs || sigs.results.length === 0 ? (
              <p className="text-sm text-muted-foreground">No active signals.</p>
            ) : (
              <div className="space-y-3">
                {sigs.results.map((s) => (
                  <div key={s.symbol} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{s.symbol}</span>
                      <SignalBadge action={s.action as "BUY" | "SELL" | "HOLD"} />
                    </div>
                    <span className="text-sm text-muted-foreground">
                      {(s.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Broker Status */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Broker Status</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Broker</span>
              <Badge variant="secondary">{acc?.broker ?? "—"}</Badge>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Mode</span>
              <Badge variant="outline">{acc?.is_paper ? "Paper" : "Live"}</Badge>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Buying Power</span>
              <span className="font-mono">
                ${acc?.buying_power.toLocaleString("en-US", { minimumFractionDigits: 2 }) ?? "—"}
              </span>
            </div>
          </CardContent>
        </Card>

        {/* Quick Actions */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Quick Actions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <KillSwitchButton />
            <div className="text-sm text-muted-foreground space-y-1">
              <p>Use <strong>Analysis</strong> to analyze any symbol.</p>
              <p>Use <strong>Scanner</strong> to find trading signals.</p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function MetricCard({
  title,
  value,
  icon,
  className,
}: {
  title: string;
  value: string;
  icon: React.ReactNode;
  className?: string;
}) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {title}
        </CardTitle>
        {icon}
      </CardHeader>
      <CardContent>
        <p className={cn("text-2xl font-bold", className)}>{value}</p>
      </CardContent>
    </Card>
  );
}
