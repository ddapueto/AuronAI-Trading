"""
Script para ejecutar backtest de SwingMultiAssetV2 - Inter-Sector Rotation.

Fase 2: Expansión a sectores no-tech
- 10 acciones tech (baseline)
- 5 ETFs tech (Fase 1)
- 7 ETFs sectores no-tech + bonos (Fase 2)
- Total: 22 símbolos

Objetivo: Rotación inter-sectorial completa, reducir dependencia del Nasdaq
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

from auronai.backtesting.swing_multi_asset_v2 import SwingMultiAssetV2

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Ejecutar backtest de SwingMultiAssetV2."""
    
    # Universo expandido: 22 símbolos
    symbols = [
        # 10 acciones tech (baseline)
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META',
        'NVDA', 'TSLA', 'NFLX', 'AVGO', 'COST',
        
        # 5 ETFs tech (Fase 1)
        'SMH',   # VanEck Semiconductor ETF
        'XLK',   # Technology Select Sector SPDR
        'SOXX',  # iShares Semiconductor ETF
        'IGV',   # iShares Expanded Tech-Software ETF
        'HACK',  # ETFMG Prime Cyber Security ETF
        
        # 7 ETFs sectores no-tech + bonos (Fase 2 - NUEVO)
        'XLE',   # Energy Select Sector SPDR
        'XLF',   # Financial Select Sector SPDR
        'XLV',   # Health Care Select Sector SPDR
        'XLI',   # Industrial Select Sector SPDR
        'XLP',   # Consumer Staples Select Sector SPDR
        'XLU',   # Utilities Select Sector SPDR
        'TLT',   # iShares 20+ Year Treasury Bond ETF
    ]
    
    logger.info(f"Universo: {len(symbols)} símbolos")
    logger.info(f"  - 10 acciones tech")
    logger.info(f"  - 5 ETFs tech")
    logger.info(f"  - 6 ETFs sectores no-tech")
    logger.info(f"  - 1 ETF bonos (TLT)")
    
    # Configuración de estrategia (baseline)
    strategy = SwingMultiAssetV2(
        symbols=symbols,
        benchmark='QQQ',
        initial_capital=1000.0,
        base_risk_budget=0.20,        # 20% en mercado alcista
        defensive_risk_budget=0.05,   # 5% en mercado defensivo
        top_k=3,                       # Top 3 símbolos por día
        tp_multiplier=1.05,            # TP 5%
        max_holding_days=7,            # 7 días holding
        dd_threshold_1=0.05,           # 5% DD
        dd_threshold_2=0.08,           # 8% DD
        dd_threshold_3=0.10,           # 10% DD (kill switch)
        cooldown_days=10
    )
    
    # Período de backtest
    start_date = '2024-01-01'
    end_date = '2026-01-31'
    test_start_date = '2025-07-01'
    
    logger.info(f"Período total: {start_date} a {end_date}")
    logger.info(f"Período de test: {test_start_date} a {end_date}")
    
    # Ejecutar backtest
    logger.info("Iniciando backtest...")
    results = strategy.run_backtest(
        start_date=start_date,
        end_date=end_date,
        test_start_date=test_start_date
    )
    
    if 'error' in results:
        logger.error(f"Error en backtest: {results['error']}")
        return
    
    # Mostrar resultados
    metrics = results['metrics']
    
    print("\n" + "="*80)
    print("SWING MULTI-ASSET V2 - INTER-SECTOR ROTATION RESULTS")
    print("="*80)
    print(f"\nCapital Inicial: ${results['initial_capital']:.2f}")
    print(f"Capital Final:   ${results['final_equity']:.2f}")
    print(f"\nMÉTRICAS DE PERFORMANCE:")
    print(f"  Total Return:    {metrics['total_return']:.2f}%")
    print(f"  CAGR:            {metrics['cagr']:.2f}%")
    print(f"  Sharpe Ratio:    {metrics['sharpe_ratio']:.2f}")
    print(f"  Max Drawdown:    {metrics['max_drawdown']:.2f}%")
    print(f"\nMÉTRICAS DE TRADING:")
    print(f"  Número de Trades: {metrics['num_trades']}")
    print(f"  Win Rate:         {metrics['win_rate']:.2f}%")
    print(f"  Avg Winner:       {metrics['avg_winner']:.2f}%")
    print(f"  Avg Loser:        {metrics['avg_loser']:.2f}%")
    print(f"  Profit Factor:    {metrics['profit_factor']:.2f}")
    print(f"  Expectancy:       {metrics['expectancy']:.2f}%")
    print(f"  Exposure:         {metrics['exposure']:.2f}%")
    print("="*80)
    
    # Guardar resultados
    results_dir = project_root / 'results'
    results_dir.mkdir(exist_ok=True)
    
    # Guardar JSON
    results_file = results_dir / 'swing_multi_asset_v2_results.json'
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    logger.info(f"Resultados guardados en: {results_file}")
    
    # Guardar trades CSV
    trades_df = pd.DataFrame(results['trades'])
    trades_file = results_dir / 'swing_multi_asset_v2_trades.csv'
    trades_df.to_csv(trades_file, index=False)
    logger.info(f"Trades guardados en: {trades_file}")
    
    # Graficar equity curve
    plt.figure(figsize=(14, 7))
    
    dates = [datetime.strptime(d, '%Y-%m-%d') for d in results['dates']]
    equity_curve = results['equity_curve']
    
    plt.plot(dates, equity_curve, linewidth=2, label='Equity Curve')
    plt.axhline(y=results['initial_capital'], color='gray', linestyle='--', alpha=0.5, label='Initial Capital')
    
    # Marcar período de test
    test_start_dt = datetime.strptime(test_start_date, '%Y-%m-%d')
    plt.axvline(x=test_start_dt, color='red', linestyle='--', alpha=0.5, label='Test Period Start')
    
    plt.title('SwingMultiAssetV2 - Inter-Sector Rotation\nEquity Curve', fontsize=14, fontweight='bold')
    plt.xlabel('Date', fontsize=12)
    plt.ylabel('Equity ($)', fontsize=12)
    plt.legend(loc='best')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    chart_file = results_dir / 'equity_curve_multi_asset_v2.png'
    plt.savefig(chart_file, dpi=300, bbox_inches='tight')
    logger.info(f"Gráfico guardado en: {chart_file}")
    
    # Análisis por tipo de activo
    print("\n" + "="*80)
    print("ANÁLISIS POR TIPO DE ACTIVO")
    print("="*80)
    
    tech_stocks = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA', 'NFLX', 'AVGO', 'COST']
    tech_etfs = ['SMH', 'XLK', 'SOXX', 'IGV', 'HACK']
    sector_etfs = ['XLE', 'XLF', 'XLV', 'XLI', 'XLP', 'XLU']
    bonds = ['TLT']
    
    for category, symbols_list in [
        ('Tech Stocks', tech_stocks),
        ('Tech ETFs', tech_etfs),
        ('Sector ETFs', sector_etfs),
        ('Bonds', bonds)
    ]:
        category_trades = [t for t in results['trades'] if t['symbol'] in symbols_list]
        
        if not category_trades:
            print(f"\n{category}: No trades")
            continue
        
        winners = [t for t in category_trades if t['pnl_dollar'] > 0]
        win_rate = (len(winners) / len(category_trades)) * 100 if category_trades else 0
        avg_pnl = sum(t['pnl_percent'] for t in category_trades) / len(category_trades)
        
        print(f"\n{category}:")
        print(f"  Trades: {len(category_trades)}")
        print(f"  Win Rate: {win_rate:.1f}%")
        print(f"  Avg P&L: {avg_pnl:.2f}%")
    
    print("="*80)
    
    logger.info("Backtest completado exitosamente")


if __name__ == '__main__':
    main()
