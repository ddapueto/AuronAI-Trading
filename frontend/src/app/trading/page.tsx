"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Loader2, X } from "lucide-react";
import {
  useAccount,
  usePositions,
  useOrders,
  useBuy,
  useSell,
  useClosePosition,
  useTradeHistory,
} from "@/hooks/use-api";
import { cn } from "@/lib/utils";
import { KillSwitchButton } from "@/components/trading/kill-switch-button";

export default function TradingPage() {
  const account = useAccount();
  const positions = usePositions();
  const orders = useOrders();
  const tradeHistory = useTradeHistory();
  const buyMut = useBuy();
  const sellMut = useSell();
  const closeMut = useClosePosition();

  const [symbol, setSymbol] = useState("");
  const [quantity, setQuantity] = useState("");
  const [side, setSide] = useState<"buy" | "sell">("buy");

  const acc = account.data;
  const pos = positions.data ?? [];
  const ords = orders.data ?? [];
  const history = tradeHistory.data ?? [];

  function submitOrder() {
    const sym = symbol.trim().toUpperCase();
    const qty = Number(quantity);
    if (!sym || !qty || qty <= 0) return;

    if (side === "buy") {
      buyMut.mutate({ symbol: sym, quantity: qty });
    } else {
      sellMut.mutate({ symbol: sym, quantity: qty });
    }
  }

  const isPending = buyMut.isPending || sellMut.isPending;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Paper Trading</h1>

      <div className="grid gap-6 lg:grid-cols-5">
        {/* Left column — kill switch + account + order form */}
        <div className="space-y-4 lg:col-span-2">
          {/* Kill Switch */}
          <KillSwitchButton />

          {/* Account card */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Account</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <AccountRow label="Cash" value={acc ? `$${acc.cash.toFixed(2)}` : "—"} />
              <AccountRow label="Equity" value={acc ? `$${acc.equity.toFixed(2)}` : "—"} />
              <AccountRow label="Buying Power" value={acc ? `$${acc.buying_power.toFixed(2)}` : "—"} />
            </CardContent>
          </Card>

          {/* Order form */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">New Order</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <Tabs value={side} onValueChange={(v) => setSide(v as "buy" | "sell")}>
                <TabsList className="w-full">
                  <TabsTrigger value="buy" className="flex-1">
                    Buy
                  </TabsTrigger>
                  <TabsTrigger value="sell" className="flex-1">
                    Sell
                  </TabsTrigger>
                </TabsList>
              </Tabs>

              <div className="space-y-2">
                <Label htmlFor="symbol">Symbol</Label>
                <Input
                  id="symbol"
                  placeholder="AAPL"
                  value={symbol}
                  onChange={(e) => setSymbol(e.target.value)}
                  className="uppercase"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="qty">Quantity</Label>
                <Input
                  id="qty"
                  type="number"
                  placeholder="10"
                  min={0.01}
                  step={0.01}
                  value={quantity}
                  onChange={(e) => setQuantity(e.target.value)}
                />
              </div>

              <Button
                onClick={submitOrder}
                disabled={isPending || !symbol || !quantity}
                className={cn(
                  "w-full",
                  side === "buy"
                    ? "bg-emerald-600 hover:bg-emerald-700"
                    : "bg-red-600 hover:bg-red-700"
                )}
              >
                {isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                {side === "buy" ? "Buy" : "Sell"} {symbol.toUpperCase() || "..."}
              </Button>

              {(buyMut.error || sellMut.error) && (
                <p className="text-xs text-destructive">
                  {String(buyMut.error ?? sellMut.error)}
                </p>
              )}
              {(buyMut.data || sellMut.data) && (
                <p className="text-xs text-emerald-500">
                  Order {(buyMut.data ?? sellMut.data)?.status} — {(buyMut.data ?? sellMut.data)?.filled_quantity} @ ${(buyMut.data ?? sellMut.data)?.filled_avg_price.toFixed(2)}
                </p>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Right column — positions + orders + trade history */}
        <div className="space-y-4 lg:col-span-3">
          <Card>
            <Tabs defaultValue="positions">
              <CardHeader className="pb-0">
                <TabsList>
                  <TabsTrigger value="positions">Positions ({pos.length})</TabsTrigger>
                  <TabsTrigger value="orders">Open Orders ({ords.length})</TabsTrigger>
                  <TabsTrigger value="history">Trade History ({history.length})</TabsTrigger>
                </TabsList>
              </CardHeader>
              <CardContent className="pt-4">
                <TabsContent value="positions" className="mt-0">
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
                          <TableHead />
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {pos.map((p) => (
                          <TableRow key={p.symbol}>
                            <TableCell className="font-medium">{p.symbol}</TableCell>
                            <TableCell className="text-right">{p.quantity}</TableCell>
                            <TableCell className="text-right font-mono">
                              ${p.entry_price.toFixed(2)}
                            </TableCell>
                            <TableCell className="text-right font-mono">
                              ${p.current_price.toFixed(2)}
                            </TableCell>
                            <TableCell
                              className={cn(
                                "text-right font-mono font-medium",
                                p.unrealized_pnl >= 0 ? "text-emerald-500" : "text-red-500"
                              )}
                            >
                              ${p.unrealized_pnl.toFixed(2)} ({(p.unrealized_pnl_pct * 100).toFixed(1)}%)
                            </TableCell>
                            <TableCell>
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => closeMut.mutate(p.symbol)}
                                disabled={closeMut.isPending}
                              >
                                <X className="h-3.5 w-3.5" />
                              </Button>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  )}
                </TabsContent>

                <TabsContent value="orders" className="mt-0">
                  {ords.length === 0 ? (
                    <p className="text-sm text-muted-foreground">No open orders.</p>
                  ) : (
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>ID</TableHead>
                          <TableHead>Symbol</TableHead>
                          <TableHead>Side</TableHead>
                          <TableHead className="text-right">Qty</TableHead>
                          <TableHead>Status</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {ords.map((o) => (
                          <TableRow key={o.order_id}>
                            <TableCell className="font-mono text-xs">{o.order_id}</TableCell>
                            <TableCell>{o.symbol}</TableCell>
                            <TableCell className="capitalize">{o.side}</TableCell>
                            <TableCell className="text-right">{o.quantity}</TableCell>
                            <TableCell className="capitalize">{o.status}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  )}
                </TabsContent>

                <TabsContent value="history" className="mt-0">
                  {history.length === 0 ? (
                    <p className="text-sm text-muted-foreground">No trade history yet.</p>
                  ) : (
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Symbol</TableHead>
                          <TableHead>Side</TableHead>
                          <TableHead className="text-right">Qty</TableHead>
                          <TableHead className="text-right">Price</TableHead>
                          <TableHead>Date</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {history.map((o) => (
                          <TableRow key={o.order_id}>
                            <TableCell className="font-medium">{o.symbol}</TableCell>
                            <TableCell className="capitalize">{o.side}</TableCell>
                            <TableCell className="text-right">{o.filled_quantity}</TableCell>
                            <TableCell className="text-right font-mono">
                              ${o.filled_avg_price.toFixed(2)}
                            </TableCell>
                            <TableCell className="text-xs text-muted-foreground">
                              {new Date(o.updated_at).toLocaleString()}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  )}
                </TabsContent>
              </CardContent>
            </Tabs>
          </Card>
        </div>
      </div>
    </div>
  );
}

function AccountRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-mono">{value}</span>
    </div>
  );
}
