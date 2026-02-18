"""
Script para verificar disponibilidad de datos históricos.

Verifica si tenemos suficientes datos para:
- EMA200 (necesita 200 días previos)
- Walk-forward validation 2022-2026
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

from auronai.data.market_data_provider import MarketDataProvider

def check_data_availability():
    """Verificar disponibilidad de datos históricos."""
    
    provider = MarketDataProvider()
    
    # Símbolos a verificar
    symbols = [
        # Tech stocks
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META',
        'NVDA', 'TSLA', 'NFLX', 'AVGO', 'COST',
        # Tech ETFs
        'SMH', 'XLK', 'SOXX', 'IGV', 'HACK',
        # Benchmark
        'QQQ'
    ]
    
    # Períodos a testear
    test_periods = [
        ('2022', '2022-01-01', '2022-12-31'),
        ('2023', '2023-01-01', '2023-12-31'),
        ('2024', '2024-01-01', '2024-12-31'),
        ('2025', '2025-01-01', '2025-12-31'),
    ]
    
    print("="*80)
    print("DATA AVAILABILITY CHECK")
    print("="*80)
    print(f"\nVerificando {len(symbols)} símbolos...")
    print(f"Necesitamos 200 días previos para EMA200\n")
    
    results = {}
    
    for symbol in symbols:
        print(f"Checking {symbol}...", end=" ")
        
        try:
            # Descargar máximo histórico disponible
            data = provider.get_historical_data(
                symbol,
                period='max',
                interval='1d'
            )
            
            if data is None or len(data) == 0:
                print(f"❌ NO DATA")
                results[symbol] = {'status': 'NO_DATA', 'first_date': None, 'last_date': None}
                continue
            
            first_date = data.index[0]
            last_date = data.index[-1]
            total_days = len(data)
            
            # Verificar si tenemos datos desde antes de 2022
            # Para 2022 necesitamos datos desde mid-2021 (200 días antes)
            required_start = datetime(2021, 6, 1)
            
            if first_date.tz is not None:
                first_date_naive = first_date.tz_localize(None)
            else:
                first_date_naive = first_date
            
            if first_date_naive <= required_start:
                status = "✅ OK"
            else:
                status = f"⚠️  STARTS {first_date_naive.strftime('%Y-%m-%d')}"
            
            print(f"{status} ({total_days} days, {first_date_naive.strftime('%Y-%m-%d')} to {last_date.strftime('%Y-%m-%d')})")
            
            results[symbol] = {
                'status': 'OK' if first_date_naive <= required_start else 'LIMITED',
                'first_date': first_date_naive,
                'last_date': last_date,
                'total_days': total_days
            }
            
        except Exception as e:
            print(f"❌ ERROR: {e}")
            results[symbol] = {'status': 'ERROR', 'error': str(e)}
    
    # Resumen
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    ok_count = sum(1 for r in results.values() if r.get('status') == 'OK')
    limited_count = sum(1 for r in results.values() if r.get('status') == 'LIMITED')
    error_count = sum(1 for r in results.values() if r.get('status') in ['NO_DATA', 'ERROR'])
    
    print(f"\n✅ OK: {ok_count}/{len(symbols)} símbolos")
    print(f"⚠️  LIMITED: {limited_count}/{len(symbols)} símbolos")
    print(f"❌ ERROR: {error_count}/{len(symbols)} símbolos")
    
    if limited_count > 0:
        print("\n⚠️  Símbolos con datos limitados:")
        for symbol, info in results.items():
            if info.get('status') == 'LIMITED':
                print(f"  - {symbol}: Inicia {info['first_date'].strftime('%Y-%m-%d')}")
    
    # Verificar períodos específicos
    print("\n" + "="*80)
    print("PERIOD COVERAGE")
    print("="*80)
    
    for period_name, start_date, end_date in test_periods:
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        # Necesitamos 200 días antes para EMA200
        required_start = start_dt - timedelta(days=250)  # 200 trading days ≈ 250 calendar days
        
        print(f"\n{period_name} ({start_date} to {end_date}):")
        print(f"  Required data from: {required_start.strftime('%Y-%m-%d')}")
        
        covered = 0
        for symbol, info in results.items():
            if info.get('status') in ['OK', 'LIMITED'] and info.get('first_date'):
                if info['first_date'] <= required_start:
                    covered += 1
        
        coverage_pct = (covered / len(symbols)) * 100
        status = "✅" if coverage_pct >= 90 else "⚠️" if coverage_pct >= 70 else "❌"
        print(f"  {status} Coverage: {covered}/{len(symbols)} ({coverage_pct:.1f}%)")
    
    # Recomendación
    print("\n" + "="*80)
    print("RECOMMENDATION")
    print("="*80)
    
    if ok_count >= len(symbols) * 0.9:
        print("\n✅ GOOD TO GO!")
        print("Tienes suficientes datos para walk-forward validation 2022-2025.")
        print("Puedes proceder con el backtest completo.")
    elif ok_count >= len(symbols) * 0.7:
        print("\n⚠️  MOSTLY OK")
        print("La mayoría de símbolos tienen datos suficientes.")
        print("Considera excluir símbolos con datos limitados o ajustar período de test.")
    else:
        print("\n❌ INSUFFICIENT DATA")
        print("Muchos símbolos no tienen datos suficientes para 2022.")
        print("Opciones:")
        print("  1. Empezar walk-forward desde 2023")
        print("  2. Usar solo símbolos con datos completos")
        print("  3. Reducir lookback de EMA200 a EMA100")
    
    return results


if __name__ == '__main__':
    check_data_availability()
